# Simulatore + solver per lo strato di dinamite (Dynamite Sweeper).
# Regole ricavate da decompiled_nov6/Core/SweeperController.cs e da EN/docs/unlocks/dynamite.md:
#  - le mine sono scelte alla prima cella scavata; la cella di partenza e le 8 vicine non sono mine
#    (generazione con rifiuto: 100 tentativi per mina, come nel sorgente)
#  - numero di mine = round(W*H*ratio), ratio 0.10 a profondita' 20 .. 0.17 a 600
#  - measure() su una cella scavata (diventata soot) = mine tra le 8 vicine, nessun wrap ai bordi
#  - scavare una mina = esplosione dello strato (fallimento)
#  - scavare un dud = dynamite ceil(1*f); flood-fill se il conteggio e' 0 (le celle del flood non danno dynamite)
#  - vittoria quando tutti i dud sono scoperti; bonus ceil(n^2*f), n = mine ancora "scoperte" (vedi finish())
# Assunzione da verificare in gioco: le celle scoperte dal flood contano per la vittoria.
import math
import random
from collections import defaultdict

DIRS8 = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]


def neigh(c, W, H):
    x, y = c
    for dx, dy in DIRS8:
        nx, ny = x + dx, y + dy
        if 0 <= nx < W and 0 <= ny < H:
            yield (nx, ny)


class Board:
    def __init__(self, W, H, ratio, start, rng, f=1.0):
        self.W, self.H, self.f = W, H, f
        num = max(round(W * H * ratio), 1)
        mines = set()
        for _ in range(num):
            for _ in range(100):
                p = (rng.randrange(W), rng.randrange(H))
                if (abs(start[0] - p[0]) > 1 or abs(start[1] - p[1]) > 1) and p not in mines:
                    mines.add(p)
                    break
        self.mines = mines
        self.revealed = set()      # celle scavate (dud rimossi, soot visibile)
        self.yield_ = 0            # dynamite raccolta
        self.dig_count = 0
        self.status = None         # None / 'win' / 'fail'
        self.total_safe = W * H - len(mines)
        self.start = start

    def measure(self, c):
        assert c in self.revealed, "measure solo su celle scavate"
        return sum(1 for n in neigh(c, self.W, self.H) if n in self.mines)

    def dig(self, c):
        """Scava c. Ritorna le nuove celle rivelate (c + flood)."""
        assert self.status is None
        self.dig_count += 1
        if c in self.mines:
            self.status = 'fail'
            self.finish()
            return []
        if c in self.revealed:
            return []
        new = [c]
        self.revealed.add(c)
        self.yield_ += math.ceil(1 * self.f)
        if self.measure(c) == 0:
            queue = list(neigh(c, self.W, self.H))
            seen = {c}
            while queue:
                n = queue.pop()
                if n in seen:
                    continue
                seen.add(n)
                if n in self.mines or n in self.revealed:
                    continue
                self.revealed.add(n)
                new.append(n)
                if self.measure(n) == 0:
                    queue.extend(neigh(n, self.W, self.H))
        if len(self.revealed) >= self.total_safe:
            self.status = 'win'
            self.finish()
        return new

    def finish(self):
        if self.status == 'win':
            n = len(self.mines)  # a vittoria tutte le mine non hanno piu' vicini sicuri presenti
        else:
            n = sum(1 for m in self.mines
                    if any(q not in self.mines and q not in self.revealed for q in neigh(m, self.W, self.H)))
        self.yield_ += math.ceil(n * n * self.f)


class Solver:
    """Deduzione locale (R==0, R==|U|, coppie di sottoinsiemi) + ipotesi a probabilita' minima."""

    def __init__(self, board, ratio_est):
        self.b = board
        self.ratio = ratio_est
        self.safe = set()
        self.mine = set()
        self.counts = {}      # cella scoperta -> numero
        self.pos = board.start
        self.moves = 0
        self.guesses = 0

    def learn(self, cells):
        for c in cells:
            self.safe.add(c)
            if c in self.b.revealed:
                self.counts[c] = self.b.measure(c)

    def constraints(self):
        W, H = self.b.W, self.b.H
        cons = []
        for c, k in self.counts.items():
            U = frozenset(n for n in neigh(c, W, H) if n not in self.safe and n not in self.mine)
            R = k - sum(1 for n in neigh(c, W, H) if n in self.mine)
            if U:
                cons.append((U, R))
        return cons

    def deduce(self):
        changed = True
        while changed:
            changed = False
            cons = self.constraints()
            for U, R in cons:
                if R == 0:
                    if U - self.safe:
                        self.safe |= U
                        changed = True
                elif R == len(U):
                    if U - self.mine:
                        self.mine |= U
                        changed = True
            if changed:
                continue
            # coppie: U_A subset di U_B -> U_B \ U_A ha R_B - R_A mine
            index = defaultdict(list)
            for i, (U, R) in enumerate(cons):
                for c in U:
                    index[c].append(i)
            for i, (UA, RA) in enumerate(cons):
                cand = set()
                for c in UA:
                    cand.update(index[c])
                for j in cand:
                    if i == j:
                        continue
                    UB, RB = cons[j]
                    if not UA < UB and UA != UB:
                        continue
                    D = UB - UA
                    r = RB - RA
                    if not D:
                        continue
                    if r == 0 and D - self.safe:
                        self.safe |= D
                        changed = True
                    elif r == len(D) and D - self.mine:
                        self.mine |= D
                        changed = True
                if changed:
                    break
            if not changed:
                break

    def next_safe(self):
        todo = [c for c in self.safe if c not in self.b.revealed]
        if not todo:
            return None
        return min(todo, key=lambda c: abs(c[0] - self.pos[0]) + abs(c[1] - self.pos[1]))

    def guess(self):
        W, H = self.b.W, self.b.H
        best, bp = None, 2.0
        cons = self.constraints()
        est = defaultdict(lambda: 1.0)
        for U, R in cons:
            p = R / len(U)
            for c in U:
                est[c] = min(est[c], p)
        for x in range(W):
            for y in range(H):
                c = (x, y)
                if c in self.safe or c in self.mine or c in self.b.revealed:
                    continue
                p = est[c] if c in est else self.ratio
                if p < bp:
                    best, bp = c, p
        self.guesses += 1
        return best

    def run(self):
        b = self.b
        new = b.dig(b.start)
        self.learn(new)
        while b.status is None:
            self.deduce()
            c = self.next_safe()
            if c is None:
                c = self.guess()
                self.safe.add(c)  # l'ipotesi: la mossa e' un rischio accettato
            self.moves += abs(c[0] - self.pos[0]) + abs(c[1] - self.pos[1])
            self.pos = c
            new = b.dig(c)
            self.learn(new)
        return b.status


def simulate(W, H, ratio, seeds=200, f=1.0):
    wins = guesses = digs = moves = 0
    yields = []
    for s in range(seeds):
        rng = random.Random(s)
        start = (rng.randrange(W), rng.randrange(H))
        b = Board(W, H, ratio, start, rng, f)
        sv = Solver(b, ratio)
        st = sv.run()
        wins += st == 'win'
        guesses += sv.guesses
        digs += b.dig_count
        moves += sv.moves
        yields.append(b.yield_)
    n = seeds
    return {
        'win_rate': wins / n,
        'guesses_per_run': guesses / n,
        'digs_per_run': digs / n,
        'moves_per_run': moves / n,
        'avg_yield': sum(yields) / n,
    }


if __name__ == '__main__':
    for (W, H) in [(8, 8), (32, 32)]:
        for r in [0.10, 0.135, 0.17]:
            res = simulate(W, H, r, seeds=100)
            print(W, H, r, {k: round(v, 2) for k, v in res.items()})
