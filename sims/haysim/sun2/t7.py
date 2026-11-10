from prog11 import ev, sim11
N = 10
B = dict(MERGE15=False, G_W=0.85, DEFER=False, PREPOS=True, LMIN_LIST=[3, 3, 3, 2.5, 2.5, 2], GW_LIST=[1.5, 1.2, 1.0])
print('base', ev(B, N))
gl = [1.5, 1.2, 1.0, 0.85, 0.8, 0.7, 0.6, 0.5, 0.45, 0.4, 0.35, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3]
print('G decrescente', ev(dict(B, GW_LIST=gl), N))
print('G decrescente WF 8', ev(dict(B, GW_LIST=gl, WF=8.0), N))
print('G decrescente WF 8.4 WL 9', ev(dict(B, GW_LIST=gl, WF=8.4, WL=9), N))
gl2 = [1.5, 1.2, 1.0, 0.85, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
print('G -> 0.1 WF 8.4', ev(dict(B, GW_LIST=gl2, WF=8.4, WL=9), N))
r = sim11(dict(B, GW_LIST=gl, WF=8.4, WL=9, RANDGOAL=False), 0, stats=True)
print(r['t'], r['boost'], r['zmax'], r['notmax'], r['tank'], r['st'].get('waterfail'), r['st'].get('water'))
