"""Discesa per coordinate sui parametri della v11 (prog11), semi comuni."""
import math, sys, json, time
from prog11 import sim11
import statistics as S

def build(x):
    gl = [x['ginf'] + (x['g1'] - x['ginf']) * math.exp(-i / x['gtau']) for i in range(24)]
    ll = [x['linf'] + (x['l0'] - x['linf']) * math.exp(-i / x['ltau']) for i in range(25)]
    P = dict(MERGE15=False, DEFER=False, PREPOS=True, PACE=True, GW_LIST=[round(g, 3) for g in gl],
             LMIN_LIST=[round(l, 3) for l in ll], P_W=x['pw'], PH_W=x['ph'], WB=x['wb'], CAP=int(x['cap']),
             TAU=x['tau'], WF=x['wf'], WL=x['wl'], P_W0=x['pw0'], G_W0=x['gw0'], PH_W0=x['ph0'], MINV=int(x['minv']))
    return P

X0 = dict(ginf=0.3, g1=1.5, gtau=4.0, linf=2.0, l0=3.0, ltau=4.0, pw=3.8, ph=0.72, wb=4000, cap=7, tau=0.075,
          wf=7.0, wl=7.0, pw0=10.5, gw0=4.5, ph0=1.5, minv=9)
STEPS = dict(ginf=0.1, g1=0.25, gtau=1.5, linf=0.3, l0=0.5, ltau=1.5, pw=0.1, ph=0.02, wb=200, cap=1, tau=0.008,
             wf=0.4, wl=1.0, pw0=0.4, gw0=0.4, ph0=0.15, minv=0)

def f(x, n):
    P = build(x)
    ts = []
    for s in range(n):
        r = sim11(P, s)
        ts.append(r['t'] if r['ok'] else 999.0)
    return S.mean(ts)

if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    x = dict(X0)
    if len(sys.argv) > 2:
        x.update(json.load(open(sys.argv[2])))
    best = f(x, n)
    print('start', best, flush=True)
    for it in range(3):
        improved = False
        for k in STEPS:
            if STEPS[k] == 0:
                continue
            for sgn in (+1, -1):
                while True:
                    y = dict(x)
                    y[k] = round(x[k] + sgn * STEPS[k], 4)
                    if y[k] <= 0:
                        break
                    v = f(y, n)
                    if v < best - 0.15:
                        best, x = v, y
                        improved = True
                        print('  %s -> %s : %.2f' % (k, y[k], v), flush=True)
                    else:
                        break
        print('iter', it, best, json.dumps(x), flush=True)
        json.dump(x, open('tune_best.json', 'w'))
        if not improved:
            break
