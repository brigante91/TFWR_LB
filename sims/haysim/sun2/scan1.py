import sys, os, statistics as S
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import sunprog
from base_stats import V10
def ev(P, n=12):
    ts = []
    for s in range(n):
        Q = dict(V10); Q.update(P); Q['RANDGOAL'] = True
        r = sunprog.sim7(Q, s)
        ts.append(r['t'] if r['ok'] else 999)
    return S.mean(ts), S.stdev(ts) / len(ts) ** .5
if __name__ == '__main__':
    import time
    t0 = time.time()
    print('v10', ev({}), time.time() - t0)
    for cap, phw, pw in [(5, 0.75, 3.8), (5, 0.75, 4.0), (5, 0.7, 4.0), (5, 0.8, 3.9), (4, 0.62, 4.3), (4, 0.65, 4.6), (6, 0.8, 3.8), (6, 0.75, 3.8)]:
        print(cap, phw, pw, ev(dict(CAP=cap, PH_W=phw, P_W=pw)))
