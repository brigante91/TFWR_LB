import json, sys
from gen_sun11 import params
from prog11 import sim11
from harness import Game
x = json.load(open('best9.json'))
P = dict(params(x), RANDGOAL=False)
for seed in (0, 1, 2):
    r = sim11(P, seed, stats=True)
    h = Game('../../lb_sunflowers_v11.py', seed, 5.0).run()
    h10 = Game('../../lb_sunflowers_v10.py', seed, 5.0).run()
    print('seed', seed, 'sim11 %.1f boost %d zmax %d notmax %d tank %d | harness v11 %.1f boost %d zmax %d notmax %d tank %d %s | harness v10 %.1f boost %d zmax %d notmax %d' % (
        r['t'], r['boost'], r['zmax'], r['notmax'], r['tank'], h['t'], h['boost'], h['zmax'], h['notmax'], h['tank'],
        {k: v for k, v in h['cnt'].items() if 'fail' in k}, h10['t'], h10['boost'], h10['zmax'], h10['notmax']))
