# Fastest Reset v4 — ordine Flekay (~33m) + ossa hamiltoniane + WS mega-zucca
# leaderboard_run(Leaderboards.Fastest_Reset, "lb_reset", 1000000)
# Copia in Save1 SOLO a gioco chiuso.
#
# Economia:
# - Oro = n²·2^(mazes-1) per reuse; gold/WS = n → max Expand
# - WS = floor(numWeird·0.5·min(n,6)·YF) da mega-zucca tutta fertilizzata
# - Ossa = length²·2^(dino-1); 1 serpente pieno 32x32 con dino≥2 ≥ 2M
# - Ossa: ciclo + scorciatoie measure (lb_dinosaur). Mai ciclo puro a vuoto.

ws = 1
max_ws = 1
COL = None
facing = North
sub = 1
busy = False
CYC = []
POSX = []
POSY = []
IDX = {}
NB = []
SNAKE_M = 1
MARGIN_MIN = 2
MARGIN_MAX = 12
DIRS4 = [North, East, South, West]
DXX = {North: 0, East: 1, South: 0, West: -1}
DYY = {North: 1, East: 0, South: -1, West: 0}
LEFT = {North: West, East: North, South: East, West: South}
RIGHT = {North: East, East: South, South: West, West: North}
OPP = {North: South, East: West, South: North, West: East}

# Ordine #1 Flekay (Unlock Order.md) — Leaderboard ~33:17
ORDER = [
	Unlocks.Speed,
	Unlocks.Plant,
	Unlocks.Expand,
	Unlocks.Expand,
	Unlocks.Speed,
	Unlocks.Carrots,
	Unlocks.Grass,
	Unlocks.Trees,
	Unlocks.Trees,
	Unlocks.Expand,
	Unlocks.Carrots,
	Unlocks.Speed,
	Unlocks.Expand,
	Unlocks.Watering,
	Unlocks.Watering,
	Unlocks.Carrots,
	Unlocks.Grass,
	Unlocks.Sunflowers,
	Unlocks.Fertilizer,
	Unlocks.Watering,
	Unlocks.Speed,
	Unlocks.Pumpkins,
	Unlocks.Watering,
	Unlocks.Polyculture,
	Unlocks.Speed,
	Unlocks.Expand,
	Unlocks.Fertilizer,
	Unlocks.Mazes,
	Unlocks.Megafarm,
	Unlocks.Trees,
	Unlocks.Trees,
	Unlocks.Carrots,
	Unlocks.Watering,
	Unlocks.Pumpkins,
	Unlocks.Pumpkins,
	Unlocks.Expand,
	Unlocks.Cactus,
	Unlocks.Dinosaurs,
	Unlocks.Dinosaurs,
	Unlocks.Polyculture,
	Unlocks.Mazes,
	Unlocks.Mazes,
	Unlocks.Megafarm,
	Unlocks.Megafarm,
	Unlocks.Grass,
	Unlocks.Trees,
	Unlocks.Fertilizer,
	Unlocks.Fertilizer,
	Unlocks.Watering,
	Unlocks.Carrots,
	Unlocks.Carrots,
	Unlocks.Pumpkins,
	Unlocks.Pumpkins,
	Unlocks.Expand,
	Unlocks.Megafarm,
	Unlocks.Cactus,
	Unlocks.Cactus,
	Unlocks.Dinosaurs,
	Unlocks.Dinosaurs,
	Unlocks.Dinosaurs,
	Unlocks.Mazes,
	Unlocks.Leaderboard,
]


def sync():
	global ws
	global max_ws
	ws = get_world_size()
	if ws > max_ws:
		max_ws = ws


def size_drones():
	sync()
	if num_unlocked(Unlocks.Megafarm) == 0:
		return
	md = max_drones()
	if md < 2:
		return
	cap = md
	if max_ws < cap:
		cap = max_ws
	if get_world_size() != cap:
		set_world_size(cap)
	sync()


def size_max():
	sync()
	if max_ws > 1 and get_world_size() != max_ws:
		set_world_size(max_ws)
	sync()


def ground(entity):
	if entity == Entities.Grass or entity == Entities.Bush:
		return Grounds.Grassland
	return Grounds.Soil


def fert():
	if num_unlocked(Unlocks.Fertilizer) > 0 and num_items(Items.Fertilizer) > 0:
		use_item(Items.Fertilizer)


def wait_fert(n):
	while num_items(Items.Fertilizer) < n:
		do_a_flip()


def water():
	if num_unlocked(Unlocks.Watering) > 0:
		if get_water() < 0.4 and num_items(Items.Water) > 0:
			use_item(Items.Water)


def sow(do_harvest, entity):
	if (do_harvest and can_harvest()) or get_entity_type() != entity:
		harvest()
	if get_ground_type() != ground(entity):
		till()
	water()
	if entity != Entities.Grass and get_entity_type() != entity:
		plant(entity)
	fert()


def goto(x, y):
	n = get_world_size()
	dx = (x - get_pos_x()) % n
	if dx <= n // 2:
		for _ in range(dx):
			move(East)
	else:
		for _ in range(n - dx):
			move(West)
	dy = (y - get_pos_y()) % n
	if dy <= n // 2:
		for _ in range(dy):
			move(North)
	else:
		for _ in range(n - dy):
			move(South)


def stock(entity, tiles):
	n = get_world_size()
	if tiles < n * n:
		tiles = n * n
	cost = get_cost(entity)
	if cost == None:
		return
	for item in cost:
		need = cost[item] * tiles
		if num_items(item) < need:
			farm(item, need)


def power_up():
	global busy
	if busy:
		return
	if num_unlocked(Unlocks.Sunflowers) == 0:
		return
	if num_items(Items.Power) >= 50:
		return
	busy = True
	farm_power(200)
	busy = False


def col_run():
	n = get_world_size()
	for _ in range(n):
		COL()
		move(North)


def columns(fn):
	global COL
	COL = fn
	n = get_world_size()
	if num_unlocked(Unlocks.Megafarm) > 0 and max_drones() > 1 and n <= max_drones():
		goto(0, 0)
		i = 0
		while i < n - 1:
			spawn_drone(col_run)
			move(East)
			i += 1
		col_run()
		while num_drones() > 1:
			pass
	else:
		for _ in range(n):
			for _ in range(n):
				fn()
				move(North)
			move(East)


# ---------- crop farms ----------

def farm_hay():
	size_drones()
	def cell():
		sow(True, Entities.Grass)
	columns(cell)


def farm_wood():
	size_drones()
	if num_unlocked(Unlocks.Trees) > 0:
		def cell():
			if (get_pos_x() + get_pos_y()) % 2 == 0:
				sow(True, Entities.Tree)
			else:
				sow(True, Entities.Bush)
		columns(cell)
	else:
		sow(True, Entities.Bush)


def farm_carrot():
	size_drones()
	n = get_world_size()
	stock(Entities.Carrot, n * n)
	def cell():
		sow(True, Entities.Carrot)
	columns(cell)


def farm_pumpkin():
	size_drones()
	n = get_world_size()
	stock(Entities.Pumpkin, n * n)
	def cell():
		sow(get_pos_x() == 0 and get_pos_y() == 0, Entities.Pumpkin)
	columns(cell)
	# ripara morti finché (0,0) è harvestable
	passes = 0
	while passes < 6:
		def fix():
			et = get_entity_type()
			if et == None or et == Entities.Dead_Pumpkin:
				if num_items(Items.Carrot) > 0:
					plant(Entities.Pumpkin)
				fert()
			elif not can_harvest():
				fert()
		columns(fix)
		goto(0, 0)
		if can_harvest() and get_entity_type() == Entities.Pumpkin:
			harvest()
			return
		passes += 1
	goto(0, 0)
	if can_harvest():
		harvest()


def farm_power(need):
	size_drones()
	n = get_world_size()
	stock(Entities.Sunflower, n * n)
	clear()
	def plant_sf():
		sow(False, Entities.Sunflower)
	columns(plant_sf)
	t0 = get_time()
	while get_time() < t0 + 3:
		pass
	p = 15
	while p >= 7 and num_items(Items.Power) < need:
		def cut():
			if measure() == p:
				fert()
				if can_harvest():
					harvest()
		columns(cut)
		p -= 1


def farm_ws(need):
	# Mega-zucca tutta fertilizzata: WS = floor(weird·0.5·min(n,6)·YF)
	while num_items(Items.Weird_Substance) < need:
		power_up()
		size_drones()
		n = get_world_size()
		stock(Entities.Pumpkin, n * n)
		wait_fert(n)
		clear()
		def plant_p():
			sow(False, Entities.Pumpkin)
			fert()
		columns(plant_p)
		passes = 0
		while passes < 10:
			wait_fert(n // 2 + 1)
			def fix():
				et = get_entity_type()
				if et == None or et == Entities.Dead_Pumpkin:
					if num_items(Items.Carrot) > 0:
						plant(Entities.Pumpkin)
					fert()
				elif not can_harvest():
					fert()
			columns(fix)
			goto(0, 0)
			if can_harvest() and get_entity_type() == Entities.Pumpkin:
				break
			passes += 1
		goto(0, 0)
		if can_harvest():
			harvest()
		else:
			# niente mega: harvest pezzo per pezzo fertilizzato
			def cut():
				fert()
				if can_harvest():
					harvest()
			columns(cut)


def shaker(fwd, back):
	n = get_world_size()
	lo = 0
	hi = n - 1
	while lo < hi:
		swapped = False
		last = lo
		cur = measure()
		k = lo
		while k < hi:
			nxt = measure(fwd)
			if cur != None and nxt != None and cur > nxt:
				swap(fwd)
				last = k
				swapped = True
			else:
				if nxt != None:
					cur = nxt
			move(fwd)
			k += 1
		if not swapped:
			return
		s = hi - last
		while s > 0:
			move(back)
			s -= 1
		hi = last
		if lo >= hi:
			return
		swapped = False
		last = hi
		cur = measure()
		k = hi
		while k > lo:
			nxt = measure(back)
			if cur != None and nxt != None and cur < nxt:
				swap(back)
				last = k
				swapped = True
			else:
				if nxt != None:
					cur = nxt
			move(back)
			k -= 1
		if not swapped:
			return
		s = last - lo
		while s > 0:
			move(fwd)
			s -= 1
		lo = last


def shake_col():
	shaker(North, South)


def shake_row():
	shaker(East, West)


def farm_cactus():
	power_up()
	size_drones()
	n = get_world_size()
	stock(Entities.Cactus, n * n)
	clear()
	def plant_c():
		sow(False, Entities.Cactus)
	columns(plant_c)
	if num_unlocked(Unlocks.Megafarm) > 0 and max_drones() >= n:
		goto(0, 0)
		i = 0
		while i < n - 1:
			spawn_drone(shake_col)
			move(East)
			i += 1
		shake_col()
		while num_drones() > 1:
			pass
		goto(0, 0)
		i = 0
		while i < n - 1:
			spawn_drone(shake_row)
			move(North)
			i += 1
		shake_row()
		while num_drones() > 1:
			pass
	else:
		x = 0
		while x < n:
			goto(x, 0)
			shaker(North, South)
			x += 1
		y = 0
		while y < n:
			goto(0, y)
			shaker(East, West)
			y += 1
	harvest()


# ---------- maze / gold ----------

def maze_step():
	global facing
	if move(RIGHT[facing]):
		facing = RIGHT[facing]
	elif move(facing):
		pass
	elif move(LEFT[facing]):
		facing = LEFT[facing]
	else:
		facing = OPP[facing]
		move(facing)


def to_treasure():
	global facing
	g = 0
	lim = get_world_size() * get_world_size() * 16
	while get_entity_type() != Entities.Treasure and g < lim:
		pos = measure()
		if pos == None:
			maze_step()
		else:
			tx = pos[0]
			ty = pos[1]
			moved = False
			if get_pos_x() < tx and can_move(East):
				move(East)
				facing = East
				moved = True
			elif get_pos_x() > tx and can_move(West):
				move(West)
				facing = West
				moved = True
			elif get_pos_y() < ty and can_move(North):
				move(North)
				facing = North
				moved = True
			elif get_pos_y() > ty and can_move(South):
				move(South)
				facing = South
				moved = True
			if not moved:
				maze_step()
		g += 1


def farm_gold(need):
	global facing
	global sub
	# Oro/WS = n → campo massimo. Un maze, reuse fino a 300.
	power_up()
	size_max()
	n = get_world_size()
	mult = 2 ** (num_unlocked(Unlocks.Mazes) - 1)
	sub = n * mult
	while num_items(Items.Gold) < need:
		if num_items(Items.Weird_Substance) < sub:
			# batch WS per ~un maze pieno di reuse, non di più
			batch = sub * 40
			missing = need - num_items(Items.Gold)
			gold_each = n * n * mult
			if gold_each < 1:
				gold_each = 1
			trips = missing // gold_each + 2
			if trips < 40:
				batch = sub * trips
			if batch < sub:
				batch = sub
			farm_ws(num_items(Items.Weird_Substance) + batch)
			size_max()
			n = get_world_size()
			mult = 2 ** (num_unlocked(Unlocks.Mazes) - 1)
			sub = n * mult
		clear()
		plant(Entities.Bush)
		if not use_item(Items.Weird_Substance, sub):
			farm_ws(num_items(Items.Weird_Substance) + sub)
			continue
		facing = North
		to_treasure()
		r = 0
		while num_items(Items.Gold) < need and num_items(Items.Weird_Substance) >= sub and r < 300:
			if get_entity_type() != Entities.Treasure:
				to_treasure()
			if get_entity_type() != Entities.Treasure:
				break
			before = num_items(Items.Gold)
			if not use_item(Items.Weird_Substance, sub):
				break
			r += 1
			# aspetta spostamento tesoro
			tpos = measure()
			w = 0
			while measure() == tpos and w < 200:
				w += 1
			if num_items(Items.Gold) <= before and r > 1:
				break
		if get_entity_type() == Entities.Treasure:
			harvest()


# ---------- bones: ciclo + scorciatoie verso mela (come lb_dinosaur) ----------
# Bug 6h: ciclo puro senza mele non collide mai → lim=n⁴ mosse a vuoto.

def build_snake_maps(n):
	global CYC
	global POSX
	global POSY
	global IDX
	global NB
	global SNAKE_M
	d = []
	i = 0
	while i < n - 1:
		d.append(East)
		i += 1
	k = 0
	while k < n - 1:
		if k == 0:
			j = 0
			while j < n - 1:
				d.append(North)
				j += 1
		elif k % 2 == 0:
			j = 0
			while j < n - 2:
				d.append(North)
				j += 1
		else:
			j = 0
			while j < n - 2:
				d.append(South)
				j += 1
		d.append(West)
		k += 1
	i = 0
	while i < n - 1:
		d.append(South)
		i += 1
	CYC = d
	SNAKE_M = n * n
	POSX = []
	POSY = []
	IDX = {}
	x = 0
	y = 0
	k = 0
	while k < SNAKE_M:
		POSX.append(x)
		POSY.append(y)
		IDX[(x, y)] = k
		x += DXX[CYC[k]]
		y += DYY[CYC[k]]
		k += 1
	NB = []
	k = 0
	while k < SNAKE_M:
		lst = []
		for ddir in DIRS4:
			nx = POSX[k] + DXX[ddir]
			ny = POSY[k] + DYY[ddir]
			if nx >= 0 and nx < n and ny >= 0 and ny < n:
				lst.append((ddir, IDX[(nx, ny)]))
		NB.append(lst)
		k += 1


def run_snake(target_len):
	# Ritorna lunghezza. Esce appena L >= target_len o collisione.
	goto(0, 0)
	change_hat(Hats.Dinosaur_Hat)
	if get_entity_type() != Entities.Apple:
		change_hat(Hats.Straw_Hat)
		return 0
	body = [0]
	occ = set()
	occ.add(0)
	h = 0
	L = 1
	t_idx = -1
	tx = 0
	ty = 0
	M = SNAKE_M
	while L < M and L < target_len:
		on_apple = get_entity_type() == Entities.Apple
		if on_apple:
			tp = measure()
			if tp == None:
				t_idx = -1
			else:
				t_idx = IDX[tp]
				tx = tp[0]
				ty = tp[1]
		elif t_idx == h:
			t_idx = -1
		nh = (h + 1) % M
		choice = CYC[h]
		if t_idx >= 0:
			d_apple = (t_idx - h) % M
			if d_apple > 1:
				if L > 1:
					d_tail = (body[0] - h) % M
				else:
					d_tail = M
				lim = d_tail - (MARGIN_MIN + (MARGIN_MAX - MARGIN_MIN) * L // M)
				if lim > d_apple + 1:
					lim = d_apple + 1
				best_dist = abs(POSX[nh] - tx) + abs(POSY[nh] - ty)
				best_dd = 1
				for pair in NB[h]:
					ddir = pair[0]
					ni = pair[1]
					dd = (ni - h) % M
					if dd > 1 and dd < lim and not (ni in occ):
						dist = abs(POSX[ni] - tx) + abs(POSY[ni] - ty)
						if dist < best_dist or (dist == best_dist and dd > best_dd):
							best_dist = dist
							best_dd = dd
							choice = ddir
							nh = ni
		if not move(choice):
			moved = False
			for pair in NB[h]:
				ni = pair[1]
				if not (ni in occ) and move(pair[0]):
					nh = ni
					moved = True
					break
			if not moved:
				break
		h = nh
		body.append(h)
		occ.add(h)
		if on_apple:
			L += 1
			if t_idx < 0:
				break
		else:
			occ.remove(body.pop(0))
	change_hat(Hats.Straw_Hat)
	return L


def farm_bones(need):
	power_up()
	size_max()
	n = get_world_size()
	cost = get_cost(Entities.Apple)
	pa = 1
	if cost != None and Items.Cactus in cost:
		pa = cost[Items.Cactus]
	build_snake_maps(n)
	dino_lv = num_unlocked(Unlocks.Dinosaurs)
	mult = 1
	if dino_lv > 1:
		mult = 2 ** (dino_lv - 1)
	while num_items(Items.Bone) < need:
		remain = need - num_items(Items.Bone)
		# L² * mult >= remain → L >= ceil(sqrt(remain/mult))
		need_L = 2
		while need_L * need_L * mult < remain:
			need_L += 1
			if need_L > n * n - 1:
				need_L = n * n - 1
				break
		# cactus per need_L mele (+margine)
		need_c = pa * (need_L + n)
		if num_items(Items.Cactus) < need_c:
			farm(Items.Cactus, need_c)
			size_max()
			n = get_world_size()
			build_snake_maps(n)
			dino_lv = num_unlocked(Unlocks.Dinosaurs)
			mult = 1
			if dino_lv > 1:
				mult = 2 ** (dino_lv - 1)
		clear()
		def prep():
			if get_ground_type() != Grounds.Soil:
				till()
			if get_entity_type() != None:
				harvest()
		columns(prep)
		before = num_items(Items.Bone)
		L = run_snake(need_L + 2)
		quick_print("snake", L, "bone", num_items(Items.Bone), get_time())
		if num_items(Items.Bone) <= before:
			# nessuna mela mangiata: manca cactus o ciclo rotto
			farm(Items.Cactus, pa * n * n)
			if L < 2:
				do_a_flip()


# ---------- dispatch ----------

def farm(item, num):
	global busy
	while num_items(item) < num:
		if item == Items.Hay:
			farm_hay()
		elif item == Items.Wood:
			farm_wood()
		elif item == Items.Carrot:
			farm_carrot()
		elif item == Items.Power:
			if busy:
				return
			busy = True
			farm_power(num)
			busy = False
		elif item == Items.Pumpkin:
			farm_pumpkin()
		elif item == Items.Weird_Substance:
			farm_ws(num)
		elif item == Items.Cactus:
			farm_cactus()
		elif item == Items.Bone:
			farm_bones(num)
		elif item == Items.Gold:
			farm_gold(num)
		elif item == Items.Water or item == Items.Fertilizer:
			do_a_flip()
		else:
			quick_print("skip", item)
			return


def unlock_tech(tech):
	quick_print("need", tech)
	cost = get_cost(tech)
	if cost != None:
		for item in cost:
			farm(item, cost[item])
	if not unlock(tech):
		unlock_tech(tech)
	if tech == Unlocks.Expand:
		sync()
	quick_print("ok", tech, get_time())


def run():
	sync()
	quick_print("reset v4 flekay+ham")
	t0 = get_time()
	for tech in ORDER:
		if num_unlocked(Unlocks.Leaderboard) > 0:
			break
		unlock_tech(tech)
	while num_unlocked(Unlocks.Leaderboard) == 0:
		unlock_tech(Unlocks.Leaderboard)
	quick_print("done", get_time() - t0)
	do_a_flip()


if num_unlocked(Unlocks.Speed) == 0 and num_unlocked(Unlocks.Plant) == 0:
	run()
else:
	quick_print("Avvia via leaderboard_run/simulate, non sul save live")
