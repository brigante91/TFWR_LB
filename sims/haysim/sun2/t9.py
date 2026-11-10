from prog11 import ev
N = 10
gl = [1.5, 1.2, 1.0, 0.85, 0.8, 0.7, 0.6, 0.5, 0.45, 0.4, 0.35, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3]
B = dict(MERGE15=False, G_W=0.85, DEFER=False, PREPOS=True, LMIN_LIST=[3, 3, 3, 2.5, 2.5, 2], GW_LIST=gl)
print('base', ev(B, N))
print('pace', ev(dict(B, PACE=True), N))
for pw in (3.6, 3.4, 3.2):
    print('pace pw', pw, ev(dict(B, PACE=True, P_W=pw), N))
for wb, ph in [(4400, 0.8), (4000, 0.75), (4000, 0.72), (3600, 0.7), (3600, 0.66), (3300, 0.62)]:
    print('pace wb', wb, ph, ev(dict(B, PACE=True, WB=wb, PH_W=ph, CAP=7), N), ev(dict(B, PACE=True, WB=wb, PH_W=ph, CAP=7, P_W=3.6), N))
