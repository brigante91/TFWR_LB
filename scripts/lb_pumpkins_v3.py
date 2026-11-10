# Classifica Pumpkins: 2e8 zucche, 32 droni, campo 32x32. v3 del 6 nov 2026.
# v2 in gioco: 8:06 (ciclo ~7.5 s). Simulatore haysim/pumpsim.py: v2 455 s, v3 415 s (-9%);
# il simulatore e' ottimista del 7% rispetto al gioco, quindi stima in gioco ~7:20-7:25.
#
# Cosa cambia rispetto a v2 (tutto misurato col simulatore, vedi haysim/pump_blk.py):
# - Ogni drone ha un blocco 4x8 invece di una colonna 1x32 (8 blocchi per riga, 4 per colonna).
#   Le celle sono ordinate su un CICLO hamiltoniano (colonna sinistra in su, poi le righe a
#   serpentina in giu'): il riempimento parte da qualunque cella e torna al punto di partenza
#   senza viaggio di ritorno, e le celle pendenti sono vicine (spola corta). -6% da solo.
# - Acqua: il ciclo e' limitato dal viaggio del drone (non dalla crescita), quindi l'acqua sulle
#   fresche serve solo a far maturare le ultime piantate prima della seconda passata: 0.25 -> 0.5
#   quando la cella e' sotto 0.25 (spalmare l'acqua su tutto il campo conviene: resa concava).
#   Le ripiantate (percorso critico) vanno a 1.0. Il serbatoio (25.6/s) non basta a tenere il
#   campo a 1.0: a regime il campo sta a ~0.55-0.6 (decadimento 1%/s su 1024 celle).
# - Fertilizzante (0.8/s, ~5 per ciclo): usato solo sulle celle alla 4a morte nel ciclo
#   (crescita istantanea, resta il 20% di morte): spezza le catene piu' lunghe (-2.5%).
#   Costo: ogni zucca weird toglie 1536 zucche su 3.1M, irrilevante.
# - Con <= 2 celle pendenti il drone aspetta sul posto (rilevamento immediato della morte).
# Perche' il ciclo non scende sotto ~6.3 s (sim): 32 plant + 32 move (2.1 s) + seconda passata
# (32 move + ~6 ripiantate, 1.5 s) + terza passata (~0.6 s) + coda = massimo su 32 blocchi
# delle catene di morti (ogni generazione ~0.5 s). Il resto e' il "max su 32" (la mediana dei
# blocchi finisce a ~4.6 s, l'ultimo a ~6.3). Per andare oltre servono quadrati indipendenti
# (resa per cella identica per lato >= 6: blocchi 7x7 separati da corridoi vuoti, raccolti
# ognuno appena completo: sim ~392 s), ma con una barriera diversa da questa.
#
# Regole (Pumpkin.cs, PumpkinController.cs, Growable.cs): crescita 2 s / (1 + 4*acqua) (+-20%);
# al termine 20% di morte (dead_pumpkin: harvest 200 e ripiantare). Le zucche mature adiacenti si
# fondono nel quadrato piu' grande; resa L^2 * min(L, 6) * 512: il 32x32 vale 3.145.728 -> 64
# raccolti. Barriera: tutte le zucche di un gruppo hanno lo stesso measure(); dalla colonna 0,
# measure() == measure(West) legge (31, y) via wrap: vero solo quando il gruppo e' il 32x32.
# Corsa: durante le passate una cella None vuol dire che il main ha raccolto -> il ciclo finisce.
GOAL = 200000000

S = get_world_size()
PUMPKIN = Entities.Pumpkin
DEAD = Entities.Dead_Pumpkin
SOIL = Grounds.Soil
WATER = Items.Water
FERT = Items.Fertilizer
N = 32          # celle per blocco

WLOW = 0.25     # fresche: annaffia se la cella e' sotto WLOW ...
WTGT = 0.5      # ... fino a WTGT
WREP = 1.0      # ripiantate: fino a 1.0 (con quello che c'e' nel serbatoio)
WAIT_K = 2      # con <= WAIT_K pendenti si aspetta sul posto
FERT_GEN = 4    # fertilizzante dalla FERT_GEN-esima morte della cella nel ciclo


def block_cells(b):
	# blocco b: colonne 4*(b%8).., righe 8*(b//8)..; ciclo hamiltoniano di 32 celle
	x0 = (b % 8) * 4
	y0 = (b // 8) * 8
	cells = []
	for j in range(8):
		cells.append((x0, y0 + j))
	for jj in range(8):
		j = 7 - jj
		if jj % 2 == 0:
			for i in range(3):
				cells.append((x0 + 1 + i, y0 + j))
		else:
			for i in range(3):
				cells.append((x0 + 3 - i, y0 + j))
	dirs = []
	for k in range(N):
		a = cells[k]
		c = cells[(k + 1) % N]
		if c[0] > a[0]:
			dirs.append(East)
		elif c[0] < a[0]:
			dirs.append(West)
		elif c[1] > a[1]:
			dirs.append(North)
		else:
			dirs.append(South)
	return cells, dirs


def goto_start(cells):
	# dallo spawner (0, 0) alla prima cella del blocco, con wrap
	tx = cells[0][0]
	ty = cells[0][1]
	if tx <= S // 2:
		for _ in range(tx):
			move(East)
	else:
		for _ in range(S - tx):
			move(West)
	if ty <= S // 2:
		for _ in range(ty):
			move(North)
	else:
		for _ in range(S - ty):
			move(South)


def goto(cells, pos, k):
	# dentro il blocco (niente wrap): da cells[pos] a cells[k]
	a = cells[pos]
	c = cells[k]
	dx = c[0] - a[0]
	dy = c[1] - a[1]
	while dx > 0:
		move(East)
		dx -= 1
	while dx < 0:
		move(West)
		dx += 1
	while dy > 0:
		move(North)
		dy -= 1
	while dy < 0:
		move(South)
		dy += 1


def water_to(target):
	# porta l'acqua della cella a target (0.25 per unita') in UNA azione; se il serbatoio non
	# basta usa quello che c'e'
	need = (target - get_water()) * 4
	n = need // 1
	if n < need:
		n += 1
	if n <= 0:
		return
	tank = num_items(WATER)
	if tank < n:
		n = tank
	if n > 0:
		use_item(WATER, n)


def run_cycle(cells, dirs, gens, pos, first):
	# Riempie il blocco partendo da cells[pos] lungo il ciclo (torna su cells[pos]), poi passa
	# sulle celle pendenti finche' sono tutte mature o il main ha raccolto (cella None).
	# Ritorna l'indice della cella su cui si trova il drone.
	pending = []
	for i in range(N):
		k = (pos + i) % N
		if first and get_ground_type() != SOIL:
			till()
		t = get_entity_type()
		if t == DEAD:
			harvest()
			t = None
		if t == None:
			gens[k] = 0
			plant(PUMPKIN)
			if get_water() < WLOW:
				water_to(WTGT)
			pending.append(k)
		elif not can_harvest():
			pending.append(k)
		move(dirs[k])
	while len(pending) > 0:
		left = []
		for k in pending:
			goto(cells, pos, k)
			pos = k
			while True:
				t = get_entity_type()
				if t == PUMPKIN:
					if can_harvest():
						break
					# in crescita
					if gens[k] >= FERT_GEN and num_items(FERT) >= 1:
						use_item(FERT)
						continue
					if len(pending) > WAIT_K:
						left.append(k)
						break
				elif t == None:
					# il main ha raccolto il 32x32: il ciclo e' finito
					return pos
				else:
					# morta: ripianta subito (percorso critico)
					gens[k] += 1
					harvest()
					plant(PUMPKIN)
					if gens[k] >= FERT_GEN and num_items(FERT) >= 1:
						use_item(FERT)
						continue
					water_to(WREP)
					if len(pending) > WAIT_K:
						left.append(k)
						break
		pending = left
	return pos


def worker(b):
	def fn():
		cd = block_cells(b)
		cells = cd[0]
		dirs = cd[1]
		goto_start(cells)
		gens = []
		for _ in range(N):
			gens.append(0)
		pos = 0
		first = True
		while True:
			pos = run_cycle(cells, dirs, gens, pos, first)
			first = False
			while get_entity_type() != None:
				pass
	return fn


def spawn_range(lo, hi):
	while hi - lo > 1:
		mid = (lo + hi) // 2
		spawn_drone(spawn_range_task(mid, hi))
		hi = mid
	worker(lo)()


def spawn_range_task(lo, hi):
	def fn():
		spawn_range(lo, hi)
	return fn


clear()
spawn_drone(spawn_range_task(1, 32))
# il main ha il blocco 0 (x 0..3, y 0..7) e parte da (0, 0) = cells[0]
cd = block_cells(0)
cells = cd[0]
dirs = cd[1]
gens = []
for _ in range(N):
	gens.append(0)
pos = 0
first = True
c = 0
while True:
	pos = run_cycle(cells, dirs, gens, pos, first)
	first = False
	t_fill = get_time()
	# barriera dalla colonna 0: si porta su (0, y) della stessa riga (cells[y] = (0, y))
	cx = cells[pos][0]
	for _ in range(cx):
		move(West)
	pos = cells[pos][1]
	while measure() != measure(West):
		pass
	t_ok = get_time()
	before = num_items(Items.Pumpkin)
	harvest()
	c += 1
	quick_print("ciclo", c, "colonna finita a", t_fill, "campo completo a", t_ok, "raccolto", num_items(Items.Pumpkin) - before, "acqua", num_items(WATER))
	if num_items(Items.Pumpkin) >= GOAL:
		clear()
		break
