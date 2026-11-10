"""Percorso con visita anticipata ottimizzato: i nodi sono origine, cespugli, il blocco [A,C] (o [C,A])
che deve restare contiguo, e la fine su A. 2-opt con vincolo di contiguita' + or-opt del blocco.
Costo = mosse + piantate + penalita' se le azioni dopo la visita sono < MINPOST (ricrescita a secco).
uso: PLAN=plan_opt.json OUT=plan_split2.json MINPOST=15 python3 split2.py"""
import json, os, sys, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layout import S, dist
from split import actions_for, nacts, steps

SRC = os.environ.get("PLAN", os.path.join(os.path.dirname(os.path.abspath(__file__)), "plan_opt.json"))
OUT = os.environ.get("OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "plan_split2.json"))
MINPOST = int(os.environ.get("MINPOST", "15"))
PEN = float(os.environ.get("PEN", "0.5"))     # mosse-equivalenti per azione mancante dopo la visita


def plen(seq):
    return sum(dist(seq[k], seq[k + 1]) for k in range(len(seq) - 1))


def build(seq, A, C):
    """seq: lista di nodi (tuple) con 'E1','E2' per i due nodi del blocco; restituisce la lista azioni."""
    acts = []
    cur = seq[0]
    for k in range(1, len(seq)):
        node = seq[k]
        if node in ("E1", "E2"):
            tgt = A if node == "E1" else C
            for d in steps(cur, tgt):
                acts.append(["move", d])
            acts.append(["early", "A" if tgt == A else "C"])
            cur = tgt
        else:
            for d in steps(cur, node):
                acts.append(["move", d])
            cur = node
            if k < len(seq) - 1:
                acts.append(["plant", list(node)])
    return acts


def coords(seq, A, C):
    return [A if n == "E1" else C if n == "E2" else n for n in seq]


def post_actions(acts):
    j = max(k for k, a in enumerate(acts) if a[0] == "early")
    return nacts(acts[j + 1:])


def cost(seq, A, C):
    acts = build(seq, A, C)
    n = nacts(acts)
    post = post_actions(acts)
    return n + PEN * max(0, MINPOST - post), n, post, acts


def optimize(path, A, C):
    bushes = path[1:-1]
    best = None
    # inserimento del blocco in ogni posizione, nelle due orientazioni, poi 2-opt vincolato
    for i in range(0, len(bushes) + 1):
        for blk in (["E1", "E2"], ["E2", "E1"]):
            seq = [path[0]] + bushes[:i] + blk + bushes[i:] + [A]
            seq = two_opt(seq, A, C)
            seq = or_opt(seq, A, C)
            seq = two_opt(seq, A, C)
            c = cost(seq, A, C)
            if best is None or c[0] < best[0][0]:
                best = (c, seq)
    return best


def or_opt(seq, A, C):
    """sposta un nodo (o il blocco E1,E2 intero) in un'altra posizione se riduce il costo."""
    seq = list(seq)
    improved = True
    while improved:
        improved = False
        cur = cost(seq, A, C)[0]
        n = len(seq)
        # elementi spostabili: singoli cespugli, oppure il blocco come unita'
        units = []
        k = 1
        while k < n - 1:
            if seq[k] in ("E1", "E2"):
                units.append((k, 2)); k += 2
            else:
                units.append((k, 1)); k += 1
        for k, ln in units:
            unit = seq[k:k + ln]
            rest = seq[:k] + seq[k + ln:]
            for pos in range(1, len(rest)):
                if pos == k:
                    continue
                for u in ((unit, unit[::-1]) if ln == 2 else (unit,)):
                    new = rest[:pos] + list(u) + rest[pos:]
                    c = cost(new, A, C)[0]
                    if c < cur - 1e-9:
                        seq, cur, improved = new, c, True
                        break
                if improved:
                    break
            if improved:
                break
    return seq


def two_opt(seq, A, C):
    seq = list(seq)
    improved = True
    while improved:
        improved = False
        cur = cost(seq, A, C)[0]
        for i in range(1, len(seq) - 2):
            for j in range(i + 1, len(seq) - 1):
                # il blocco E1,E2 deve restare contiguo: non spezzare tra i-1,i o j,j+1 se sono i due E
                if {seq[i - 1], seq[i]} == {"E1", "E2"} or {seq[j], seq[j + 1]} == {"E1", "E2"}:
                    continue
                new = seq[:i] + seq[i:j + 1][::-1] + seq[j + 1:]
                c = cost(new, A, C)[0]
                if c < cur - 1e-9:
                    seq, cur, improved = new, c, True
    return seq


plan = json.load(open(SRC))
out = []
tot = totb = 0
for di, p in enumerate(plan):
    path = [tuple(c) for c in p["path"]]
    A = tuple(p["A"]); C = tuple(p["C"])
    nb = nacts(actions_for(path, A, C, None)); totb += nb
    (c, n, post, acts), seq = optimize(path, A, C)
    tot += n
    out.append({"pair": p["pair"], "A": list(A), "C": list(C), "actions": acts, "post": post, "extra": n - nb, "nacts": n})
    print("drone %2d: azioni %2d (+%d) post %2d" % (di, n, n - nb, post))
print("azioni medie %.2f (prima %.2f)" % (tot / 32, totb / 32))
json.dump(out, open(OUT, "w"))
