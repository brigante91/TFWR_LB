from prog11 import sim11
import sys
def show(P, seed=0):
    r = sim11(P, seed, stats=True)
    st = r['st']
    print(P, '\n  t %.1f boost %d plain %d zero %d lost %d zmax %d notmax %d tank %d | late %d h15seed %d defer %d/%d idle P %.0f 15 %.0f G %.0f H %.0f' % (
        r['t'], r['boost'], r['plain'], r['zero'], r['lost'], r['zmax'], r['notmax'], r['tank'], st.get('late_sweep', 0), st.get('h15_seed', 0),
        st.get('hdefer', 0), st.get('hdefer_seed', 0), st.get('idle_P', 0), st.get('idle_15', 0), st.get('idle_G', 0), st.get('idle_H', 0)))
if __name__ == '__main__':
    show(dict(RANDGOAL=False))
    show(dict(RANDGOAL=False, G_W=1.4))
    show(dict(RANDGOAL=False, G_W=1.4, P_W=4.1))
    show(dict(RANDGOAL=False, G_W=1.4, P_W=4.1, G_W0=6.0))
    show(dict(RANDGOAL=False, MERGE15=False, G_W=0.85, DEFER=False, PREPOS=False))
    show(dict(RANDGOAL=False, MERGE15=False, G_W=0.85, DEFER=False, PREPOS=False, LATE14=True))
