import json
from tune import build, X0
from prog11 import ev
x = dict(X0); x.update(json.load(open('tune_best.json')))
N = 10
print('best9', ev(build(x), N))
for minv, pw, ph, wb, cap in [(7, 3.0, 0.62, 3300, 8), (7, 2.8, 0.62, 3300, 8), (7, 3.0, 0.66, 3500, 8), (7, 3.2, 0.66, 3500, 8), (7, 3.0, 0.58, 3100, 8),
                              (8, 3.4, 0.68, 3600, 8), (8, 3.2, 0.66, 3500, 8), (8, 3.4, 0.64, 3400, 8)]:
    y = dict(x, minv=minv, pw=pw, ph=ph, wb=wb, cap=cap)
    print(minv, pw, ph, wb, cap, ev(build(y), N))
