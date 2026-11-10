# Classifica Wood: 1e10 legno, 32 droni.
# Simulatore: scacchiera a colonne ~403 s -> questo schema ~287 s.
# Perche':
#  - un reroll di un albero costa harvest+plant = 400 tick (l'albero non si ripianta sopra)
#  - nella scacchiera 8 delle 24 celle del rombo sono alberi: companion valido 2/9
#  - qui alberi ogni 2 celle su 12 righe distanziate 3,3,2 e sfalsate di 1:
#    companion valido ~0.29, nessun albero adiacente (crescita non raddoppiata)
#  - ogni drone gira su un anello di 6 alberi tra due righe: il giro dura piu'
#    della crescita, quindi quasi niente attese
#  - fine con clear() dal drone principale appena il legno arriva all'obiettivo
GOAL = 10000000000
W = 0.9

S = get_world_size()
TREE = Entities.Tree
GRASS = Entities.Grass
WOOD = Items.Wood
WATER = Items.Water
ROWS = [0, 3, 6, 8, 11, 14, 16, 19, 22, 24, 27, 30]


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


ROWK = {}
for k in range(12):
	ROWK[ROWS[k]] = k % 2
DIAMOND = [(0, 1), (0, 2), (0, 3), (0, -1), (0, -2), (0, -3),
	(1, 0), (2, 0), (3, 0), (-1, 0), (-2, 0), (-3, 0),
	(1, 1), (1, 2), (2, 1), (1, -1), (1, -2), (2, -1),
	(-1, 1), (-1, 2), (-2, 1), (-1, -1), (-1, -2), (-2, -1)]


def ok_dict(x, y):
	# companion validi: erba in una cella del rombo di raggio 3 che non e' un albero
	d = {}
	for o in DIAMOND:
		px = (x + o[0]) % S
		py = (y + o[1]) % S
		if py in ROWK and px % 2 == ROWK[py]:
			continue
		d[(GRASS, (px, py))] = True
	return d


def tour_of(i):
	if i < 30:
		pi = i // 5
		x0 = 6 * (i % 5)
		ya = ROWS[2 * pi]
		yb = ROWS[2 * pi + 1]
		return [(x0, ya), (x0 + 2, ya), (x0 + 4, ya), (x0 + 5, yb), (x0 + 3, yb), (x0 + 1, yb)]
	t = []
	for k in range(6 * (i - 30), 6 * (i - 30) + 6):
		t.append((30 + k % 2, ROWS[k]))
	return t


def work(i):
	tour = tour_of(i)
	oks = []
	for p in tour:
		oks.append(ok_dict(p[0], p[1]))
	n = len(tour)
	main = i == 0
	while True:
		for j in range(n):
			p = tour[j]
			goto(p[0], p[1])
			ok = oks[j]
			if get_entity_type() == TREE:
				while not can_harvest():
					if get_water() < W and num_items(WATER) > 0:
						use_item(WATER)
				harvest()
				if main and num_items(WOOD) >= GOAL:
					return
			plant(TREE)
			while get_companion() not in ok:
				harvest()
				plant(TREE)


def make_task(i):
	def fn():
		work(i)
	return fn


clear()
for i in range(1, 32):
	spawn_drone(make_task(i))
work(0)
clear()
