"""Aggiunge al piano i controlli dei raccolti gratuiti durante la semina.
Dopo ogni mossa su una cella che non e' A o C di nessun drone si inserisce
["check", [x,y], [posizioni]]: posizioni del rombo con un cespuglio che sara' sicuramente gia'
piantato (dallo stesso drone prima, o da un altro con MARGIN tick di anticipo sul tempo nominale).
uso: PLAN=plan_split3_16.json OUT=plan_chk.json MARGIN=1500 python3 addchecks.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "haysim"))
import dsim
from haysim import S, DIAMOND

SRC = os.path.join(HERE, os.environ.get("PLAN", "plan_split3_16.json"))
OUT = os.path.join(HERE, os.environ.get("OUT", "plan_chk.json"))
MARGIN = float(os.environ.get("MARGIN", "1500"))
OWNONLY = os.environ.get("OWNONLY", "0") == "1"
EARLY_T = 450.0
DIR = {"North": (0, 1), "South": (0, -1), "East": (1, 0), "West": (-1, 0)}

plan = json.load(open(SRC))
grass = set()
for p in plan:
    grass |= {tuple(p["A"]), tuple(p["C"])}
    if "B" in p:
        grass |= {tuple(p["B"]), tuple(p["D"])}   # erbe del riscaldamento a 4 celle (add4.py)


def timeline(acts, b, ptime):
    """tempi nominali di ogni azione e cespugli piantati; le azioni check costano il valore atteso"""
    t = dsim.spawn_ready(b) + 2
    pos = (0, 0); out = []
    for a in acts:
        out.append((t, pos))
        if a[0] == "move":
            d = DIR[a[1]]; pos = ((pos[0] + d[0]) % S, (pos[1] + d[1]) % S); t += 200
        elif a[0] == "plant":
            ptime[tuple(a[1])] = min(ptime.get(tuple(a[1]), 1e18), t); t += 200
        elif a[0] == "early":
            t += EARLY_T
        elif a[0] == "check":
            n = len(a[2]); t += 4 + (5 + 3 * n) / 3 + 200 * n / 72
    return out


def owner_ok(c, b, t, own, ptime):
    if c in own:
        return True
    if OWNONLY:
        return False
    return ptime.get(c, 1e18) + MARGIN <= t


acts0 = [p["actions"] for p in plan]
cur = acts0
for it in range(3):
    ptime = {}
    for b in range(32):
        timeline(cur, b, ptime) if False else None
    ptime = {}
    tls = [timeline(cur[b], b, ptime) for b in range(32)]
    new = []
    tot = 0.0; nchk = 0
    for b in range(32):
        own = set(); out = []
        tl = tls[b]
        pos = (0, 0)
        for k, a in enumerate(cur[b]):
            if a[0] == "check":
                continue
            out.append(a)
            t = tl[k][0]
            if a[0] == "plant":
                own.add(tuple(a[1]))
            if a[0] == "move":
                d = DIR[a[1]]; pos = ((pos[0] + d[0]) % S, (pos[1] + d[1]) % S)
                if pos in grass:
                    continue
                cand = []
                for dx, dy in DIAMOND:
                    c = ((pos[0] + dx) % S, (pos[1] + dy) % S)
                    if owner_ok(c, b, t + 200, own, ptime):
                        cand.append(list(c))
                if cand:
                    out.append(["check", list(pos), cand]); nchk += 1; tot += len(cand) / 72
        new.append(out)
    cur = new
    print("iterazione %d: controlli %d, raccolti attesi %.1f (%.2f per drone)" % (it, nchk, tot, tot / 32))
for p, a in zip(plan, cur):
    p["actions"] = a
json.dump(plan, open(OUT, "w"))
