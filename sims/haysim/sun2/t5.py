import sim3
from prog11 import ev
N = 8
B = dict(MERGE15=False, G_W=0.85, DEFER=False, PREPOS=True, RANDGOAL=False)
print('base', ev(B, N))
g0 = sim3.GROW
sim3.GROW = 1.4
print('crescita 1.4 s (come acqua piena)', ev(B, N))
print('  + G 0.3', ev(dict(B, G_W=0.3, G_W0=1.0), N))
print('  + G 0.3, merge', ev(dict(B, MERGE15=True, G_W=0.9, G_W0=1.5), N))
sim3.GROW = 0.01
print('crescita 0', ev(B, N))
print('  + G 0.05', ev(dict(B, G_W=0.05, G_W0=0.1), N))
print('  + G 0.05 PH .75', ev(dict(B, G_W=0.05, G_W0=0.1, PH_W=0.75), N))
print('  + merge G .75', ev(dict(B, MERGE15=True, G_W=0.75, G_W0=1.5), N))
sim3.GROW = g0
