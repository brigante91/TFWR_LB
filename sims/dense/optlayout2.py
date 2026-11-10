"""Ricerca locale sulla scelta delle 32 coppie con l'obiettivo vero: somma delle azioni dei percorsi
(mosse + piantate), percorsi calcolati con assegnazione al drone piu' vicino + NN + 2-opt (routes.py).
uso: python3 optlayout2.py [iterazioni] [seed]  -> pairs_opt2.json + plan_opt2.json"""
import json, random, sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layout import S, D, dist, analyse
from routes import assign, route
from improve import two_opt, best_insert, plen
from optlayout import lattice_points


def improve_plan(plan, rounds=8):
    """sposta cespugli tra droni quando accorcia i percorsi (improve.py), poi 2-opt."""
    for it in range(rounds):
        moved = 0
        for i, p in enumerate(plan):
            for c in list(p["path"][1:-1]):
                k = p["path"].index(c)
                gain = dist(p["path"][k - 1], c) + dist(c, p["path"][k + 1]) - dist(p["path"][k - 1], p["path"][k + 1])
                cand = None
                for j, q in enumerate(plan):
                    if j == i:
                        continue
                    add, pos = best_insert(q["path"], c)
                    if add < gain and (cand is None or add < cand[0]):
                        cand = (add, j, pos)
                if cand:
                    add, j, pos = cand
                    p["path"].pop(k); plan[j]["path"].insert(pos, c); moved += 1
        for p in plan:
            two_opt(p["path"])
        if not moved:
            break
    for p in plan:
        p["moves"] = plen(p["path"]); p["plants"] = len(p["path"]) - 2
    return plan

ITER = int(sys.argv[1]) if len(sys.argv) > 1 else 300
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 1
WMAX = float(os.environ.get("WMAX", "0.0"))   # peso sul massimo (bilanciamento)


def valid(sel):
    grass = set(c for p in sel for c in p)
    if len(grass) != 64:
        return False
    for p in sel:
        for g in p:
            o = p[1] if g == p[0] else p[0]
            for dx, dy in D:
                c = ((g[0] + dx) % S, (g[1] + dy) % S)
                if c in grass and c != o:
                    return False
    return True


def evaluate(sel):
    grass, union, bad = analyse(sel)
    own = assign(sel, union)
    plan = []
    tot = 0
    for i, pr in enumerate(sel):
        L, path, end = route((0, 0), own[i], list(pr))
        other = pr[1] if end == pr[0] else pr[0]
        plan.append({"pair": pr, "A": end, "C": other, "path": path, "moves": L, "plants": len(own[i])})
    plan = improve_plan(plan)
    tot = sum(p["moves"] + p["plants"] for p in plan)
    mx = max(p["moves"] + p["plants"] for p in plan)
    return tot + WMAX * mx, tot, len(union), plan


random.seed(SEED)
start = [tuple(map(tuple, p)) for p in json.load(open("pairs_opt.json"))["pairs"]]
cur_c, cur_tot, cur_b, cur_plan = evaluate(start)
print("partenza: azioni totali %d (media %.2f), cespugli %d" % (cur_tot, cur_tot / 32, cur_b), flush=True)
sel = list(start)
# candidati: punti dei reticoli densi (orizzontali) vicini all'origine
pool = list(dict.fromkeys(lattice_points((6, 0), (3, 2), (2, 0), False)))
pool.sort(key=lambda p: min(dist((0, 0), g) for g in p))
pool = pool[:120]
t0 = time.time()
for it in range(ITER):
    i = random.randrange(32)
    cand = random.choice(pool)
    if cand in sel:
        continue
    new = sel[:i] + [cand] + sel[i + 1:]
    if not valid(new):
        continue
    c, tot, b, plan = evaluate(new)
    if c <= cur_c:
        if c < cur_c:
            print("it %d: azioni %d (media %.2f) cespugli %d  [%.0fs]" % (it, tot, tot / 32, b, time.time() - t0), flush=True)
        sel, cur_c, cur_tot, cur_b, cur_plan = new, c, tot, b, plan
print("finale: azioni %d (media %.2f) cespugli %d" % (cur_tot, cur_tot / 32, cur_b))
json.dump({"pairs": sel}, open("pairs_opt2.json", "w"))
json.dump(cur_plan, open("plan_opt2.json", "w"))
