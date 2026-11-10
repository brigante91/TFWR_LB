"""Statistiche della v10 nel simulatore tarato: dove va il tempo dei droni."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import sunprog, sunsim2
from sunprog import BASE, GOAL0

V10 = dict(P_W=3.8, P_W0=10.5, G_W=0.85, G_W0=4.5, PH_W=0.85, PH_W0=1.5, CAP=6, MINV=9,
           WFACT=7.0, WLEFT=7.0, NO15_LATE=1.5, FIXDIR=True, LATE14=True, ANY_STOP=True,
           STOP_AT=GOAL0 + 10)

ST = {}

def wrap(gen):
    send = None
    while True:
        try:
            req = gen.send(send)
        except StopIteration:
            return
        k = req[1]
        if k == 'wait':
            t = yield (req[0], 'time')
            ST['code'] = ST.get('code', 0) + req[0]
            ST['idle'] = ST.get('idle', 0) + max(0.0, req[2] - t)
            ST['nwait'] = ST.get('nwait', 0) + 1
            send = yield (0, 'wait', req[2])
            continue
        if k == 'spawn':
            f = req[2]
            req = (req[0], 'spawn', (lambda f: (lambda d: wrap(f(d))))(f))
        # req[0] = azioni (multipli di 200) + codice
        a = (req[0] // 200) * 200 if req[0] >= 200 else 0
        ST['act'] = ST.get('act', 0) + a
        ST['code'] = ST.get('code', 0) + req[0] - a
        ST[k] = ST.get(k, 0) + 1
        send = yield req

def run(seed):
    ST.clear()
    Q = dict(BASE); Q.update(V10)
    r = sunsim2.simulate(lambda d, P, m: wrap(sunprog.main_prog7(d, P, m)), Q, seed)
    return r, dict(ST)

if __name__ == '__main__':
    import statistics as S
    ts = []
    for seed in range(8):
        r, st = run(seed)
        ts.append(r['t'])
        if seed == 0:
            T = r['t']
            tot = 32 * T
            print('t', T, 'ok', r['ok'], 'boost', r['boost'], 'plain', r['plain'], 'zero', r['zero'], 'lost', r['lost'], 'tank', r['tank'])
            print({k: round(v, 1) for k, v in st.items()})
            print('idle s/drone', st['idle'] / 32, 'frac', st['idle'] / tot)
            mv = st['act'] / 200
            print('azioni in moto (move+till, dentro req[0])', mv, 'tick', st['act'], 's/drone', st['act'] / 6075 / 32)
            print('codice s/drone', st['code'] / 6075 / 32)
            for k in ('plant', 'harv', 'water'):
                print(k, st.get(k), 's/drone', st.get(k, 0) * 200 / 6075 / 32)
    print('media', S.mean(ts), ts)
