# Predittore della posizione della mappa: x_k = floor(4*frac(u0 + k*b)) + 2 (System.Random con semi consecutivi)
import sys, random
sys.path.insert(0, '../..'); sys.path.insert(0, '.')
from tfwr_rng import DotNetRandom, MBIG
CX = 4 * 458365203 / MBIG
CY = 4 * 969558243 / MBIG

def chunk(s):
    r = DotNetRandom(s); [r.next(0, 1), r.next(0, 1), r.next(0, 6)]
    return r.next(2, 6), r.next(2, 6)

class Track:
    def __init__(self, c): self.c = c; self.lo = None
    def obs(self, k, v):
        a = (v - 2) - k * self.c
        if self.lo is None:
            a %= 4; self.lo, self.hi = a, a + 1; return
        a -= 4 * round((a - self.lo) / 4)
        self.lo = max(self.lo, a); self.hi = min(self.hi, a + 1)
    def pred(self, k):
        if self.lo is None: return None, False
        m = (self.lo + self.hi) / 2 + k * self.c
        a = int(((self.lo + k * self.c) % 4)); b = int(((self.hi - 1e-9 + k * self.c) % 4))
        return int(m % 4) + 2, a == b

if __name__ == "__main__":
    R = random.Random(3); ok = [0]*12; cert = [0]*12; N = 3000
    for _ in range(N):
        s = R.randrange(1 << 30)
        tx, ty = Track(CX), Track(CY)
        for k in range(12):
            x, y = chunk(s + k)
            px, cx = tx.pred(k); py, cy = ty.pred(k)
            if px is not None:
                ok[k] += (px == x and py == y); cert[k] += (cx and cy)
            tx.obs(k, x); ty.obs(k, y)
    print("k, P(giusta), P(certa)")
    for k in range(1, 12): print(k, round(ok[k]/N, 3), round(cert[k]/N, 3))
