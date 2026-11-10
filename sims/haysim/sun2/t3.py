from prog11 import ev
import itertools
base = dict(DEFER=False)
print('v10 equiv', ev(dict(MERGE15=False, G_W=0.85, DEFER=False, PREPOS=False, LATE14=True), 12))
print('v10 + prepos', ev(dict(MERGE15=False, G_W=0.85, DEFER=False, PREPOS=True, LATE14=True), 12))
print('v10 + prepos ph .8', ev(dict(MERGE15=False, G_W=0.85, DEFER=False, PREPOS=True, LATE14=True, PH_W=0.8), 12))
for gw, no15, d15, pw in itertools.product([1.2, 1.4, 1.6], [1.5, 2.0], [0.3, 0.5], [3.8, 4.0]):
    P = dict(base, G_W=gw, NO15=no15, D15=d15, P_W=pw)
    print(gw, no15, d15, pw, ev(P, 12))
