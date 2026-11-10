# Classifica Carrots: 2e9 carote, 32 droni. v3 del 6 nov 2026 (v2 in gioco: 4:49, poi ~4:20 con acqua a 1.0).
# Classifica Steam: #1 3:10, #10 3:46, #25 4:08.
# v3: invece di rerollare sempre, quando il companion chiesto e' (bush|tree, p) con p cella libera
# a distanza <= 2, il drone va a piantare quel tipo in p e torna (600-1000 tick) invece di
# rerollare (403 tick per tentativo, ~1300 attesi). Le celle convertite restano: le estrazioni
# future con quel tipo in p sono accettate, quelle con grass in p no (la probabilita' totale non
# cambia). Non si converte una cella da cui dipende un'altra carota del drone. Stima -10..-15 s.
#
# Regole (Growable.cs): companion estratto al plant: tipo uniforme fra {grass, bush, tree}
# (mai carota), posizione uniforme fra le 24 celle del rombo di raggio 3. La resa x160 arriva
# se al raccolto quella cella contiene un'entita' di quel tipo. L'erba cresce da sola sul
# grassland: lasciando tutto a prato le celle non-carota sono gratis e sempre valide.
# Probabilita' di accettazione = (celle del rombo che non sono carote)/24/3: il reroll
# (harvest + plant = 403 tick) costa in media 403*(1/acc - 1).
# Layout (valutato con haysim/layout_eval.py): 32 blocchi 2x3 a passo 5, un drone per blocco
# che gira sul perimetro (1 mossa per raccolto): ~1820 tick/raccolto contro ~2000 degli
# anelli su coppie di righe e ~4400 del vecchio schema a 2 celle (limitato dalla crescita).
# Crescita carota 6 s +-20% / (1 + 4*acqua): con acqua 1.0 ~1.2 s = 7290 tick, un giro di
# 6 celle dura ~11000 tick: nessuna attesa.
GOAL = 2000000000
S = get_world_size()
CARROT = Entities.Carrot
GRASS = Entities.Grass
SOIL = Grounds.Soil
WATER = Items.Water
PITCH = 5
OFFS = [
	(0, 1), (0, 2), (0, 3), (0, -1), (0, -2), (0, -3),
	(1, 0), (2, 0), (3, 0), (-1, 0), (-2, 0), (-3, 0),
	(1, 1), (1, 2), (2, 1), (1, -1), (1, -2), (2, -1),
	(-1, 1), (-1, 2), (-2, 1), (-1, -1), (-1, -2), (-2, -1)
]
# perimetro del blocco 2x3 partendo dall'angolo in basso a sinistra
STEPS = [North, North, East, South, South, West]
CELLS = [(0, 0), (0, 1), (0, 2), (1, 2), (1, 1), (1, 0)]


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


def is_carrot(px, py):
	# blocchi 2x3 con origine (5i, 5j), i = 0..5, j = 0..4, piu' j = 5 solo per i = 0, 1
	if px >= 30 or py >= 28 or px % PITCH >= 2 or py % PITCH >= 3:
		return False
	if py >= 25 and px >= 10:
		return False
	return True


def ok_dict(x, y):
	d = {}
	for o in OFFS:
		px = (x + o[0]) % S
		py = (y + o[1]) % S
		if not is_carrot(px, py):
			d[(GRASS, (px, py))] = True
	return d


def water():
	# serbatoio abbondante (25.6/s per 192 celle): tenere tutto a ~1.0, crescita 1.2 s < giro 1.8 s
	w = get_water()
	if w < 0.5:
		if not use_item(WATER, 4):
			use_item(WATER, 2)
	elif w < 0.8:
		use_item(WATER, 2)


def dist(a, b):
	dx = abs(a[0] - b[0])
	dy = abs(a[1] - b[1])
	if dx > S // 2:
		dx = S - dx
	if dy > S // 2:
		dy = S - dy
	return dx + dy


def go(dx, dy):
	# spostamento relativo con wrap (dx, dy in -2..2)
	if dx > 0:
		for _ in range(dx):
			move(East)
	elif dx < 0:
		for _ in range(-dx):
			move(West)
	if dy > 0:
		for _ in range(dy):
			move(North)
	elif dy < 0:
		for _ in range(-dy):
			move(South)


def settle(cell, cont, need, j):
	# dopo plant(CARROT) sulla cella j: accetta, converte o rerolla finche' il companion e' valido.
	# ritorna il numero di reroll fatti
	nr = 0
	while True:
		c = get_companion()
		t = c[0]
		p = c[1]
		if not is_carrot(p[0], p[1]):
			if p in cont:
				cur = cont[p]
			else:
				cur = GRASS
			if cur == t:
				need[j] = c
				return nr
			if t != GRASS:
				# conversione possibile se vicina e nessun'altra carota del drone dipende da p
				dx = p[0] - cell[0]
				dy = p[1] - cell[1]
				if dx > S // 2:
					dx -= S
				elif dx < -S // 2:
					dx += S
				if dy > S // 2:
					dy -= S
				elif dy < -S // 2:
					dy += S
				if abs(dx) + abs(dy) <= 2:
					free = True
					for i in range(6):
						if i != j and need[i] != None and need[i][1] == p:
							free = False
					if free:
						go(dx, dy)
						if cur != GRASS:
							harvest()
						plant(t)
						cont[p] = t
						go(-dx, -dy)
						need[j] = c
						return nr
		harvest()
		plant(CARROT)
		nr += 1


def work(b, main):
	bx = PITCH * (b % 6)
	by = PITCH * (b // 6)
	cells = []
	for c in CELLS:
		cells.append(((bx + c[0]) % S, (by + c[1]) % S))
	cont = {}
	need = [None, None, None, None, None, None]
	goto(bx, by)
	for j in range(6):
		if get_ground_type() != SOIL:
			till()
		plant(CARROT)
		settle(cells[j], cont, need, j)
		water()
		move(STEPS[j])
	nh = 0
	nr = 0
	nw = 0
	while True:
		for j in range(6):
			if not can_harvest():
				nw += 1
				while not can_harvest():
					pass
			harvest()
			plant(CARROT)
			nr += settle(cells[j], cont, need, j)
			water()
			move(STEPS[j])
			if main:
				nh += 1
				if nh % 32 == 0:
					quick_print("t", get_time(), "raccolti", nh, "reroll", nr, "attese", nw, "convertite", len(cont), "carote", num_items(Items.Carrot))
				if num_items(Items.Carrot) >= GOAL:
					clear()
					return


def spawn_range(lo, hi):
	while hi - lo > 1:
		mid = (lo + hi) // 2
		spawn_drone(spawn_range_task(mid, hi))
		hi = mid
	work(lo, False)


def spawn_range_task(lo, hi):
	def fn():
		spawn_range(lo, hi)
	return fn


clear()
spawn_drone(spawn_range_task(1, 32))
work(0, True)
