"""Recover the game's per-session seed generator from seedless simulations.

Every simulation started without a seed (simulate(..., -1, ...) or leaderboard_run)
takes its master seed from one process-wide System.Random on Unity's main thread.
Observing a few consecutive master seeds reveals that generator, and with it the
master seed of the next seedless simulation.

usage: python3 session.py FP_OUTPUT.txt [--range LO HI]
  FP_OUTPUT.txt: game output containing one "fp HI LO" line per fingerprint run, in order.
"""
import re
import subprocess
import sys
import os

from tfwr_rng import DotNetRandom, SimulationRng, MBIG

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_INDEX = 120       # how far into the session generator to look for the first observation
LOOKAHEAD = 400


def outputs(seed, n):
    r = DotNetRandom(seed)
    return [r.sample() for _ in range(n)]


_B = outputs(0, MAX_INDEX)
_A = [(x - b) % MBIG for x, b in zip(outputs(1, MAX_INDEX), _B)]


def seeds_with_output(j, value):
    """All seeds s whose j-th sample (0-based) equals value.

    Samples are linear in the seed modulo 2^31-1 up to a small even error
    (int32 wrap-around during seeding), so try the handful of corrections.
    """
    inv = pow(_A[j], -1, MBIG)
    found = set()
    for e in range(-400, 401, 2):
        s = ((value - _B[j] - e) * inv) % MBIG
        for cand in (s, MBIG - s):
            if cand not in found and outputs(cand, j + 1)[j] == value:
                found.add(cand)
    return found


def fingerprint(master):
    """(HI, LO) printed by fingerprint.py for a simulation with this master seed."""
    raw = SimulationRng(master).new_drone().sample()
    return raw // 65536, raw % 65536


def master_candidates(raw, search_range=None):
    """Master seeds whose main drone's first random() has this raw value."""
    targets = set()
    for d in seeds_with_output(0, raw):          # the drone's own generator seed
        targets |= seeds_with_output(0, d)       # seed of Simulation.randomRandom
    cmd = [os.path.join(HERE, "seedfind"), "7"] + [str(t) for t in sorted(targets)]
    if search_range:
        cmd += ["--range", str(search_range[0]), str(search_range[1])]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    cands = [int(line.split()[0]) for line in out.splitlines()]
    return [m for m in cands if fingerprint(m) == (raw // 65536, raw % 65536)]


def find_session(cand_lists):
    """Session seed g and the index of each observation in Random(g)'s output."""
    hits = []
    for m0 in cand_lists[0]:
        for j in range(MAX_INDEX):
            for g in seeds_with_output(j, m0):
                seq = outputs(g, j + LOOKAHEAD)
                idx, pos, ok = [j], j, True
                for cands in cand_lists[1:]:
                    nxt = [k for k in range(pos + 1, len(seq)) if seq[k] in cands]
                    if not nxt:
                        ok = False
                        break
                    pos = nxt[0]
                    idx.append(pos)
                if ok:
                    hits.append((g, idx))
    return hits


def main():
    args = sys.argv[1:]
    search_range = None
    if "--range" in args:
        i = args.index("--range")
        search_range = (int(args[i + 1]), int(args[i + 2]))
        del args[i:i + 3]
    if len(args) != 1:
        sys.exit(__doc__)
    text = open(args[0], encoding="utf-8", errors="replace").read()
    raws = [int(h) * 65536 + int(l) for h, l in re.findall(r"fp\D+(\d+)\D+(\d+)", text)]
    if not raws:
        sys.exit("no 'fp HI LO' lines found")
    cand_lists = []
    for n, raw in enumerate(raws, 1):
        print(f"observation {n}: raw={raw}, searching master seed...", flush=True)
        cands = master_candidates(raw, search_range)
        print(f"  candidates: {cands}")
        if not cands:
            sys.exit("  no master seed reproduces this fingerprint: the model is wrong somewhere")
        cand_lists.append(cands)
    if len(cand_lists) < 2:
        print("one observation only: run at least two consecutive fingerprints to identify the session")
        return
    hits = find_session(cand_lists)
    if not hits:
        print(f"\nNO session generator explains these seeds within the first {MAX_INDEX} outputs.")
        print("Either the seeds are not drawn from one generator, or something else consumes it heavily.")
        return
    for g, idx in hits:
        gaps = [b - a for a, b in zip(idx, idx[1:])]
        print(f"\nSESSION FOUND: generator seed {g}, observations at output indices {idx} (gaps {gaps})")
        seq = outputs(g, idx[-1] + 9)
        print("next seedless simulations, in order (master seed -> expected 'fp HI LO'):")
        for k in range(idx[-1] + 1, idx[-1] + 9):
            hi, lo = fingerprint(seq[k])
            print(f"  +{k - idx[-1]}: master {seq[k]:>10} -> fp {hi} {lo}")


if __name__ == "__main__":
    main()
