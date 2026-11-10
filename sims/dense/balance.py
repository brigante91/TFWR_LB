import json, sys
from layout import dist
src = sys.argv[1]; dst = sys.argv[2]; CAP = int(sys.argv[3])
plan = json.load(open(src))
for p in plan:
    p["path"] = [tuple(c) for c in p["path"]]

def plen(path): return sum(dist(path[k], path[k + 1]) for k in range(len(path) - 1))
def acts(p): return plen(p["path"]) + len(p["path"]) - 2
def pen(a): return max(0, a - CAP) ** 2 * 0.5
def two_opt(path):
    improved = True
    while improved:
        improved = False
        for i in range(1, len(path) - 2):
            for j in range(i + 1, len(path) - 1):
                a, b, c, d = path[i - 1], path[i], path[j], path[j + 1]
                if dist(a, c) + dist(b, d) < dist(a, b) + dist(c, d):
                    path[i:j + 1] = reversed(path[i:j + 1]); improved = True
def ins(path, c):
    best = None
    for k in range(len(path) - 1):
        add = dist(path[k], c) + dist(c, path[k + 1]) - dist(path[k], path[k + 1])
        if best is None or add < best[0]: best = (add, k + 1)
    return best

for it in range(60):
    moved = 0
    A = [acts(p) for p in plan]
    for i, p in enumerate(plan):
        for c in list(p["path"][1:-1]):
            k = p["path"].index(c)
            gain = dist(p["path"][k - 1], c) + dist(c, p["path"][k + 1]) - dist(p["path"][k - 1], p["path"][k + 1]) + 1
            ai = A[i]
            best = None
            for j, q in enumerate(plan):
                if j == i: continue
                add, pos = ins(q["path"], c); add += 1
                delta = (add - gain) + pen(A[j] + add) - pen(A[j]) + pen(ai - gain) - pen(ai)
                if delta < -1e-9 and (best is None or delta < best[0]): best = (delta, j, pos, add)
            if best:
                _, j, pos, add = best
                p["path"].pop(k); plan[j]["path"].insert(pos, c)
                A[i] -= gain; A[j] += add; moved += 1
    for p in plan: two_opt(p["path"])
    if not moved: break
for p in plan:
    p["moves"] = plen(p["path"]); p["plants"] = len(p["path"]) - 2
    p["path"] = [list(c) for c in p["path"]]
a = [p["moves"] + p["plants"] for p in plan]
print("cap", CAP, "azioni medie %.1f, min/max %d/%d" % (sum(a) / 32, min(a), max(a)))
json.dump(plan, open(dst, "w"))
