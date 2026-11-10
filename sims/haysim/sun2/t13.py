from prog12 import show, ev
B = dict(CAP=5, PH=[0.72] * 9, P_W=3.3, G_W=0.85, LMIN=1.5, BEAT=False)
print('nocasc', ev(dict(B, CASC=False), 8))
print('casc15', ev(dict(B, CASC=True, LC=15), 8))
print('casc15 ph15 .85', ev(dict(B, CASC=True, LC=15, PH=[0.85] + [0.72] * 8), 8))
print('casc15 gap2', ev(dict(B, CASC=True, LC=15, KEEPGAP=2, PH=[0.85] + [0.72] * 8), 8))
print('casc15 cap6 .8', ev(dict(B, CASC=True, LC=15, CAP=5, PH=[0.85] + [0.72] * 3 + [0.8] * 5), 8))
