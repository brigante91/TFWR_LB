"""Ricerca locale sulla scelta delle 32 coppie: minimizza cespugli + peso * viaggio dall'origine.
Reticoli densi (det 12) in tutte le orientazioni, coppie orizzontali e verticali."""
import json, random
from layout import S, D, dist

def lattice_points(u, v, off, vertical):
    pts = []
    for a in range(-10, 11):
        for b in range(-16, 17):
            x = a * u[0] + b * v[0] + off[0]; y = a * u[1] + b * v[1] + off[1]
            if -16 <= x <= 15 and -16 <= y <= 15:
                c1 = (x % S, y % S)
                c2 = (c1[0], (c1[1] + 1) % S) if vertical else ((c1[0] + 1) % S, c1[1])
                pts.append((c1, c2))
    return list(dict.fromkeys(pts))

def cost(sel, W_TRAVEL):
    grass = set(c for p in sel for c in p)
    if len(grass) != 64: return None
    union = set()
    for g in grass:
        for dx, dy in D:
            c = ((g[0] + dx) % S, (g[1] + dy) % S)
            if c in grass:
                # solo la compagna puo' stare nel rombo
                pass
            else:
                union.add(c)
    # controllo: ogni erba vede solo la compagna
    for p in sel:
        for g in p:
            o = p[1] if g == p[0] else p[0]
            for dx, dy in D:
                c = ((g[0] + dx) % S, (g[1] + dy) % S)
                if c in grass and c != o: return None
    trav = sum(min(dist((0, 0), g) for g in p) for p in sel)
    return len(union) + W_TRAVEL * trav, len(union), trav

if __name__ == "__main__":
    random.seed(1)
    best_all = None
    W_TRAVEL = 0.5
    for vertical in (False, True):
        bases = [((6, 0), (3, 2)), ((6, 0), (3, -2))] if not vertical else [((0, 6), (2, 3)), ((0, 6), (-2, 3))]
        for u, v in bases:
            for ox in range(0, 6):
                for oy in range(0, 2 if not vertical else 6):
                    pts = lattice_points(u, v, (ox, oy), vertical)
                    pts.sort(key=lambda p: min(dist((0, 0), g) for g in p))
                    sel = pts[:32]
                    c = cost(sel, W_TRAVEL)
                    if c is None: continue
                    cur = c
                    pool = pts[:80]
                    for it in range(4000):
                        i = random.randrange(32); cand = random.choice(pool)
                        if cand in sel: continue
                        new = sel[:i] + [cand] + sel[i + 1:]
                        nc = cost(new, W_TRAVEL)
                        if nc and nc[0] <= cur[0]:
                            sel, cur = new, nc
                    if best_all is None or cur[0] < best_all[0][0]:
                        best_all = (cur, sel, vertical, u, v, (ox, oy))
    (cst, bush, trav), sel, vertical, u, v, off = best_all
    print("migliore: cespugli", bush, "viaggio totale", trav, "verticale" if vertical else "orizzontale", u, v, off, "(attuale: 436 cespugli, viaggio 323)")
    json.dump({"pairs": sel}, open("pairs_opt.json", "w"))
