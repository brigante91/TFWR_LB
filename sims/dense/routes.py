import json, random, itertools
from layout import S, D, dist, analyse



def assign(pairs, cells):
    # ogni cespuglio al drone la cui coppia e' piu' vicina (bilanciando i pareggi)
    own = {i: [] for i in range(len(pairs))}
    for c in sorted(cells):
        ds = [(min(dist(c, g) for g in pr), len(own[i]), i) for i, pr in enumerate(pairs)]
        own[min(ds)[2]].append(c)
    return own


def route(start, cells, end_choices):
    """percorso start -> tutte le celle -> una delle celle finali; nearest neighbour + 2-opt"""
    best = None
    for end in end_choices:
        rest = list(cells); path = [start]; cur = start
        while rest:
            nxt = min(rest, key=lambda c: (dist(cur, c), dist(c, end)))
            rest.remove(nxt); path.append(nxt); cur = nxt
        path.append(end)
        improved = True
        while improved:
            improved = False
            for i in range(1, len(path) - 2):
                for j in range(i + 1, len(path) - 1):
                    a, b, c, d = path[i - 1], path[i], path[j], path[j + 1]
                    if dist(a, c) + dist(b, d) < dist(a, b) + dist(c, d):
                        path[i:j + 1] = reversed(path[i:j + 1]); improved = True
        L = sum(dist(path[k], path[k + 1]) for k in range(len(path) - 1))
        if best is None or L < best[0]:
            best = (L, path, end)
    return best


if __name__ == "__main__":
    pairs = [tuple(map(tuple, p)) for p in json.load(open(__import__("os").environ.get("PAIRS","pairs.json")))["pairs"]]
    grass, union, bad = analyse(pairs)
    own = assign(pairs, union)
    tot_moves = tot_plants = 0
    plan = []
    for i, pr in enumerate(pairs):
        L, path, end = route((0, 0), own[i], list(pr))
        other = pr[1] if end == pr[0] else pr[0]
        plan.append({"pair": pr, "A": end, "C": other, "path": path, "moves": L, "plants": len(own[i])})
        tot_moves += L; tot_plants += len(own[i])
    print("mosse medie per drone %.1f, piantate medie %.1f, azioni medie %.1f" % (tot_moves / 32, tot_plants / 32, (tot_moves + tot_plants) / 32))
    print("min/max azioni:", min(p["moves"] + p["plants"] for p in plan), max(p["moves"] + p["plants"] for p in plan))
    json.dump(plan, open(__import__("os").environ.get("PLAN","plan.json"), "w"))
