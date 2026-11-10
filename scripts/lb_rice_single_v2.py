# Classifica Rice_Single (1e5 riso, 1 drone, 8x8). v2 dell'8 nov 2026: versione snella di lb_rice.py v7.
# lb_rice.py v7 in gioco: 2:29.1. #1 2:19.294.
#
# Stesso schema (vedi lb_rice.py): per strato tre passate a serpentina sulle 64 celle
#   A2: scendi all'argilla e pianta;  B: raccogli, scava la terrazza secca, pianta sul 2o blocco;
#   A1: raccogli il 2o blocco (la terrazza secca la toglie il crollo nella A2 dopo).
# Acqua: alla semina, se la cella e' sotto S_LOW, la si riempie a 1.0 (circa una volta per cella).
# Ultimo strato: si piantano solo le colonne che servono e si raccolgono ad anello (vedi v2 sotto).
#
# Differenza: l'interprete conta anche le istruzioni (if 1, chiamata 1, confronto 1, indice 1,
# for 1 a giro; decompilato, FINDINGS_cactus_dino_maze.md). La v7 spendeva ~70 tick di
# interprete per cella a strato (lista work[], statistiche, stampe), ~27000 tick = ~4.5 s in tutto.
# Qui ~30: niente liste nel giro normale, percorso con due for, caso comune "can_harvest() vero"
# controllato per primo (2 tick).
# v1 (lb_rice_single_v1.py) in gioco 2:27 (2:27.208 in classifica, #4; #1 2:19.294).
# v2: ultimo strato ad anello. La v1 piantava need+2 celle e tornava indietro raccogliendo dalla
# ultima piantata, che doveva ancora crescere (~1.2 s d'attesa). Ora pianta colonne intere
# (need+1 celle arrotondate alla colonna), torna a (0, 0) e raccoglie nello stesso ordine della
# semina: la prima raccolta e' la prima piantata, gia' cresciuta. Sim (haysim/rice/single.py):
# il percorso a orientamento ottimo per strato varrebbe al massimo -2.2 s con un oracolo, non usato.

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
	use_item(WATER, 4)


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


def goto0():
	x = get_pos_x()
	y = get_pos_y()
	if x <= HALF:
		for _ in range(x):
			move(West)
	else:
		for _ in range(S - x):
			move(East)
	if y <= HALF:
		for _ in range(y):
			move(South)
	else:
		for _ in range(S - y):
			move(North)


def plant_full():
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	if plant(RICE):
		water_full()
	return False


def final_round(cols):
	# ultimo strato: scendi e pianta le prime cols colonne, torna a (0, 0) e raccogli nello stesso ordine
	for c in range(cols):
		for _ in range(STEPS):
			plant_full()
			if c % 2 == 0:
				move(North)
			else:
				move(South)
		plant_full()
		move(East)
	goto0()
	for c in range(cols):
		for _ in range(STEPS):
			if aa():
				return True
			if c % 2 == 0:
				move(North)
			else:
				move(South)
		if aa():
			return True
		move(East)
	return False


while True:
	need = (GOAL - num_items(RI)) / 128
	cols = (need + 1) / S
	c = cols // 1
	if c < cols:
		c += 1
	if c < S:
		if final_round(c):
			clear()
			break
		goto0()
	quick_print("strato a", get_time(), "riso", num_items(RI), "acqua", num_items(WATER))
	sweep(a2)
	if sweep(bb):
		clear()
		break
	if sweep(aa):
		clear()
		break
