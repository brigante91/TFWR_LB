from prog12 import show, ev
B = dict(CAP=5, PH=[0.72] * 9, P_W=3.3, G_W=0.85, LMIN=1.5, BEAT=False)
show(dict(B, CASC=False))
show(dict(B, CASC=False, BEAT=True))
show(dict(B, CASC=True, BEAT=True, LC=15))
show(dict(B, CASC=True, BEAT=True, LC=13, PH=[0.8, 0.8, 0.8, 0.75, 0.8, 0.85, 0.9, 0.9, 0.9]))
show(dict(B, CASC=True, BEAT=True, LC=12, KEEPGAP=2, PH=[0.8, 0.8, 0.8, 0.8, 0.8, 0.85, 0.9, 0.9, 0.9]))
