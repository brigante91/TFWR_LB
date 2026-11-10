# lib.py - funzioni comuni estratte dagli script (Save1, rng_predictor/lb_*, script_achievement).
# Uso:  import lib          ->  lib.goto(3, 5)
#       from lib import *   ->  goto(3, 5)
# Nessuna funzione legge una S globale: la dimensione si legge con get_world_size() al momento
# della chiamata, cosi' resta giusta anche dopo set_world_size().
# Per gli script da classifica le versioni locali "micro-ottimizzate" (es. goto senza
# get_pos in lb_hay_micro) restano piu' veloci: qui c'e' la versione generica.


# ---------------------------------------------------------------- direzioni
DIRS = [North, East, South, West]
DX = {North: 0, East: 1, South: 0, West: -1}
DY = {North: 1, East: 0, South: -1, West: 0}
OPP = {North: South, East: West, South: North, West: East}
LEFT = {North: West, East: North, South: East, West: South}
RIGHT = {North: East, East: South, South: West, West: North}


# ---------------------------------------------------------------- movimento
def goto(tx, ty):
	# percorso piu' corto con wrap (campo aperto). Era goto/vai in ~40 script.
	n = get_world_size()
	dx = (tx - get_pos_x()) % n
	if dx <= n // 2:
		for _ in range(dx):
			move(East)
	else:
		for _ in range(n - dx):
			move(West)
	dy = (ty - get_pos_y()) % n
	if dy <= n // 2:
		for _ in range(dy):
			move(North)
	else:
		for _ in range(n - dy):
			move(South)


def goto_from_origin(tx, ty):
	# come goto ma parte da (0, 0) senza leggere la posizione (goto_start, lb_hay_micro)
	n = get_world_size()
	if tx <= n // 2:
		for _ in range(tx):
			move(East)
	else:
		for _ in range(n - tx):
			move(West)
	if ty <= n // 2:
		for _ in range(ty):
			move(North)
	else:
		for _ in range(n - ty):
			move(South)


def goto_x(x):
	# da x = 0 alla colonna x, con wrap (lb_pumpkins_v2, lb_sunflowers_v2)
	n = get_world_size()
	if x <= n // 2:
		for _ in range(x):
			move(East)
	else:
		for _ in range(n - x):
			move(West)


def goto_nowrap(tx, ty):
	# senza wrap, utile quando ci sono ostacoli sul bordo (vai di f14)
	while get_pos_x() < tx:
		move(East)
	while get_pos_x() > tx:
		move(West)
	while get_pos_y() < ty:
		move(North)
	while get_pos_y() > ty:
		move(South)


def step(dx, dy):
	# spostamento relativo senza leggere la posizione
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


def goto_cell(cells, pos, k):
	# da cells[pos] a cells[k] dentro un blocco (goto di lb_pumpkins_v3/v4, zucca)
	step(cells[k][0] - cells[pos][0], cells[k][1] - cells[pos][1])
	return k


def goto_k(k, cur, bw):
	# celle numerate k = y * bw + x dentro un blocco largo bw (go_to_k dei girasoli)
	step(k % bw - cur % bw, k // bw - cur // bw)
	return k


# ---------------------------------------------------------------- attese
def wait_until(t):
	while get_time() < t:
		pass


def wait_ready():
	# while not can_harvest(): pass  (31 script)
	while not can_harvest():
		pass


def wait_all(handles):
	for h in handles:
		if h != None:
			wait_for(h)


# ---------------------------------------------------------------- terreno e semina
def ensure_soil():
	if get_ground_type() != Grounds.Soil:
		till()


def ensure_grassland():
	if get_ground_type() != Grounds.Grassland:
		till()


def ground_for(entity):
	if entity == Entities.Grass or entity == Entities.Bush or entity == Entities.Tree:
		return Grounds.Grassland
	return Grounds.Soil


def sow(entity, do_water):
	# raccoglie se serve, sistema il terreno, annaffia e pianta (lb_reset)
	et = get_entity_type()
	if can_harvest() or (et != None and et != entity and et != Entities.Dead_Pumpkin):
		harvest()
	if get_ground_type() != ground_for(entity):
		till()
	if do_water:
		water_min(0.5)
	if entity != Entities.Grass and get_entity_type() != entity:
		plant(entity)


def harvest_if_ready():
	if can_harvest():
		harvest()
		return True
	return False


# ---------------------------------------------------------------- acqua e fertilizzante
def water_to(target):
	# porta l'acqua della cella a target (0.25 per unita') in UNA azione;
	# se il serbatoio non basta usa quello che c'e' (lb_pumpkins_v3/v4, zucca)
	need = (target - get_water()) * 4
	n = need // 1
	if n < need:
		n += 1
	if n <= 0:
		return
	tank = num_items(Items.Water)
	if tank < n:
		n = tank
	if n > 0:
		use_item(Items.Water, n)


def water_min(level):
	# annaffia una unita' alla volta finche' la cella e' sotto level (water_here, seed_cell)
	while get_water() < level and num_items(Items.Water) > 0:
		use_item(Items.Water)


def fertilize_until_ready():
	while not can_harvest() and num_items(Items.Fertilizer) > 0:
		use_item(Items.Fertilizer)


# ---------------------------------------------------------------- droni
def bind(fn, a):
	# closure per spawn_drone in stile vecchio (make_column, make_task, make_prep...)
	def task():
		return fn(a)
	return task


def bind2(fn, a, b):
	def task():
		return fn(a, b)
	return task


def spawn_range(lo, hi, fn):
	# esegue fn(i) per i in [lo, hi) con spawn ad albero binario: ogni drone ne lancia
	# altri e poi fa fn(lo). Non aspetta nessuno (spawn_range/spawn_range_task/make_task).
	while hi - lo > 1:
		mid = (lo + hi) // 2
		if spawn_drone(spawn_range, mid, hi, fn) == None:
			# droni finiti: questa meta' la faccio io
			for i in range(mid, hi):
				fn(i)
		hi = mid
	fn(lo)


def run_parallel(fn, n):
	# fn(i) per i in [0, n): fn(0) sul drone corrente, gli altri su droni nuovi,
	# poi aspetta tutti (run_phase di Cactus, prep_field di OSSA/lb_dinosaur)
	handles = []
	rest = []
	for i in range(1, n):
		h = spawn_drone(fn, i)
		if h == None:
			rest.append(i)
		else:
			handles.append(h)
	fn(0)
	for i in rest:
		fn(i)
	wait_all(handles)


def map_parallel(fn, items, arg):
	# come in_parallelo (f13, f17): fn(item, arg) per ogni item, un drone per item;
	# ritorna la lista dei risultati nello stesso ordine di items
	handles = []
	for i in range(1, len(items)):
		handles.append(spawn_drone(fn, items[i], arg))
	res = [fn(items[0], arg)]
	for i in range(1, len(items)):
		h = handles[i - 1]
		if h == None:
			res.append(fn(items[i], arg))
		else:
			res.append(wait_for(h))
	return res


# ---------------------------------------------------------------- campo
def prep_column(x):
	# zappa e svuota la colonna x (prep_column di OSSA/lb_dinosaur)
	goto(x, 0)
	for _ in range(get_world_size()):
		ensure_soil()
		if get_entity_type() != None:
			harvest()
		move(North)


def prep_field():
	run_parallel(prep_column, get_world_size())


# ---------------------------------------------------------------- cactus
def shaker(fwd, back):
	# cocktail sort sulla linea lunga quanto il campo; il drone parte dalla casella 0
	# e si ferma appena una passata non scambia nulla (versione di lb_cactus_v3)
	lo = 0
	hi = get_world_size() - 1
	while lo < hi:
		last = lo
		swapped = False
		cur = measure()
		k = lo
		while k < hi:
			nxt = measure(fwd)
			if cur > nxt:
				swap(fwd)
				last = k
				swapped = True
			else:
				cur = nxt
			move(fwd)
			k += 1
		if not swapped:
			return
		for _ in range(hi - last):
			move(back)
		hi = last
		if lo >= hi:
			return
		last = hi
		swapped = False
		cur = measure()
		k = hi
		while k > lo:
			nxt = measure(back)
			if cur < nxt:
				swap(back)
				last = k
				swapped = True
			else:
				cur = nxt
			move(back)
			k -= 1
		if not swapped:
			return
		for _ in range(last - lo):
			move(fwd)
		lo = last


def sort_column(x):
	goto(x, 0)
	shaker(North, South)


def sort_row(y):
	goto(0, y)
	shaker(East, West)


def sort_field():
	# colonne poi righe, in parallelo: dopo il campo e' pronto per un raccolto a catena
	n = get_world_size()
	run_parallel(sort_column, n)
	run_parallel(sort_row, n)


# ---------------------------------------------------------------- compagni (policoltura)
def reroll_companion(seed, accept):
	# ripianta seed finche' accept(entita', (x, y)) del compagno e' vero
	# (reroll di lb_carrots/f11 con BUSH, di lb_wood/legna con GRASS)
	c, pos = get_companion()
	while not accept(c, pos):
		old = (c, pos)
		plant(seed)  # sopra la pianta acerba a volte basta un'azione
		c, pos = get_companion()
		if (c, pos) == old:
			harvest()
			plant(seed)
			c, pos = get_companion()
	return c, pos


# ---------------------------------------------------------------- labirinti
def maze_amount():
	# sostanza strana per un labirinto grande quanto il campo
	return get_world_size() * 2 ** (num_unlocked(Unlocks.Mazes) - 1)


def maze_new():
	plant(Entities.Bush)
	use_item(Items.Weird_Substance, maze_amount())


def maze_wall_follow():
	# mano destra sul muro finche' trova il tesoro (maze_search di lb_reset). Non raccoglie.
	facing = North
	while get_entity_type() != Entities.Treasure:
		if move(RIGHT[facing]):
			facing = RIGHT[facing]
		elif move(facing):
			pass
		elif move(LEFT[facing]):
			facing = LEFT[facing]
		else:
			facing = OPP[facing]
			move(facing)


def maze_find_treasure():
	# DFS che prova prima la direzione piu' vicina al tesoro (measure() da' la sua
	# posizione); si ferma sulla cella del tesoro, non raccoglie (explorer di lb_maze)
	t = measure()
	tx = t[0]
	ty = t[1]
	x = get_pos_x()
	y = get_pos_y()
	visited = set()
	visited.add((x, y))
	stack = []
	while get_entity_type() != Entities.Treasure:
		best = None
		best_p = None
		best_dist = 99999
		for d in DIRS:
			p = (x + DX[d], y + DY[d])
			if not (p in visited):
				dist = abs(p[0] - tx) + abs(p[1] - ty)
				if dist < best_dist and can_move(d):
					best = d
					best_p = p
					best_dist = dist
		if best != None:
			move(best)
			visited.add(best_p)
			stack.append(best)
		elif len(stack) > 0:
			move(OPP[stack.pop()])
		else:
			visited = set()
			visited.add((x, y))
		x = get_pos_x()
		y = get_pos_y()


# ---------------------------------------------------------------- dinosauro
def build_cycle(n):
	# ciclo hamiltoniano su un campo n x n (n pari) partendo da (0, 0):
	# lista di direzioni da ripetere all'infinito (OSSA, lb_dinosaur)
	d = []
	for i in range(n - 1):
		d.append(East)
	for k in range(n - 1):
		if k == 0:
			for i in range(n - 1):
				d.append(North)
		elif k % 2 == 0:
			for i in range(n - 2):
				d.append(North)
		else:
			for i in range(n - 2):
				d.append(South)
		d.append(West)
	for i in range(n - 1):
		d.append(South)
	return d
	