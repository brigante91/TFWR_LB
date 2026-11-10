import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import sunprog, sunsim2
from base_stats import V10
from sunprog import BASE
# conta per round: boost, zmax (massimo non cresciuto), lost, acqua usata, fallimenti acqua
orig_h = sunsim2.World.harvest
log = []
def h(self, c, tick):
    b, z, l = self.nboost, self.nzmax, self.nlost
    orig_h(self, c, tick)
    log.append((self.time(tick), self.nboost - b, self.nzmax - z, self.nlost - l, self.tank_used))
sunsim2.World.harvest = h
Q = dict(BASE); Q.update(V10)
r = sunsim2.simulate(sunprog.main_prog7, Q, 0)
print(r['t'], r['boost'], r['zmax'], r['notmax'], r['lost'], r['tank'])
# confini dei round: 0, 16.5, poi ogni 10.6
b = [0, 10.5 + 4.5 + 1.5 + 6 * 0.85]
while b[-1] < r['t']:
    b.append(b[-1] + 3.8 + 0.85 + 7 * 0.85)
W = r['W']
for i in range(len(b) - 1):
    xs = [x for x in log if b[i] <= x[0] < b[i + 1]]
    print('round', i, 'da', round(b[i], 1), 'boost', sum(x[1] for x in xs), 'zmax', sum(x[2] for x in xs), 'lost', sum(x[3] for x in xs))
import statistics
print('acqua media celle a fine run', statistics.mean(W.water_now(c, r['t']) for c in range(1024)))
print('--- serbatoio')

import bisect
ts = [x[0] for x in log]
for t in list(range(5, 160, 10)):
    i = bisect.bisect(ts, t) - 1
    if i >= 0:
        print('t', t, 'prodotta', int(t / sunsim2.TANK_DT), 'usata', log[i][4], 'scorta', int(t / sunsim2.TANK_DT) - log[i][4])
