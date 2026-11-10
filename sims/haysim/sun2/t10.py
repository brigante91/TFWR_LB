import sim3, prog11, sys
gl = [1.5, 1.2, 1.0, 0.85, 0.8, 0.7, 0.6, 0.5, 0.45, 0.4, 0.35, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3]
BEST = dict(MERGE15=False, G_W=0.85, DEFER=False, PREPOS=True, LMIN_LIST=[3, 3, 3, 2.5, 2.5, 2], GW_LIST=gl, PACE=True, WB=4000, PH_W=0.72, CAP=7)
def rounds(P, seed=0):
    log = []
    oh = sim3.World.harvest
    def h(self, c, tick):
        b, z, n = self.nboost, self.nzmax, self.nnotmax
        oh(self, c, tick)
        log.append((self.time(tick), self.nboost - b, self.nzmax - z, self.nnotmax - n, self.tank_used))
    sim3.World.harvest = h
    Q = dict(P, RANDGOAL=False)
    r = prog11.sim11(Q, seed, stats=True)
    sim3.World.harvest = oh
    D = dict(prog11.DEF); D.update(Q)
    # confini dei round
    t = 0.0; rr = 0; out = []
    while t < r['t']:
        pw = D['P_W0'] if rr == 0 else prog11.lget(D['PW_LIST'], rr - 1, D['P_W'])
        gw = D['G_W0'] if rr == 0 else prog11.lget(D['GW_LIST'], rr - 1, D['G_W'])
        nph = (16 - D['MINV']) - (1 if D['MERGE15'] else 0)
        ph = [D['PH_W']] * nph
        if rr == 0: ph[0] = D['PH_W0']
        t2 = t + pw + gw + sum(ph)
        xs = [x for x in log if t <= x[0] < t2]
        out.append((rr, t, t2 - t, sum(x[1] for x in xs), sum(x[2] for x in xs), sum(x[3] for x in xs), xs[-1][4] if xs else 0))
        t = t2; rr += 1
    return r, out
if __name__ == '__main__':
    r, out = rounds(BEST)
    print(r['t'], r['boost'], 'zmax', r['zmax'], 'notmax', r['notmax'], 'lost', r['lost'], 'tank', r['tank'])
    print({k: (round(v, 1) if isinstance(v, float) else v) for k, v in sorted(r['st'].items())})
    for o in out:
        print('round %2d da %6.1f dur %5.2f boost %4d zmax %3d notmax %3d tank %4d (prod %4d)  rate %.1f/s' % (o[0], o[1], o[2], o[3], o[4], o[5], o[6], int((o[1] + o[2]) * 25.6), o[3] / o[2]))
