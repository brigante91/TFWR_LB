from prog11 import ev
from t10 import BEST
N = 10
print('best', ev(BEST, N))
for step, md in [(0.14, 0.06), (0.17, 0.06), (0.2, 0.08), (0.25, 0.1)]:
    print('defer', step, md, ev(dict(BEST, DEFER=True, STEP=step, MD=md), N))
print('jit 4', ev(dict(BEST, JIT=4.0), N))
print('jit 4 ph .70', ev(dict(BEST, JIT=4.0, PH_W=0.70), N))
print('jit 4 ph .68 pw 3.7', ev(dict(BEST, JIT=4.0, PH_W=0.68, P_W=3.7), N))
print('WF 7.7', ev(dict(BEST, WF=7.7), N))
print('WF 6.5', ev(dict(BEST, WF=6.5), N))
