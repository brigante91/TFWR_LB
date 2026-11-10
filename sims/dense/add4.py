"""Piano per il riscaldamento a 4 erbe (dsim4 Q4): per ogni drone sceglie il lato (Nord o Sud)
del quadrato 2x2 A, C, B = C + lato, D = A + lato; B e D restano erba (non vengono piantati nei
percorsi) e il drone li trasforma in cespugli a fine riscaldamento.
uso: PLAN=plan_split3_16.json OUT=plan_q4.json SIDE=auto|N|S python3 add4.py"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
S = 32
SRC = os.path.join(HERE, os.environ.get("PLAN", "plan_split3_16.json"))
OUT = os.path.join(HERE, os.environ.get("OUT", "plan_q4.json"))
SIDE = os.environ.get("SIDE", "auto")
D3 = [(dx, dy) for dx in range(-3, 4) for dy in range(-3, 4) if (dx or dy) and abs(dx) + abs(dy) <= 3]
plan = json.load(open(SRC))
grass = set()
for p in plan:
    grass |= {tuple(p["A"]), tuple(p["C"])}
owner = {}
for i, p in enumerate(plan):
    for a in p["actions"]:
        if a[0] == "plant":
            owner[tuple(a[1])] = i


def others_hit(c, i):
    # quante erbe di altri droni hanno c nel rombo (perdono un cespuglio durante il riscaldamento)
    return sum(1 for g in grass if g not in (tuple(plan[i]["A"]), tuple(plan[i]["C"]))
               and ((c[0] - g[0]) % S, (c[1] - g[1]) % S) in {(dx % S, dy % S) for dx, dy in D3})


taken = set()
for i, p in enumerate(plan):
    A = tuple(p["A"]); C = tuple(p["C"])
    best = None
    for side, dy in (("North", 1), ("South", -1)):
        if SIDE != "auto" and side[0] != SIDE:
            continue
        B = (C[0], (C[1] + dy) % S); Dc = (A[0], (A[1] + dy) % S)
        if B in grass or Dc in grass or B in taken or Dc in taken or B not in owner or Dc not in owner:
            continue
        cost = others_hit(B, i) + others_hit(Dc, i)
        if best is None or cost < best[0]:
            best = (cost, side, B, Dc)
    assert best, i
    _, side, B, Dc = best
    taken |= {B, Dc}
    p["B"] = list(B); p["D"] = list(Dc); p["side"] = side
for p in plan:
    p["actions"] = [a for a in p["actions"] if not (a[0] == "plant" and tuple(a[1]) in taken)]
    p["nacts"] = sum(1 for a in p["actions"] if a[0] != "early")
json.dump(plan, open(OUT, "w"))
print("piano Q4 scritto:", OUT, "lati", sum(1 for p in plan if p["side"] == "North"), "N /", sum(1 for p in plan if p["side"] == "South"), "S")
