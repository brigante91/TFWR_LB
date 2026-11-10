from prog11 import ev
import itertools
N = 10
B = dict(MERGE15=False, G_W=0.85, DEFER=False, PREPOS=True, LMIN_LIST=[3, 3, 3, 2.5, 2.5, 2], GW_LIST=[1.5, 1.2, 1.0])
print('base', ev(B, N))
for minv, cap, ph, pw in [(8, 6, 0.85, 3.6), (8, 5, 0.75, 3.6), (8, 5, 0.72, 3.4), (7, 5, 0.72, 3.2), (7, 5, 0.75, 3.4), (7, 4, 0.62, 3.4), (7, 4, 0.66, 3.6), (7, 6, 0.8, 3.2), (8, 4, 0.65, 3.8)]:
    print(minv, cap, ph, pw, ev(dict(B, MINV=minv, CAP=cap, PH_W=ph, P_W=pw), N))
