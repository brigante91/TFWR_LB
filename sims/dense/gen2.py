"""Genera ../lb_hay_dense2.py da un piano in formato azioni (split2.py).
Differenze rispetto a lb_hay_dense.py:
 - visita anticipata di A e C a meta' percorso (primo harvest + reroll economico se il companion
   iniziale non e' valido): la prima ricrescita a secco avviene mentre si piantano gli altri cespugli;
 - dizionari dei companion validi come letterali (1+len tick invece di ~16 per voce);
 - al rientro su A: harvest+reroll, acqua, mossa, idem su C (poi warmup/farm identici).
uso: PLAN=plan_split2.json python3 gen2.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layout import S

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = os.environ.get("PLAN", os.path.join(HERE, "plan_split2.json"))
OUT = os.environ.get("OUT", os.path.join(HERE, "..", "lb_hay_dense2.py"))
plan = json.load(open(PLAN))
assert len(plan) == 32

OFFS = [(dx, dy) for dx in range(-3, 4) for dy in range(-3, 4) if (dx or dy) and abs(dx) + abs(dy) <= 3]
OFFS.sort(key=lambda o: (o[1], o[0]))

src_old = open(os.path.join(HERE, "..", "lb_hay_dense.py")).read()
body = src_old[src_old.index("def warmup("):src_old.index("def run_range(")]


def diamond(cell, other):
    return [((cell[0] + dx) % S, (cell[1] + dy) % S) for dx, dy in OFFS if ((cell[0] + dx) % S, (cell[1] + dy) % S) != other]


def dict_lit(cell, other):
    return "{" + ", ".join("(BUSH, (%d, %d)): True" % p for p in diamond(cell, other)) + "}"


routes = []
dirs = []
for i, p in enumerate(plan):
    A = tuple(p["A"]); C = tuple(p["C"])
    lines = ["def r%d():" % i]
    for a in p["actions"]:
        if a[0] == "move":
            lines.append("\tmove(%s)" % a[1])
        elif a[0] == "plant":
            lines.append("\tplant(BUSH)")
        elif a[0] == "early":
            other = C if a[1] == "A" else A
            lines.append("\tearly((%d, %d))" % other)
        else:
            raise ValueError(a)
    lines.append("\tokA = %s" % dict_lit(A, C))
    lines.append("\tokC = %s" % dict_lit(C, A))
    lines.append("\treturn okA, okC")
    routes.append("\n".join(lines))
    assert C[1] == A[1] and (C[0] - A[0]) % S in (1, S - 1), (i, A, C)
    d2 = "East" if C[0] == (A[0] + 1) % S else "West"
    d1 = "West" if d2 == "East" else "East"
    dirs.append("(%s, %s)" % (d1, d2))

head = '''# Classifica Hay: 2e9 fieno, 32 droni. Disposizione densa delle coppie d'erba (reticolo (6,0),(3,2),
# 421 cespugli condivisi) come lb_hay_dense.py, con tre modifiche misurate su haysim/dsim.py:
#  1. visita anticipata: ogni percorso passa su A e C a meta' piantagione; se il companion iniziale
#     non e' gia' valido si raccoglie e si rerolla subito, cosi' la prima ricrescita (a secco, 0.5 s)
#     avviene mentre il drone pianta il resto dei cespugli invece di farlo aspettare;
#  2. dizionari dei companion validi come letterali (circa 70 tick ciascuno invece di circa 390);
#  3. al rientro su A: harvest+reroll, acqua, mossa (idem su C), poi warmup e regime identici.
# Simulatore (dsim.py, 96 run, stesse sequenze di companion): circa -0.04 s rispetto a lb_hay_dense.
GOAL = 2000000000
NEAR = GOAL - 50000000
W = 0.7       # soglia acqua nella fase iniziale (solo durante le attese)
W0 = 0.4      # soglia piu' bassa nei primi cicli: il serbatoio parte vuoto
EARLY = 13    # cicli iniziali con W0
WR = 0.73     # soglia acqua a regime (controllata ogni 8 cicli; 0.71 produce raccolti acerbi)
THR = 64      # passaggio al regime quando il serbatoio supera questa scorta

BUSH = Entities.Bush
HAY = Items.Hay
WATER = Items.Water
BLOCKS = 32


def early(other):
	# visita anticipata: se il companion iniziale e' gia' un cespuglio valido lo si tiene,
	# altrimenti primo harvest e reroll economico (senza dizionario)
	c = get_companion()
	if c[0] == BUSH and c[1] != other:
		return
	harvest()
	while True:
		while get_companion()[0] != BUSH:
			harvest()
		if get_companion()[1] != other:
			return
		harvest()


# percorsi di piantagione: dall'origine, piantano i cespugli assegnati passando su A e C,
# finiscono su A e restituiscono i dizionari dei companion validi di A e di C
'''

first = '''

def first(okA, okC, d1, d2):
	# rientro su A: l'erba e' ricresciuta a secco durante la piantagione
	while not can_harvest():
		if get_water() < W0:
			use_item(WATER)
	harvest()
	while get_companion() not in okA:
		harvest()
	use_item(WATER)
	move(d2)
	while not can_harvest():
		if get_water() < W0:
			use_item(WATER)
	harvest()
	while get_companion() not in okC:
		harvest()
	use_item(WATER)
	move(d1)


'''

tail = '''def run_range(lo, hi):
	while hi - lo > 1:
		mid = (lo + hi) // 2
		spawn_drone(run_range, mid, hi)
		hi = mid
	okA, okC = ROUTES[lo]()
	d1, d2 = DIRS[lo]
	first(okA, okC, d1, d2)
	warmup(okA, okC, d1, d2)
	if lo == 0:
		farm_main(okA, okC, d1, d2)
		clear()
	else:
		farm(okA, okC, d1, d2)


run_range(0, BLOCKS)
'''

routes_list = "ROUTES = [" + ", ".join("r%d" % i for i in range(32)) + "]"
dirs_list = "# (d1, d2): d2 va da A a C, d1 da C ad A\nDIRS = [\n" + ",\n".join("\t" + d for d in dirs) + "\n]"
src = head + "\n\n\n".join(routes) + "\n\n\n" + routes_list + "\n" + dirs_list + first + body + tail
open(OUT, "w").write(src)
import ast
ast.parse(src.replace("\t", "    "))
print("ok", OUT, src.count("\n"), "righe")
