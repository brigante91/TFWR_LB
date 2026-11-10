import json
from layout import dist

def plen(path):
    return sum(dist(path[k], path[k + 1]) for k in range(len(path) - 1))

def two_opt(path):
    improved = True
    while improved:
        improved = False
        for i in range(1, len(path) - 2):
            for j in range(i + 1, len(path) - 1):
                a, b, c, d = path[i - 1], path[i], path[j], path[j + 1]
                if dist(a, c) + dist(b, d) < dist(a, b) + dist(c, d):
                    path[i:j + 1] = reversed(path[i:j + 1]); improved = True
    return path

def best_insert(path, c):
    best = None
    for k in range(len(path) - 1):
        add = dist(path[k], c) + dist(c, path[k + 1]) - dist(path[k], path[k + 1])
        if best is None or add < best[0]:
            best = (add, k + 1)
    return best

if __name__ == "__main__":
    plan = json.load(open(__import__("os").environ.get("PLAN","plan.json")))
    for p in plan:
        p["path"] = [tuple(c) for c in p["path"]]
    before = sum(plen(p["path"]) for p in plan)
    for it in range(30):
        moved = 0
        for i, p in enumerate(plan):
            for c in list(p["path"][1:-1]):
                k = p["path"].index(c)
                gain = dist(p["path"][k - 1], c) + dist(c, p["path"][k + 1]) - dist(p["path"][k - 1], p["path"][k + 1])
                cand = None
                for j, q in enumerate(plan):
                    if j == i: continue
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
    after = sum(plen(p["path"]) for p in plan)
    for p in plan:
        p["moves"] = plen(p["path"]); p["plants"] = len(p["path"]) - 2
    print("mosse totali %d -> %d; azioni medie per drone %.1f; min/max %d/%d" % (before, after, sum(p["moves"] + p["plants"] for p in plan) / 32, min(p["moves"] + p["plants"] for p in plan), max(p["moves"] + p["plants"] for p in plan)))
    json.dump(plan, open(__import__("os").environ.get("PLAN","plan.json"), "w"))
