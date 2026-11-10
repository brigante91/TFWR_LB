import json, sim3
from gen_sun11 import params
from prog11 import ev
x = json.load(open('best9.json'))
N = 16
V10 = dict(MERGE15=False, G_W=0.85, DEFER=False, PREPOS=False, LATE14=True, PACE=False, LMIN=1.5)
print('v11', ev(params(x), N))
for ph, wb in [(0.70, 3600), (0.72, 3600), (0.72, 4000), (0.74, 3800), (0.74, 4000), (0.70, 3800)]:
    print(ph, wb, ev(params(dict(x, ph=ph, wb=wb)), N))
print('--- robustezza (v10 / v11)')
for name, kw, pre in [('base', {}, None), ('jit 400', dict(JIT=400.0), None), ('grow 7.4', {}, ('GROW', 7.4)), ('grow 6.6', {}, ('GROW', 6.6)), ('tank -10%', {}, ('TANK_DT', sim3.TANK_DT * 1.1))]:
    old = None
    if pre:
        old = getattr(sim3, pre[0]); setattr(sim3, pre[0], pre[1])
    print(name, ev(dict(V10, **kw), N), ev(dict(params(x), **kw), N))
    if pre:
        setattr(sim3, pre[0], old)
