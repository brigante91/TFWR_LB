from harness import Game
import statistics as S
for opc in (5.0, 8.0):
    a, b = [], []
    for seed in (0, 1, 2, 3):
        h = Game('../../lb_sunflowers_v11.py', seed, opc).run()
        h10 = Game('../../lb_sunflowers_v10.py', seed, opc).run()
        a.append(h['t']); b.append(h10['t'])
        bad = {k: v for k, v in h['cnt'].items() if 'fail' in k and k != 'water_fail'}
        print('opc', opc, 'seed', seed, 'v11 %.1f (boost %d zmax %d notmax %d lost %d %s) v10 %.1f (notmax %d)' % (h['t'], h['boost'], h['zmax'], h['notmax'], h['lost'], bad, h10['t'], h10['notmax']))
    print('opc', opc, 'media v11 %.1f v10 %.1f' % (S.mean(a), S.mean(b)))
