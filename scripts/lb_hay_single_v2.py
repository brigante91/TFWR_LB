# Classifica Hay_Single: 100.000.000 di fieno, 1 drone, campo 8x8. v2 dell'8 nov 2026.
# Generato da rng_predictor/haysingle/gen.py (VER=2, percorso route2.json da route3.py).
# La v1 ha fatto 2:52.783 in gioco (stima 2:53.5). Modifiche, misurate con regime_sim2.py su
# 80 semi appaiati:
# 1. Niente controllo can_harvest a regime e niente flag fast. Fra due raccolti della stessa erba
#    passano almeno ~810 tick (raccolto, controllo, mossa, almeno un raccolto sull'altra erba, mossa):
#    con acqua >= 0.69 l'erba e' gia' matura (3037.5 / (1 + 4w) tick). Nell'hay a 32 droni i raccolti
#    acerbi comparivano solo sotto 0.71.
# 2. Acqua solo nel ramo "companion valido al primo raccolto": if get_water() < 0.8: 4 unita' (il
#    ramo capita una volta ogni ~3 visite, quindi l'acqua non scende sotto ~0.79).
# 3. Percorso di semina di 34 mosse invece di 35 (erbe in (5, 7) e (6, 7)).
# Simulatore: circa -0.7 s sulla v1 (atteso circa 2:52.1). Verificato con emulate.py: sempre 1.221
# raccolti validi, nessun raccolto acerbo, nessun cespuglio raccolto. Non ancora provato in gioco.
GOAL = 100000000
NEAR = GOAL - 3000000
WT = 0.8

BUSH = Entities.Bush
HAY = Items.Hay
WATER = Items.Water


def semina():
	plant(BUSH)
	move(West)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(0, 0): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(North)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(7, 0): True, (0, 0): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(West)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(7, 0): True, (0, 0): True, (7, 1): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(North)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(7, 0): True, (6, 1): True, (7, 1): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(West)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(6, 1): True, (7, 1): True, (6, 2): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(7, 0): True, (6, 1): True, (7, 1): True, (5, 2): True, (6, 2): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(West)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(5, 1): True, (6, 1): True, (7, 1): True, (5, 2): True, (6, 2): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(7, 0): True, (4, 1): True, (5, 1): True, (6, 1): True, (5, 2): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(West)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(0, 0): True, (4, 0): True, (4, 1): True, (5, 1): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(3, 0): True, (4, 0): True, (4, 1): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(3, 7): True, (3, 0): True, (4, 0): True, (4, 1): True, (5, 1): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(3, 7): True, (4, 7): True, (3, 0): True, (4, 0): True, (4, 1): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(4, 6): True, (3, 7): True, (4, 7): True, (4, 0): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(5, 2): True, (4, 5): True, (4, 6): True, (4, 7): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(5, 1): True, (5, 2): True, (6, 2): True, (4, 5): True, (5, 5): True, (4, 6): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(6, 1): True, (5, 2): True, (6, 2): True, (5, 4): True, (4, 5): True, (5, 5): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(North)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(6, 2): True, (5, 4): True, (6, 4): True, (4, 5): True, (5, 5): True, (4, 6): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(5, 4): True, (6, 4): True, (4, 5): True, (5, 5): True, (6, 5): True, (7, 0): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(North)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(6, 4): True, (5, 5): True, (6, 5): True, (7, 5): True, (4, 6): True, (7, 0): True, (0, 0): True, (7, 1): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(North)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(6, 5): True, (7, 5): True, (7, 6): True, (4, 7): True, (7, 0): True, (0, 0): True, (6, 1): True, (7, 1): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(7, 5): True, (7, 6): True, (7, 7): True, (3, 7): True, (7, 0): True, (0, 0): True, (7, 1): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(6, 5): True, (7, 5): True, (7, 6): True, (7, 7): True, (0, 7): True, (7, 0): True, (0, 0): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(7, 5): True, (7, 6): True, (0, 6): True, (4, 6): True, (7, 7): True, (0, 7): True, (3, 7): True, (0, 0): True}:
			if can_harvest():
				harvest()
	move(North)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(7, 6): True, (0, 6): True, (7, 7): True, (0, 7): True, (3, 7): True, (4, 7): True, (7, 0): True, (0, 0): True, (3, 0): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(0, 6): True, (4, 6): True, (7, 7): True, (0, 7): True, (1, 7): True, (3, 7): True, (4, 7): True, (0, 0): True, (3, 0): True, (4, 0): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(4, 5): True, (7, 6): True, (0, 6): True, (4, 6): True, (0, 7): True, (1, 7): True, (2, 7): True, (3, 7): True, (4, 7): True, (3, 0): True}:
			if can_harvest():
				harvest()
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(4, 5): True, (5, 5): True, (0, 6): True, (4, 6): True, (1, 7): True, (2, 7): True, (3, 7): True, (4, 7): True, (3, 0): True, (4, 0): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(5, 4): True, (6, 4): True, (4, 5): True, (5, 5): True, (6, 5): True, (7, 5): True, (3, 6): True, (4, 6): True, (7, 6): True, (0, 6): True, (3, 7): True, (4, 7): True, (7, 7): True, (4, 0): True, (5, 1): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(5, 4): True, (6, 4): True, (4, 5): True, (5, 5): True, (6, 5): True, (7, 5): True, (3, 6): True, (4, 6): True, (5, 6): True, (7, 6): True, (0, 6): True, (4, 7): True, (7, 7): True, (0, 7): True, (7, 0): True, (6, 1): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(North)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(6, 4): True, (5, 5): True, (6, 5): True, (7, 5): True, (4, 6): True, (5, 6): True, (6, 6): True, (7, 6): True, (0, 6): True, (3, 7): True, (4, 7): True, (7, 7): True, (0, 7): True, (1, 7): True, (4, 0): True, (7, 0): True, (0, 0): True, (5, 1): True, (6, 1): True, (7, 1): True, (6, 2): True}:
			if can_harvest():
				harvest()
	move(North)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(6, 5): True, (5, 6): True, (6, 6): True, (7, 6): True, (4, 7): True, (7, 7): True, (0, 7): True, (3, 0): True, (4, 0): True, (7, 0): True, (0, 0): True, (4, 1): True, (5, 1): True, (6, 1): True, (7, 1): True, (5, 2): True, (6, 2): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(West)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(5, 5): True, (4, 6): True, (5, 6): True, (6, 6): True, (3, 7): True, (4, 7): True, (7, 7): True, (3, 0): True, (4, 0): True, (6, 0): True, (7, 0): True, (0, 0): True, (4, 1): True, (5, 1): True, (6, 1): True, (7, 1): True, (5, 2): True, (6, 2): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(5, 4): True, (4, 5): True, (5, 5): True, (6, 5): True, (3, 6): True, (4, 6): True, (5, 6): True, (6, 6): True, (7, 6): True, (2, 7): True, (3, 7): True, (4, 7): True, (7, 7): True, (0, 7): True, (3, 0): True, (4, 0): True, (5, 0): True, (6, 0): True, (7, 0): True, (4, 1): True, (5, 1): True, (6, 1): True, (5, 2): True}:
			if can_harvest():
				harvest()


def farm():
	ok0 = {(BUSH, (5, 4)): True, (BUSH, (4, 5)): True, (BUSH, (5, 5)): True, (BUSH, (6, 5)): True, (BUSH, (3, 6)): True, (BUSH, (4, 6)): True, (BUSH, (5, 6)): True, (BUSH, (6, 6)): True, (BUSH, (7, 6)): True, (BUSH, (2, 7)): True, (BUSH, (3, 7)): True, (BUSH, (4, 7)): True, (BUSH, (7, 7)): True, (BUSH, (0, 7)): True, (BUSH, (3, 0)): True, (BUSH, (4, 0)): True, (BUSH, (5, 0)): True, (BUSH, (6, 0)): True, (BUSH, (7, 0)): True, (BUSH, (4, 1)): True, (BUSH, (5, 1)): True, (BUSH, (6, 1)): True, (BUSH, (5, 2)): True}
	ok1 = {(BUSH, (6, 4)): True, (BUSH, (5, 5)): True, (BUSH, (6, 5)): True, (BUSH, (7, 5)): True, (BUSH, (4, 6)): True, (BUSH, (5, 6)): True, (BUSH, (6, 6)): True, (BUSH, (7, 6)): True, (BUSH, (0, 6)): True, (BUSH, (3, 7)): True, (BUSH, (4, 7)): True, (BUSH, (7, 7)): True, (BUSH, (0, 7)): True, (BUSH, (1, 7)): True, (BUSH, (4, 0)): True, (BUSH, (5, 0)): True, (BUSH, (6, 0)): True, (BUSH, (7, 0)): True, (BUSH, (0, 0)): True, (BUSH, (5, 1)): True, (BUSH, (6, 1)): True, (BUSH, (7, 1)): True, (BUSH, (6, 2)): True}
	use_item(WATER, 4)
	while not can_harvest():
		pass
	harvest()
	if get_companion() in ok0:
		if get_water() < WT:
			use_item(WATER, 4)
	else:
		harvest()
		while get_companion() not in ok0:
			harvest()
	move(East)
	use_item(WATER, 4)
	while not can_harvest():
		pass
	harvest()
	if get_companion() in ok1:
		if get_water() < WT:
			use_item(WATER, 4)
	else:
		harvest()
		while get_companion() not in ok1:
			harvest()
	move(West)
	while num_items(HAY) < NEAR:
		harvest()
		if get_companion() in ok0:
			if get_water() < WT:
				use_item(WATER, 4)
		else:
			harvest()
			while get_companion() not in ok0:
				harvest()
		move(East)
		harvest()
		if get_companion() in ok1:
			if get_water() < WT:
				use_item(WATER, 4)
		else:
			harvest()
			while get_companion() not in ok1:
				harvest()
		move(West)
		harvest()
		if get_companion() in ok0:
			if get_water() < WT:
				use_item(WATER, 4)
		else:
			harvest()
			while get_companion() not in ok0:
				harvest()
		move(East)
		harvest()
		if get_companion() in ok1:
			if get_water() < WT:
				use_item(WATER, 4)
		else:
			harvest()
			while get_companion() not in ok1:
				harvest()
		move(West)
		harvest()
		if get_companion() in ok0:
			if get_water() < WT:
				use_item(WATER, 4)
		else:
			harvest()
			while get_companion() not in ok0:
				harvest()
		move(East)
		harvest()
		if get_companion() in ok1:
			if get_water() < WT:
				use_item(WATER, 4)
		else:
			harvest()
			while get_companion() not in ok1:
				harvest()
		move(West)
		harvest()
		if get_companion() in ok0:
			if get_water() < WT:
				use_item(WATER, 4)
		else:
			harvest()
			while get_companion() not in ok0:
				harvest()
		move(East)
		harvest()
		if get_companion() in ok1:
			if get_water() < WT:
				use_item(WATER, 4)
		else:
			harvest()
			while get_companion() not in ok1:
				harvest()
		move(West)
		harvest()
		if get_companion() in ok0:
			if get_water() < WT:
				use_item(WATER, 4)
		else:
			harvest()
			while get_companion() not in ok0:
				harvest()
		move(East)
		harvest()
		if get_companion() in ok1:
			if get_water() < WT:
				use_item(WATER, 4)
		else:
			harvest()
			while get_companion() not in ok1:
				harvest()
		move(West)
		harvest()
		if get_companion() in ok0:
			if get_water() < WT:
				use_item(WATER, 4)
		else:
			harvest()
			while get_companion() not in ok0:
				harvest()
		move(East)
		harvest()
		if get_companion() in ok1:
			if get_water() < WT:
				use_item(WATER, 4)
		else:
			harvest()
			while get_companion() not in ok1:
				harvest()
		move(West)
		harvest()
		if get_companion() in ok0:
			if get_water() < WT:
				use_item(WATER, 4)
		else:
			harvest()
			while get_companion() not in ok0:
				harvest()
		move(East)
		harvest()
		if get_companion() in ok1:
			if get_water() < WT:
				use_item(WATER, 4)
		else:
			harvest()
			while get_companion() not in ok1:
				harvest()
		move(West)
		harvest()
		if get_companion() in ok0:
			if get_water() < WT:
				use_item(WATER, 4)
		else:
			harvest()
			while get_companion() not in ok0:
				harvest()
		move(East)
		harvest()
		if get_companion() in ok1:
			if get_water() < WT:
				use_item(WATER, 4)
		else:
			harvest()
			while get_companion() not in ok1:
				harvest()
		move(West)
	while True:
		harvest()
		if num_items(HAY) >= GOAL:
			return
		if get_companion() in ok0:
			if get_water() < WT:
				use_item(WATER, 4)
		else:
			harvest()
			while get_companion() not in ok0:
				harvest()
		move(East)
		harvest()
		if num_items(HAY) >= GOAL:
			return
		if get_companion() in ok1:
			if get_water() < WT:
				use_item(WATER, 4)
		else:
			harvest()
			while get_companion() not in ok1:
				harvest()
		move(West)


semina()
farm()
