# Classifica Rice_Single (1e5 riso, 1 drone, 8x8). v1 dell'8 nov 2026: versione snella di lb_rice.py v7.
# lb_rice.py v7 in gioco: 2:29.1. #1 2:19.294.
#
# Stesso schema (vedi lb_rice.py): per strato tre passate a serpentina sulle 64 celle
#   A2: scendi all'argilla e pianta;  B: raccogli, scava la terrazza secca, pianta sul 2o blocco;
#   A1: raccogli il 2o blocco (la terrazza secca la toglie il crollo nella A2 dopo).
# Acqua: alla semina, se la cella e' sotto S_LOW, la si riempie a 1.0 (circa una volta per cella).
# Ultimo strato: si piantano solo le celle che servono e si torna indietro raccogliendole.
#
# Differenza: l'interprete conta anche le istruzioni (if 1, chiamata 1, confronto 1, indice 1,
# for 1 a giro; decompilato, FINDINGS_cactus_dino_maze.md). La v7 spendeva ~70 tick di
# interprete per cella a strato (lista work[], statistiche, stampe), ~27000 tick = ~4.5 s in tutto.
# Qui ~30: niente liste nel giro normale, percorso con due for, caso comune "can_harvest() vero"
# controllato per primo (2 tick).

RICE = Entities.Rice
CLAY = Grounds.Clay
WATER = Items.Water
RI = Items.Rice
GOAL = 100000
H_SKIP = 6       # durezza oltre la quale non si scava (ci pensa il trascinamento dei vicini)
S_LOW = 0.15     # alla semina: sotto questo livello la cella si riempie a 1.0
S = get_world_size()
HALF = S // 2
STEPS = S - 1


def water_full():
	n = (1.0 - get_water()) * 4 // 1
	t = num_items(WATER) // 1
	if n > t:
		n = t
	if n >= 1:
		use_item(WATER, n)


def a2():
	# scendi all'argilla e pianta
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	if plant(RICE):
		if get_water() < S_LOW:
			water_full()
	return False


def bb():
	# raccogli il 1o blocco, togli la terrazza secca, pianta sul 2o
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	else:
		plant(RICE)
		return False
	if num_items(RI) >= GOAL:
		return True
	dig()
	if plant(RICE):
		if get_water() < S_LOW:
			water_full()
	return False


def aa():
	# raccogli il 2o blocco
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	else:
		return False
	return num_items(RI) >= GOAL


def sweep(f):
	# serpentina su tutto il campo: colonne pari verso Nord, dispari verso Sud; l'ultima East fa
	# il giro (wrap) e riporta a (0, 0). Restituisce True appena f() dice che l'obiettivo e' raggiunto.
	for _ in range(HALF):
		for _ in range(STEPS):
			if f():
				return True
			move(North)
		if f():
			return True
		move(East)
		for _ in range(STEPS):
			if f():
				return True
			move(South)
		if f():
			return True
		move(East)
	return False


def path_dirs():
	dirs = []
	for _ in range(HALF):
		for _ in range(STEPS):
			dirs.append(North)
		dirs.append(East)
		for _ in range(STEPS):
			dirs.append(South)
		dirs.append(East)
	return dirs


def back(d):
	if d == North:
		return South
	if d == South:
		return North
	if d == East:
		return West
	return East


def final_round(lim):
	# ultimo strato: scendi e pianta le prime lim celle, poi torna indietro raccogliendo
	dirs = path_dirs()
	for k in range(lim):
		while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
			dig()
		plant(RICE)
		water_full()
		move(dirs[k])
	for kk in range(lim):
		move(back(dirs[lim - 1 - kk]))
		if aa():
			return True
	return False


while True:
	need = (GOAL - num_items(RI)) / 128
	lim = need // 1
	if lim < need:
		lim += 1
	if lim + 2 < S * S:
		if final_round(lim + 2):
			clear()
			break
	quick_print("strato a", get_time(), "riso", num_items(RI), "acqua", num_items(WATER))
	sweep(a2)
	if sweep(bb):
		clear()
		break
	if sweep(aa):
		clear()
		break
