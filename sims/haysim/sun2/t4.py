from prog11 import ev
N = 12
B = dict(MERGE15=False, G_W=0.85, DEFER=False, PREPOS=True)
print('base lmin 1.5', ev(B, N))
for lm in (1.0, 2.0, 2.5, 3.0):
    print('lmin', lm, ev(dict(B, LMIN=lm), N))
for lml in ([4, 4, 3.5, 3, 2.5, 2], [5, 5, 4, 3.5, 3, 2.5, 2], [3, 3, 3, 2.5, 2.5, 2]):
    for gl in (None, [0.6, 0.6, 0.6, 0.7], [1.5, 1.2, 1.0]):
        print('lminlist', lml, 'gl', gl, ev(dict(B, LMIN_LIST=lml, GW_LIST=gl), N))
