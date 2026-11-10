"""Piano con visita anticipata: il drone passa su A e C a meta' percorso (primo harvest + reroll,
l'erba ricresce a secco mentre pianta il resto) e finisce su A.
Scrive un piano con la lista esplicita delle azioni: ["move", dir] | ["plant", [x,y]] |
["early", "A"|"C"]; posizione iniziale (0,0).  uso: PLAN=plan_opt.json OUT=plan_split.json MINPOST=15"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layout import S, dist

SRC = os.environ.get("PLAN", os.path.join(os.path.dirname(os.path.abspath(__file__)), "plan_opt.json"))
OUT = os.environ.get("OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "plan_split.json"))
MINPOST = int(os.environ.get("MINPOST", "15"))
MODE = os.environ.get("MODE", "split")   # split | none (piano originale in formato azioni)


def steps(a, b):
    out = []
    dx = (b[0] - a[0]) % S
    out += ["East"] * dx if dx <= S // 2 else ["West"] * (S - dx)
    dy = (b[1] - a[1]) % S
    out += ["North"] * dy if dy <= S // 2 else ["South"] * (S - dy)
    return out


def actions_for(path, A, C, i):
    """path: [origine, cespugli..., A]; visita anticipata dopo path[i] (i=None: nessuna)."""
    acts = []
    cur = path[0]
    for k in range(1, len(path)):
        if i is not None and k == i + 1:
            for d in steps(cur, A):
                acts.append(["move", d])
            acts.append(["early", "A"])
            for d in steps(A, C):
                acts.append(["move", d])
            acts.append(["early", "C"])
            cur = C
        for d in steps(cur, path[k]):
            acts.append(["move", d])
        cur = path[k]
        if k < len(path) - 1:
            acts.append(["plant", list(path[k])])
    return acts


def nacts(acts):
    return sum(1 for a in acts if a[0] != "early")


plan = json.load(open(SRC))
out = []
tot = 0; totb = 0; nosplit = 0
for p in plan:
    path = [tuple(c) for c in p["path"]]
    A = tuple(p["A"]); C = tuple(p["C"])
    base = actions_for(path, A, C, None)
    nb = nacts(base); totb += nb
    best = None
    if MODE == "split":
        for i in range(0, len(path) - 1):
            acts = actions_for(path, A, C, i)
            n = nacts(acts)
            # azioni dopo la visita di C
            j = max(k for k, a in enumerate(acts) if a[0] == "early")
            post = nacts(acts[j + 1:])
            extra = n - nb
            # costo: mosse extra + attesa residua stimata (ricrescita a secco 3037 tick = 15.2 azioni)
            cost = extra * 200 + max(0.0, 3037.5 - 200 * post) * 0.69 * 2 + (0 if post >= MINPOST else 400)
            if best is None or cost < best[0]:
                best = (cost, i, acts, post, extra)
    if best is None:
        acts = base; post = 0; extra = 0; nosplit += 1
    else:
        _, i, acts, post, extra = best
    tot += nacts(acts)
    out.append({"pair": p["pair"], "A": list(A), "C": list(C), "actions": acts, "post": post, "extra": extra, "nacts": nacts(acts)})
    print("drone %2d: azioni %2d (+%d) post %2d" % (len(out) - 1, nacts(acts), extra, post))
print("azioni medie %.2f (prima %.2f)" % (tot / 32, totb / 32))
json.dump(out, open(OUT, "w"))
