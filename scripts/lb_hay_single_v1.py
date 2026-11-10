# Classifica Hay_Single: 100.000.000 di fieno, 1 drone, campo 8x8. v1 dell'8 nov 2026.
# Generato da rng_predictor/haysingle/gen.py (percorso da route.py, regime tarato con regime_sim.py).
# Schema: due erbe adiacenti A = (0, 0) e C = (1, 0) e 30 cespugli su tutte le altre celle dei due
# rombi di raggio 3: il companion e' valido con prob. 1/3 x 23/24, ogni raccolto valido vale 81.920,
# ne servono circa 1.221. Il drone alterna A e C: harvest, reroll finche' il companion e' valido, mossa.
# - Semina: 35 mosse e 30 piante in un giro unico; su ogni cella attraversata l'erba iniziale e' matura:
#   se il suo companion punta a un cespuglio gia' piantato la raccoglie (circa 3,6 raccolti gratuiti).
# - Acqua: un drone solo ha tutto il serbatoio, quindi le erbe stanno vicine a 1 (crescita in circa
#   0,1 s): ogni 8 cicli, se l'acqua e' sotto WT, 4 unita' in una sola azione.
# - can_harvest solo quando serve: se l'altra cella ha trovato il companion al primo raccolto
#   (fast), il tempo dall'ultimo raccolto qui e' di sole 3 azioni e l'erba potrebbe non essere pronta;
#   altrimenti sono almeno 4 azioni e con acqua >= 0.75 e' sempre pronta.
# - Fine: controllo del fieno a ogni raccolto solo negli ultimi 3 milioni, poi return.
# Stima del simulatore: circa 2:53 (173,5 s). Non ancora provato in gioco.
GOAL = 100000000
NEAR = GOAL - 3000000
WT = 0.9

BUSH = Entities.Bush
HAY = Items.Hay
WATER = Items.Water


def semina():
	move(West)
	plant(BUSH)
	move(West)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(7, 0): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(6, 0): True, (7, 0): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(6, 7): True, (6, 0): True, (7, 0): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(6, 7): True, (7, 7): True, (6, 0): True, (7, 0): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(7, 6): True, (6, 7): True, (7, 7): True, (7, 0): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(North)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(7, 6): True, (0, 6): True, (6, 7): True, (7, 7): True, (6, 0): True, (7, 0): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(7, 6): True, (0, 6): True, (6, 7): True, (7, 7): True, (0, 7): True, (7, 0): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(7, 6): True, (0, 6): True, (7, 7): True, (0, 7): True, (1, 7): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(7, 6): True, (0, 6): True, (1, 6): True, (0, 7): True, (1, 7): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(West)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(1, 5): True, (7, 6): True, (0, 6): True, (1, 6): True, (7, 7): True, (0, 7): True, (1, 7): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(0, 5): True, (1, 5): True, (7, 6): True, (0, 6): True, (1, 6): True, (0, 7): True}:
			if can_harvest():
				harvest()
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(0, 5): True, (1, 5): True, (0, 6): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(0, 3): True, (0, 5): True, (1, 5): True, (1, 6): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(1, 7): True, (0, 3): True, (1, 3): True, (1, 5): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(1, 2): True, (0, 3): True, (1, 3): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(1, 7): True, (1, 2): True, (2, 2): True, (1, 3): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(2, 1): True, (1, 2): True, (2, 2): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(1, 7): True, (6, 0): True, (2, 1): True, (3, 1): True, (2, 2): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(West)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(1, 6): True, (0, 7): True, (1, 7): True, (7, 0): True, (3, 0): True, (2, 1): True, (3, 1): True, (1, 2): True, (2, 2): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(1, 5): True, (0, 6): True, (1, 6): True, (7, 7): True, (0, 7): True, (1, 7): True, (2, 0): True, (3, 0): True, (2, 1): True, (3, 1): True, (2, 2): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(0, 5): True, (1, 5): True, (7, 6): True, (0, 6): True, (1, 6): True, (0, 7): True, (1, 7): True, (2, 7): True, (2, 0): True, (3, 0): True, (2, 1): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(1, 5): True, (0, 6): True, (1, 6): True, (2, 6): True, (1, 7): True, (2, 7): True, (2, 0): True, (3, 0): True, (3, 1): True}:
			if can_harvest():
				harvest()
	move(North)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(1, 6): True, (2, 6): True, (0, 7): True, (1, 7): True, (2, 7): True, (6, 7): True, (2, 0): True, (3, 0): True, (2, 1): True, (3, 1): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(2, 6): True, (1, 7): True, (2, 7): True, (3, 7): True, (6, 7): True, (7, 7): True, (2, 0): True, (3, 0): True, (6, 0): True, (3, 1): True}:
			if can_harvest():
				harvest()
	move(North)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(2, 7): True, (3, 7): True, (6, 7): True, (2, 0): True, (3, 0): True, (6, 0): True, (7, 0): True, (2, 1): True, (3, 1): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(3, 7): True, (6, 7): True, (7, 7): True, (2, 0): True, (3, 0): True, (4, 0): True, (6, 0): True, (7, 0): True, (3, 1): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(North)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(6, 7): True, (3, 0): True, (4, 0): True, (5, 0): True, (6, 0): True, (7, 0): True, (2, 1): True, (3, 1): True}:
			if can_harvest():
				harvest()
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(6, 7): True, (7, 7): True, (4, 0): True, (5, 0): True, (6, 0): True, (7, 0): True, (3, 1): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(7, 6): True, (6, 7): True, (7, 7): True, (0, 7): True, (5, 0): True, (6, 0): True, (7, 0): True, (6, 1): True, (2, 1): True, (1, 2): True, (0, 3): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(North)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(7, 7): True, (6, 0): True, (7, 0): True, (6, 1): True, (7, 1): True, (1, 2): True, (2, 2): True, (0, 3): True, (1, 3): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(0, 7): True, (7, 0): True, (6, 1): True, (7, 1): True, (2, 1): True, (7, 2): True, (1, 2): True, (2, 2): True, (0, 3): True, (1, 3): True, (0, 5): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(0, 6): True, (7, 7): True, (0, 7): True, (1, 7): True, (6, 0): True, (7, 0): True, (2, 0): True, (6, 1): True, (7, 1): True, (2, 1): True, (3, 1): True, (7, 2): True, (0, 2): True, (1, 2): True, (2, 2): True, (0, 3): True, (1, 3): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(East)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(1, 6): True, (0, 7): True, (1, 7): True, (2, 7): True, (7, 0): True, (2, 0): True, (3, 0): True, (6, 1): True, (7, 1): True, (0, 1): True, (2, 1): True, (3, 1): True, (7, 2): True, (0, 2): True, (1, 2): True, (2, 2): True, (0, 3): True, (1, 3): True}:
			if can_harvest():
				harvest()
	plant(BUSH)
	move(South)
	c = get_companion()
	if c[0] == BUSH:
		if c[1] in {(1, 5): True, (0, 6): True, (1, 6): True, (2, 6): True, (7, 7): True, (0, 7): True, (1, 7): True, (2, 7): True, (3, 7): True, (6, 0): True, (7, 0): True, (2, 0): True, (3, 0): True, (4, 0): True, (7, 1): True, (0, 1): True, (1, 1): True, (2, 1): True, (3, 1): True, (0, 2): True, (1, 2): True, (2, 2): True, (1, 3): True}:
			if can_harvest():
				harvest()


def farm():
	ok0 = {(BUSH, (1, 5)): True, (BUSH, (0, 6)): True, (BUSH, (1, 6)): True, (BUSH, (2, 6)): True, (BUSH, (7, 7)): True, (BUSH, (0, 7)): True, (BUSH, (1, 7)): True, (BUSH, (2, 7)): True, (BUSH, (3, 7)): True, (BUSH, (6, 0)): True, (BUSH, (7, 0)): True, (BUSH, (2, 0)): True, (BUSH, (3, 0)): True, (BUSH, (4, 0)): True, (BUSH, (7, 1)): True, (BUSH, (0, 1)): True, (BUSH, (1, 1)): True, (BUSH, (2, 1)): True, (BUSH, (3, 1)): True, (BUSH, (0, 2)): True, (BUSH, (1, 2)): True, (BUSH, (2, 2)): True, (BUSH, (1, 3)): True}
	ok1 = {(BUSH, (0, 5)): True, (BUSH, (7, 6)): True, (BUSH, (0, 6)): True, (BUSH, (1, 6)): True, (BUSH, (6, 7)): True, (BUSH, (7, 7)): True, (BUSH, (0, 7)): True, (BUSH, (1, 7)): True, (BUSH, (2, 7)): True, (BUSH, (5, 0)): True, (BUSH, (6, 0)): True, (BUSH, (7, 0)): True, (BUSH, (2, 0)): True, (BUSH, (3, 0)): True, (BUSH, (6, 1)): True, (BUSH, (7, 1)): True, (BUSH, (0, 1)): True, (BUSH, (1, 1)): True, (BUSH, (2, 1)): True, (BUSH, (7, 2)): True, (BUSH, (0, 2)): True, (BUSH, (1, 2)): True, (BUSH, (0, 3)): True}
	fast = False
	use_item(WATER, 4)
	while not can_harvest():
		pass
	harvest()
	if get_companion() in ok0:
		fast = True
	else:
		fast = False
		harvest()
		while get_companion() not in ok0:
			harvest()
	move(West)
	use_item(WATER, 4)
	while not can_harvest():
		pass
	harvest()
	if get_companion() in ok1:
		fast = True
	else:
		fast = False
		harvest()
		while get_companion() not in ok1:
			harvest()
	move(East)
	while num_items(HAY) < NEAR:
		if fast:
			while not can_harvest():
				pass
		harvest()
		if get_water() < WT:
			use_item(WATER, 4)
		if get_companion() in ok0:
			fast = True
		else:
			fast = False
			harvest()
			while get_companion() not in ok0:
				harvest()
		move(West)
		if fast:
			while not can_harvest():
				pass
		harvest()
		if get_water() < WT:
			use_item(WATER, 4)
		if get_companion() in ok1:
			fast = True
		else:
			fast = False
			harvest()
			while get_companion() not in ok1:
				harvest()
		move(East)
		if fast:
			while not can_harvest():
				pass
		harvest()
		if get_companion() in ok0:
			fast = True
		else:
			fast = False
			harvest()
			while get_companion() not in ok0:
				harvest()
		move(West)
		if fast:
			while not can_harvest():
				pass
		harvest()
		if get_companion() in ok1:
			fast = True
		else:
			fast = False
			harvest()
			while get_companion() not in ok1:
				harvest()
		move(East)
		if fast:
			while not can_harvest():
				pass
		harvest()
		if get_companion() in ok0:
			fast = True
		else:
			fast = False
			harvest()
			while get_companion() not in ok0:
				harvest()
		move(West)
		if fast:
			while not can_harvest():
				pass
		harvest()
		if get_companion() in ok1:
			fast = True
		else:
			fast = False
			harvest()
			while get_companion() not in ok1:
				harvest()
		move(East)
		if fast:
			while not can_harvest():
				pass
		harvest()
		if get_companion() in ok0:
			fast = True
		else:
			fast = False
			harvest()
			while get_companion() not in ok0:
				harvest()
		move(West)
		if fast:
			while not can_harvest():
				pass
		harvest()
		if get_companion() in ok1:
			fast = True
		else:
			fast = False
			harvest()
			while get_companion() not in ok1:
				harvest()
		move(East)
		if fast:
			while not can_harvest():
				pass
		harvest()
		if get_companion() in ok0:
			fast = True
		else:
			fast = False
			harvest()
			while get_companion() not in ok0:
				harvest()
		move(West)
		if fast:
			while not can_harvest():
				pass
		harvest()
		if get_companion() in ok1:
			fast = True
		else:
			fast = False
			harvest()
			while get_companion() not in ok1:
				harvest()
		move(East)
		if fast:
			while not can_harvest():
				pass
		harvest()
		if get_companion() in ok0:
			fast = True
		else:
			fast = False
			harvest()
			while get_companion() not in ok0:
				harvest()
		move(West)
		if fast:
			while not can_harvest():
				pass
		harvest()
		if get_companion() in ok1:
			fast = True
		else:
			fast = False
			harvest()
			while get_companion() not in ok1:
				harvest()
		move(East)
		if fast:
			while not can_harvest():
				pass
		harvest()
		if get_companion() in ok0:
			fast = True
		else:
			fast = False
			harvest()
			while get_companion() not in ok0:
				harvest()
		move(West)
		if fast:
			while not can_harvest():
				pass
		harvest()
		if get_companion() in ok1:
			fast = True
		else:
			fast = False
			harvest()
			while get_companion() not in ok1:
				harvest()
		move(East)
		if fast:
			while not can_harvest():
				pass
		harvest()
		if get_companion() in ok0:
			fast = True
		else:
			fast = False
			harvest()
			while get_companion() not in ok0:
				harvest()
		move(West)
		if fast:
			while not can_harvest():
				pass
		harvest()
		if get_companion() in ok1:
			fast = True
		else:
			fast = False
			harvest()
			while get_companion() not in ok1:
				harvest()
		move(East)
	while True:
		if fast:
			while not can_harvest():
				pass
		harvest()
		if num_items(HAY) >= GOAL:
			return
		if get_companion() in ok0:
			fast = True
		else:
			fast = False
			harvest()
			while get_companion() not in ok0:
				harvest()
		move(West)
		if fast:
			while not can_harvest():
				pass
		harvest()
		if num_items(HAY) >= GOAL:
			return
		if get_companion() in ok1:
			fast = True
		else:
			fast = False
			harvest()
			while get_companion() not in ok1:
				harvest()
		move(East)


semina()
farm()
