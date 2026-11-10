import json
from gen_sun11 import params
from prog11 import ev
x = json.load(open('best9.json'))
N = 12
P = params(x)
print('best', ev(P, N))
for wf0, wl0, gw0, l0 in [(7, 12, 4.5, 3.0), (8.4, 12, 4.0, 3.0), (8.4, 12, 3.5, 3.0), (8.4, 12, 3.5, 4.0), (8.4, 12, 3.0, 4.2), (7.7, 10, 3.5, 3.5), (8.4, 12, 2.5, 4.2)]:
    Q = dict(P, WFL_LIST=[(wf0, wl0)], G_W0=gw0)
    Q['LMIN_LIST'] = [l0] + P['LMIN_LIST'][1:]
    print(wf0, wl0, gw0, l0, ev(Q, N))
for wfl in ([(7, 7), (7.7, 9), (7.7, 9), (7.7, 9)], [(7, 7), (8.4, 10), (8.4, 10), (8.0, 9), (7.7, 8)], [(7, 7), (6.5, 7), (6.5, 7), (6.5, 7)]):
    print('wfl', wfl, ev(dict(P, WFL_LIST=wfl), N))
