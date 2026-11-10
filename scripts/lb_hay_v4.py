# Classifica Hay: 2e9 fieno, 32 droni. Derivato da lb_hay_best (1:50.159).
# Novita':
#  - controllo del companion con un dizionario (tipo, posizione): niente controllo separato della posizione
#  - acqua ridotta nei primi cicli (il serbatoio parte vuoto)
#  - uscita rapida: il principale controlla il fieno dopo ogni azione e chiude con clear(),
#    che elimina subito gli altri droni; i secondari non controllano mai il fieno
#  - i blocchi nella meta' destra entrano dall'angolo destro (viaggio piu' corto)
#  - niente clear() iniziale: il campo parte gia' tutto erba
GOAL = 2000000000
W = 0.68
W0 = 0.4
EARLY = 12

S = get_world_size()
BUSH = Entities.Bush
HAY = Items.Hay
WATER = Items.Water
BLOCKS = 32


def goto(tx, ty):
	dx = (tx - get_pos_x()) % S
	if dx <= S // 2:
		for _ in range(dx):
			move(East)
	else:
		for _ in range(S - dx):
			move(West)
	dy = (ty - get_pos_y()) % S
	if dy <= S // 2:
		for _ in range(dy):
			move(North)
	else:
		for _ in range(S - dy):
			move(South)


def ok_dict(x, y, px, py):
	# companion validi per l'erba in (x, y): un bush in una cella del rombo di raggio 3,
	# esclusa l'altra erba (px, py)
	offs = [(0, 1), (0, 2), (0, 3), (0, -1), (0, -2), (0, -3),
		(1, 0), (2, 0), (3, 0), (-1, 0), (-2, 0), (-3, 0),
		(1, 1), (1, 2), (2, 1), (1, -1), (1, -2), (2, -1),
		(-1, 1), (-1, 2), (-2, 1), (-1, -1), (-1, -2), (-2, -1)]
	other = (px % S, py % S)
	d = {}
	for o in offs:
		p = ((x + o[0]) % S, (y + o[1]) % S)
		if p != other:
			d[(BUSH, p)] = True
	return d


def work_block(b):
	i = b % 8
	bx = 4 * i
	by = (8 * (b // 8) + 4 * (i % 2)) % S
	if i < 4:
		# erba in basso a sinistra, ingresso in alto a sinistra
		ex = bx
		d1 = East
		d2 = West
		ax = bx + 1
		cx = bx
	else:
		# erba in basso a destra, ingresso in alto a destra
		ex = bx + 3
		d1 = West
		d2 = East
		ax = bx + 2
		cx = bx + 3
	goto(ex, (by + 7) % S)
	for k in range(7):
		if k % 2 == 0:
			d = d1
		else:
			d = d2
		for _ in range(3):
			plant(BUSH)
			move(d)
		plant(BUSH)
		move(South)
	plant(BUSH)
	move(d2)
	plant(BUSH)
	move(d2)
	# ora il drone e' sull'erba interna A; l'erba d'angolo C e' verso d2
	okA = ok_dict(ax, by, cx, by)
	okC = ok_dict(cx, by, ax, by)

	return okA, okC, d1, d2


def farm(okA, okC, d1, d2):
	# droni secondari: non controllano mai il fieno, li ferma il clear() del principale
	for _ in range(EARLY):
		while not can_harvest():
			if get_water() < W0 and num_items(WATER) > 0:
				use_item(WATER)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		while not can_harvest():
			if get_water() < W0 and num_items(WATER) > 0:
				use_item(WATER)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
	while True:
		while not can_harvest():
			if get_water() < W and num_items(WATER) > 0:
				use_item(WATER)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		while not can_harvest():
			if get_water() < W and num_items(WATER) > 0:
				use_item(WATER)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)


def farm_main(okA, okC, d1, d2):
	# drone principale: controlla il fieno dopo ogni azione, poi il chiamante fa clear()
	n = 0
	while True:
		if n < EARLY:
			w = W0
		else:
			w = W
		n += 1
		while not can_harvest():
			if get_water() < w and num_items(WATER) > 0:
				use_item(WATER)
		harvest()
		if num_items(HAY) >= GOAL:
			return
		while get_companion() not in okA:
			harvest()
			if num_items(HAY) >= GOAL:
				return
		move(d2)
		while not can_harvest():
			if get_water() < w and num_items(WATER) > 0:
				use_item(WATER)
		harvest()
		if num_items(HAY) >= GOAL:
			return
		while get_companion() not in okC:
			harvest()
			if num_items(HAY) >= GOAL:
				return
		move(d1)


def make_task(lo, hi):
	def fn():
		run_range(lo, hi)
	return fn


def run_range(lo, hi):
	while hi - lo > 1:
		mid = (lo + hi) // 2
		spawn_drone(make_task(mid, hi))
		hi = mid
	okA, okC, d1, d2 = work_block(lo)
	if lo == 0:
		farm_main(okA, okC, d1, d2)
		clear()   # elimina subito tutti gli altri droni: la run finisce qui
	else:
		farm(okA, okC, d1, d2)


run_range(0, BLOCKS)
