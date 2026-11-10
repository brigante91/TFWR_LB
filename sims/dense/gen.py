import json
S = 32
plan = json.load(open(__import__("os").environ.get("PLAN","plan.json")))
src_old = open("../lb_hay_micro.py").read()
body = src_old[src_old.index("def warmup("):src_old.index("def run_range(")]

def steps(a, b):
    out = []
    dx = (b[0] - a[0]) % S
    if dx <= S // 2: out += ["East"] * dx
    else: out += ["West"] * (S - dx)
    dy = (b[1] - a[1]) % S
    if dy <= S // 2: out += ["North"] * dy
    else: out += ["South"] * (S - dy)
    return out

routes = []
params = []
for i, p in enumerate(plan):
    path = [tuple(c) for c in p["path"]]
    lines = [f"def r{i}():"]
    nacts = 0
    for k in range(1, len(path)):
        for d in steps(path[k - 1], path[k]):
            lines.append(f"\tmove({d})"); nacts += 1
        if k < len(path) - 1:
            lines.append("\tplant(BUSH)"); nacts += 1
    assert nacts == p["moves"] + p["plants"], (i, nacts)
    routes.append("\n".join(lines))
    A = tuple(p["A"]); C = tuple(p["C"])
    d2 = "East" if C[0] == (A[0] + 1) % S else "West"
    d1 = "West" if d2 == "East" else "East"
    assert C[1] == A[1] and ((C[0] - A[0]) % S in (1, S - 1))
    params.append(f"({A[0]}, {A[1]}, {C[0]}, {C[1]}, {d1}, {d2})")

head = '''# Classifica Hay: 2e9 fieno, 32 droni. Disposizione densa delle coppie d'erba.
# Le coppie stanno su un reticolo (6,0),(3,2) intorno all'origine: nessuna erba estranea entro
# distanza 3 (companion valido 23/72 come prima), ma i cespugli sono condivisi tra coppie:
# 421 cespugli invece di 960, circa 34.5 azioni di preparazione per drone invece di circa 72.
# Simulatore: circa 108.2 s (disposizione a blocchi 4x8: circa 109.05 s).
# Raccolta, acqua e fine run identiche alla versione precedente.
GOAL = 2000000000
NEAR = GOAL - 50000000
W = 0.7       # soglia acqua nella fase iniziale (solo durante le attese)
W0 = 0.4      # soglia piu' bassa nei primi cicli: il serbatoio parte vuoto
EARLY = 13    # cicli iniziali con W0 (simulatore: 12-14 meglio di 9 di circa 0.03 s)
WR = 0.73     # soglia acqua a regime (controllata ogni 8 cicli)
THR = 64      # passaggio al regime quando il serbatoio supera questa scorta

S = get_world_size()
BUSH = Entities.Bush
HAY = Items.Hay
WATER = Items.Water
BLOCKS = 32

OFFS = [
	(0, 1), (0, 2), (0, 3), (0, -1), (0, -2), (0, -3),
	(1, 0), (2, 0), (3, 0), (-1, 0), (-2, 0), (-3, 0),
	(1, 1), (1, 2), (2, 1), (1, -1), (1, -2), (2, -1),
	(-1, 1), (-1, 2), (-2, 1), (-1, -1), (-1, -2), (-2, -1)
]


def ok_dict(x, y, px, py):
	other = (px, py)
	d = {}
	for o in OFFS:
		p = ((x + o[0]) % S, (y + o[1]) % S)
		if p != other:
			d[(BUSH, p)] = True
	return d


# percorsi di piantagione: dall'origine, pianta i cespugli assegnati, finisce sull'erba A
'''

start = '''

def start(ax, ay, cx, cy, d1, d2):
	# primo ciclo senza dizionari: l'erba iniziale e' gia' matura
	A = (ax, ay)
	C = (cx, cy)
	harvest()
	while True:
		while get_companion()[0] != BUSH:
			harvest()
		if get_companion()[1] != C:
			break
		harvest()
	move(d2)
	harvest()
	while True:
		while get_companion()[0] != BUSH:
			harvest()
		if get_companion()[1] != A:
			break
		harvest()
	use_item(WATER)   # C parte a secco
	move(d1)
	use_item(WATER)   # A parte a secco
	okA = ok_dict(ax, ay, cx, cy)
	okC = ok_dict(cx, cy, ax, ay)
	return okA, okC


'''

tail = '''def run_range(lo, hi):
	while hi - lo > 1:
		mid = (lo + hi) // 2
		spawn_drone(run_range, mid, hi)
		hi = mid
	ROUTES[lo]()
	ax, ay, cx, cy, d1, d2 = PARAMS[lo]
	okA, okC = start(ax, ay, cx, cy, d1, d2)
	warmup(okA, okC, d1, d2)
	if lo == 0:
		farm_main(okA, okC, d1, d2)
		clear()
	else:
		farm(okA, okC, d1, d2)


run_range(0, BLOCKS)
'''

routes_list = "ROUTES = [" + ", ".join(f"r{i}" for i in range(32)) + "]"
params_list = "# (ax, ay, cx, cy, d1, d2): d2 va da A a C, d1 da C ad A\nPARAMS = [\n" + ",\n".join("\t" + p for p in params) + "\n]"
src = head + "\n\n\n".join(routes) + "\n\n\n" + routes_list + "\n" + params_list + start + body + tail
open("../lb_hay_dense.py", "w").write(src)
import ast; ast.parse(src.replace("\t", "    "))
print("ok", src.count("\n"), "righe")
