"""Confronta varianti di lb_maze_v2.py con mazesim su piu' semi (processi paralleli).

Uso: python3 maze_batch.py [--seeds N] [--trace] [--jobs J] "IDLE=1 RACE=4" "IDLE=2 RACE=0" ...
Ogni argomento e' una lista di NOME=VALORE sostituiti nelle costanti dello script;
"" = script invariato.
"""
import sys, os, argparse, subprocess, json
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))


def one(args):
    cfg, seed, trace, script = args
    cmd = [sys.executable, os.path.join(HERE, "mazesim.py"), "--script", script, "--seed", str(seed), "--quiet"]
    if not trace:
        cmd.append("--no-trace")
    for kv in cfg.split():
        cmd += ["--set", kv]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    t = None
    win = ""
    logic = ""
    for line in out.splitlines():
        if line.startswith("tempo simulato"):
            t = float(line.split()[2])
        if "finestra" in line:
            win = line.split(": ", 1)[1]
        if "logica" in line:
            logic = line.split("logica")[1].strip()
    return cfg, seed, t, win, logic, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=4)
    ap.add_argument("--seed0", type=int, default=1)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    ap.add_argument("--script", default=os.path.join(HERE, "..", "lb_maze_v2.py"))
    ap.add_argument("cfgs", nargs="*", default=[""])
    a = ap.parse_args()
    jobs = [(c, a.seed0 + s, a.trace, os.path.abspath(a.script)) for c in a.cfgs for s in range(a.seeds)]
    res = {}
    with ProcessPoolExecutor(a.jobs) as ex:
        for cfg, seed, t, win, logic, out in ex.map(one, jobs):
            if t is None:
                print("ERRORE", cfg, seed, out[-2000:])
                continue
            res.setdefault(cfg, []).append((seed, t, win, logic))
    for cfg in a.cfgs:
        r = res.get(cfg, [])
        if not r:
            continue
        ts = [x[1] for x in r]
        print("%-40s media %7.2f s  min %7.2f  max %7.2f  (%d semi)  logica %s" % (
            cfg or "(base)", sum(ts) / len(ts), min(ts), max(ts), len(ts), r[0][3]))
        for seed, t, win, logic in r:
            print("    seme %d: %7.2f s   %s" % (seed, t, win))


if __name__ == "__main__":
    main()
