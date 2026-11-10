import json
from gen_sun11 import params
from prog11 import ev
x = json.load(open('best9.json'))
N = 12
P = params(x)
print('best', ev(P, N))
gl = P['GW_LIST']
for add in (0.5, 0.7, 0.9):
    Q = dict(P, MERGE15=True, GW_LIST=[g + add for g in gl], G_W=P['G_W'] + add)
    print('merge15 +', add, ev(Q, N), ev(dict(Q, D15=0.5), N))
print('prepos off', ev(dict(P, PREPOS=False), N))
print('pace off', ev(dict(P, PACE=False), N))
print('wb off', ev(dict(P, WB=None, CAP=6, PH_W=0.85), N))
print('lmin const 1.5', ev(dict(P, LMIN_LIST=None, LMIN=1.5), N))
print('gw const .85', ev(dict(P, GW_LIST=None, G_W=0.85), N))
print('wmax 3', ev(dict(P, WMAX=3), N))
print('jit 4', ev(dict(P, JIT=4.0), N))
