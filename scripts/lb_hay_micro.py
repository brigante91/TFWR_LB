# Classifica Hay: 2e9 fieno, 32 droni. Micro-ottimizzato sui costi letti dall'IL.
# Simulatore: circa -0.26 s rispetto alla versione con serpentina verticale e dizionari.
#  - a regime niente can_harvest(): l'erba e' sempre matura se l'acqua resta >= 0.70
#    (tra due raccolti della stessa cella passano almeno 804 tick, crescita 3037/(1+4w))
#  - acqua a regime: ogni 8 cicli, se sotto WR, use_item(WATER, 2) = +0.5 in una sola azione
#    (if e non while: a regime l'acqua e' sempre >= 0.70, quindi un'azione basta)
#  - i dizionari dei companion si costruiscono durante la prima attesa di crescita
#  - erba sulla seconda riga del blocco: tutte le serpentine in 30 mosse
#  - il drone principale controlla l'obiettivo solo vicino alla fine, poi chiude con clear()
GOAL = 2000000000
NEAR = GOAL - 50000000
W = 0.68       # soglia acqua nella fase iniziale (solo durante le attese)
W0 = 0.4      # soglia piu' bassa nei primi cicli: il serbatoio parte vuoto
EARLY = 8     # cicli iniziali con W0 (simulatore: 8-10 meglio di 7 di circa 0.02 s)
WR = 0.70     # soglia acqua a regime (controllata ogni 8 cicli)
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


def goto(tx, ty):
	# chiamata una sola volta, partendo da (0, 0): niente letture della posizione
	if tx <= 16:
		for _ in range(tx):
			move(East)
	else:
		for _ in range(S - tx):
			move(West)
	if ty <= 16:
		for _ in range(ty):
			move(North)
	else:
		for _ in range(S - ty):
			move(South)


def ok_dict(x, y, px, py):
	other = (px, py)
	d = {}
	for o in OFFS:
		p = ((x + o[0]) % S, (y + o[1]) % S)
		if p != other:
			d[(BUSH, p)] = True
	return d


def work_block(b):
	# erba sulla seconda riga del blocco (by + 1): entrambe le serpentine in 30 mosse
	i = b % 8
	bx = 4 * i
	by = 8 * (b // 8) + 4 * (i % 2)
	gy = by + 1
	if i < 4:
		ex = bx
		d1 = East
		d2 = West
		ax = bx + 2
		cx = bx + 1
	else:
		ex = bx + 3
		d1 = West
		d2 = East
		ax = bx + 1
		cx = bx + 2

	if by <= 12:
		goto(ex, by)
		plant(BUSH)
		move(d1)
		plant(BUSH)
		move(d1)
		plant(BUSH)
		move(d1)
		plant(BUSH)
		move(North)
		plant(BUSH)
		move(North)
		plant(BUSH)
		move(North)
		plant(BUSH)
		move(North)
		plant(BUSH)
		move(North)
		plant(BUSH)
		move(North)
		plant(BUSH)
		move(North)
		plant(BUSH)
		move(d2)
		plant(BUSH)
		move(South)
		plant(BUSH)
		move(South)
		plant(BUSH)
		move(South)
		plant(BUSH)
		move(South)
		plant(BUSH)
		move(South)
		plant(BUSH)
		move(d2)
		plant(BUSH)
		move(North)
		plant(BUSH)
		move(North)
		plant(BUSH)
		move(North)
		plant(BUSH)
		move(North)
		plant(BUSH)
		move(North)
		plant(BUSH)
		move(d2)
		plant(BUSH)
		move(South)
		plant(BUSH)
		move(South)
		plant(BUSH)
		move(South)
		plant(BUSH)
		move(South)
		plant(BUSH)
		move(South)
		plant(BUSH)
		move(South)
		plant(BUSH)
		move(d1)
		return cx, ax, gy, d2, d1
	else:
		goto(ex, (by + 7) % S)
		plant(BUSH)
		move(d1)
		plant(BUSH)
		move(d1)
		plant(BUSH)
		move(d1)
		plant(BUSH)
		move(South)
		plant(BUSH)
		move(d2)
		plant(BUSH)
		move(d2)
		plant(BUSH)
		move(d2)
		plant(BUSH)
		move(South)
		plant(BUSH)
		move(d1)
		plant(BUSH)
		move(d1)
		plant(BUSH)
		move(d1)
		plant(BUSH)
		move(South)
		plant(BUSH)
		move(d2)
		plant(BUSH)
		move(d2)
		plant(BUSH)
		move(d2)
		plant(BUSH)
		move(South)
		plant(BUSH)
		move(d1)
		plant(BUSH)
		move(d1)
		plant(BUSH)
		move(d1)
		plant(BUSH)
		move(South)
		plant(BUSH)
		move(d2)
		plant(BUSH)
		move(d2)
		plant(BUSH)
		move(d2)
		plant(BUSH)
		move(South)
		plant(BUSH)
		move(South)
		plant(BUSH)
		move(d1)
		plant(BUSH)
		move(d1)
		plant(BUSH)
		move(d1)
		plant(BUSH)
		move(North)
		plant(BUSH)
		move(d2)
		return ax, cx, gy, d1, d2


def start(ax, cx, by, d1, d2):
	# primo ciclo senza dizionari: l'erba iniziale e' gia' matura
	A = (ax, by)
	C = (cx, by)
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
	use_item(WATER)   # C parte a secco: +0.25 subito (simulatore: circa -0.03 s)
	move(d1)
	# di nuovo su A, erba appena ripiantata: acqua (sicuramente a 0), poi i dizionari mentre cresce
	use_item(WATER)
	okA = ok_dict(ax, by, cx, by)
	okC = ok_dict(cx, by, ax, by)
	return okA, okC


def warmup(okA, okC, d1, d2):
	for _ in range(EARLY - 1):
		while not can_harvest():
			if get_water() < W0:
				use_item(WATER)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		while not can_harvest():
			if get_water() < W0:
				use_item(WATER)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
	while num_items(WATER) <= THR:
		while not can_harvest():
			if get_water() < W:
				use_item(WATER)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		while not can_harvest():
			if get_water() < W:
				use_item(WATER)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
	# primo ciclo a regime: acqua fino a WR e un'ultima attesa di sicurezza
	if get_water() < WR:
		use_item(WATER, 2)
	while not can_harvest():
		pass
	harvest()
	while get_companion() not in okA:
		harvest()
	move(d2)
	if get_water() < WR:
		use_item(WATER, 2)
	while not can_harvest():
		pass
	harvest()
	while get_companion() not in okC:
		harvest()
	move(d1)


def farm(okA, okC, d1, d2):
	while True:
		if get_water() < WR:
			use_item(WATER, 2)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		if get_water() < WR:
			use_item(WATER, 2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)


def farm_main(okA, okC, d1, d2):
	while num_items(HAY) < NEAR:
		if get_water() < WR:
			use_item(WATER, 2)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		if get_water() < WR:
			use_item(WATER, 2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
	while True:
		harvest()
		if num_items(HAY) >= GOAL:
			return
		while get_companion() not in okA:
			harvest()
			if num_items(HAY) >= GOAL:
				return
		move(d2)
		if num_items(HAY) >= GOAL:
			return
		harvest()
		if num_items(HAY) >= GOAL:
			return
		while get_companion() not in okC:
			harvest()
			if num_items(HAY) >= GOAL:
				return
		move(d1)
		if num_items(HAY) >= GOAL:
			return


def run_range(lo, hi):
	while hi - lo > 1:
		mid = (lo + hi) // 2
		spawn_drone(run_range, mid, hi)
		hi = mid
	ax, cx, by, d1, d2 = work_block(lo)
	okA, okC = start(ax, cx, by, d1, d2)
	warmup(okA, okC, d1, d2)
	if lo == 0:
		farm_main(okA, okC, d1, d2)
		clear()
	else:
		farm(okA, okC, d1, d2)


run_range(0, BLOCKS)