"""Esegue lb_hay_single_v1.py in Python con un campo 8x8 finto (regole di haysim: companion,
crescita 3037.5/(1+4w), acqua con decadimento stocastico, serbatoio +1 ogni 237.3 tick).
Conta solo i tick delle funzioni del gioco (azioni 200, letture 1): il costo dell'interprete
manca, quindi il tempo e' una stima bassa. Serve a verificare la correttezza.
uso: python3 emulate.py [seed ...]"""
import random, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
S = 8
D3 = [(dx, dy) for dx in range(-3, 4) for dy in range(-3, 4) if (dx or dy) and abs(dx) + abs(dy) <= 3]


class Done(Exception):
    pass


def run(seed):
    rng = random.Random(seed)
    T = [0.0]
    ent = {}      # pos -> ["grass", prog, tlast, comp] | ["bush"]
    water = {}
    wt = {}
    st = dict(hay=0, tank_used=0, pos=(0, 0), free=0, unripe_valid=0, bush_harvest=0, valid=0, harv=0)

    def comp(p):
        k = rng.choice(["Bush", "Carrot", "Tree"])
        dx, dy = rng.choice(D3)
        return (k, ((p[0] + dx) % S, (p[1] + dy) % S))

    for x in range(S):
        for y in range(S):
            ent[(x, y)] = ["grass", 1.0, 0.0, comp((x, y))]
            water[(x, y)] = 0.0; wt[(x, y)] = 0.0

    def upd(p):
        now = T[0]; e = ent[p]
        n = int(now // 607.5) - int(wt[p] // 607.5)
        w0 = water[p]
        k = sum(1 for _ in range(max(0, n)) if rng.random() < 0.1)
        w1 = w0 * 0.99 ** k
        if e[0] == "grass":
            e[1] = min(1.0, e[1] + (now - e[2]) * (1 + 2 * (w0 + w1)) / 3037.5); e[2] = now
        water[p] = w1; wt[p] = now

    def tank():
        return int(T[0] / (6075 * 20 / 512)) - st["tank_used"]

    def move(d):
        x, y = st["pos"]; dx, dy = {"East": (1, 0), "West": (-1, 0), "North": (0, 1), "South": (0, -1)}[d]
        st["pos"] = ((x + dx) % S, (y + dy) % S); T[0] += 200; st["moved"] = True; return True

    def harvest():
        p = st["pos"]; upd(p); e = ent[p]
        if st.get("moved") and e[0] == "grass" and e[1] < 1:
            st["unripe_valid"] += 1
        st["moved"] = False
        if e[0] == "bush":
            st["bush_harvest"] += 1
        else:
            st["harv"] += 1
            if e[1] >= 1:
                c = e[3]
                if c[0] == "Bush" and ent[c[1]][0] == "bush":
                    st["hay"] += 81920; st["valid"] += 1
                else:
                    st["hay"] += 512
            ent[p] = ["grass", 0.0, T[0], comp(p)]
        T[0] += 200; return True

    def plant(kind):
        p = st["pos"]; ent[p] = ["bush"]; T[0] += 200; return True

    def get_companion():
        T[0] += 1; e = ent[st["pos"]]
        return (e[3][0], e[3][1]) if e[0] == "grass" else ("Grass", (0, 0))

    def can_harvest():
        st["moved"] = False
        T[0] += 1; p = st["pos"]; upd(p); e = ent[p]
        return e[0] == "grass" and e[1] >= 1

    def get_water():
        T[0] += 1; upd(st["pos"]); return water[st["pos"]]

    def use_item(item, n=1):
        if tank() < n:
            T[0] += 1; return False
        p = st["pos"]; upd(p); st["tank_used"] += n; water[p] = min(1.0, water[p] + 0.25 * n); T[0] += 200; return True

    def num_items(item):
        T[0] += 1; return st["hay"]

    class E: Bush = "Bush"
    class I: Hay = "hay"; Water = "water"
    env = dict(move=move, harvest=harvest, plant=plant, get_companion=get_companion, can_harvest=can_harvest,
               get_water=get_water, use_item=use_item, num_items=num_items, Entities=E, Items=I,
               East="East", West="West", North="North", South="South")
    src = open(os.path.join(HERE, "..", os.environ.get("SCRIPT", "lb_hay_single_v1.py"))).read().replace("\t", "    ")
    # controllo dei raccolti a vuoto sull'erba (valido atteso ma acerba): avvolge harvest
    exec(compile(src, "lb_hay_single_v1.py", "exec"), env)
    return T[0] / 6075, st


if __name__ == "__main__":
    seeds = [int(a) for a in sys.argv[1:]] or list(range(6))
    for s in seeds:
        t, st = run(s)
        print("seme %d: fine %.2f s (solo azioni), fieno %d, validi %d, raccolti %d, su cespuglio %d, acerbi dopo mossa %d, acqua usata %d" % (
            s, t, st["hay"], st["valid"], st["harv"], st["bush_harvest"], st["unripe_valid"], st["tank_used"]))
