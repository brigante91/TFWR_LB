import json, sim3
from tune import build, X0
from prog11 import ev
x = dict(X0); x.update(json.load(open('tune_best.json')))
N = 8
print('best', ev(build(x), N))
for grow in (3.0, 1.4, 0.01):
    sim3.GROW = grow
    y = dict(x)
    print('GROW', grow, ev(build(y), N))
    y = dict(x, ginf=0.05, g1=0.05, linf=0.01, l0=0.01, gw0=max(0.1, grow * 0.65))
    print('   G~0 LMIN 0', ev(build(y), N))
    y = dict(y, pw=3.5, ph=0.68, wb=3600)
    print('   + pw 3.5 ph .68', ev(build(y), N))
    y = dict(y, minv=8, pw=3.2, ph=0.66, wb=3500)
    print('   + minv 8 pw 3.2 ph .66', ev(build(y), N))
sim3.GROW = 7.0
