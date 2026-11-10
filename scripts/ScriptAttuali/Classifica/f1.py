# Classifica Maze: 9.863.168 oro. 32 droni, 16 labirinti 8x8 con 2 droni ciascuno.
# Progettato con haysim/mazesim.py (che esegue questo stesso file).
#
# Regole (dal sorgente): use_item(WS, 256) su un cespuglio (anche non cresciuto) genera
# un labirinto 8x8 centrato sul cespuglio (origine = cespuglio - (4,4)); measure() da una
# siepe = posizione del tesoro; use_item(WS, 256) sul tesoro da' 2048 oro e lo sposta
# (200 tick) in una cella casuale; a ogni trasloco ogni muro si apre con p = 0.002;
# dopo 300 riusi use_item fallisce (1 tick) e harvest() da' altri 2048 rimuovendo il
# labirinto: si ripianta il cespuglio e si rigenera (i 300 riusi sono per labirinto).
# ATTENZIONE: harvest() su una SIEPE distrugge il labirinto senza oro.
# I droni non possono entrare in un labirinto dall'esterno: tutti devono essere dentro
# il proprio quadrato quando viene generato (T_GEN per il primo; poi restano dentro).
#
# Strategia per coppia: entrambi i droni corrono al tesoro (il primo lo usa, l'altro se ne
# accorge con measure() e torna al proprio "centro"); mappa dei muri appresa con can_move
# (albero di esplorazione: genitore di ogni cella), cammino = percorso nell'albero piu'
# le scorciatoie dei muri apertisi (riscoperti ricontrollando can_move sui muri noti).
GOAL = 9863168
M = 8            # lato del labirinto (8 -> 16 labirinti, 2 droni ciascuno)
IDLE = 1         # drone libero: 0 aspetta, 1 esplora la propria zona poi va al centro, 2 va al centro
RACE = 1         # 1: entrambi i droni corrono al tesoro; 0: solo quello della zona
REPROBE = 1      # ricontrolla i muri noti a ogni passaggio (muri che si aprono)
SHORTCUT = 1     # usa i varchi noti fuori dall'albero per accorciare il cammino
PRINT_EVERY = 25 # stampa ogni 25 riusi propri (~50 del labirinto)

S = get_world_size()
NX = S // M
NM = NX * NX              # labirinti
ND = max_drones()
DPM = ND // NM            # droni per labirinto
WS = Items.Weird_Substance
GOLD = Items.Gold
AMOUNT = M * 2 ** (num_unlocked(Unlocks.Mazes) - 1)
DIRS = [North, East, South, West]
DD = [1, S, -1, -S]       # delta dell'id di cella (id = x * S + y)
REV = [2, 3, 0, 1]
if DPM == 1:
	RX = 1
	RY = 1
elif DPM == 2:
	RX = 2
	RY = 1
elif DPM == 8:
	RX = 4
	RY = 2
else:
	RX = 8
	RY = 4
RW = M // RX              # larghezza della zona di un drone
RH = M // RY
BUSH_OFF = M // 2         # cespuglio in (ox + M//2, oy + M//2) -> quadrato [ox, ox+M)
GEN_SLOT = (BUSH_OFF // RH) * RX + BUSH_OFF // RW
TPS = 6075


def wdist(a, b):
	d = (a - b) % S
	if d > S // 2:
		return S - d
	return d


def goto(tx, ty):
	# campo aperto (nessuna siepe sul percorso)
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


def home_of(ox, oy, slot):
	return (ox + (slot % RX) * RW + RW // 2, oy + (slot // RX) * RH + RH // 2)


def serve_life(ox, oy, slot, verbose):
	# una vita del labirinto (300 riusi + harvest); il labirinto esiste gia' e il drone
	# e' dentro. Ritorna True se e' stato questo drone a fare l'harvest finale.
	zx0 = ox + (slot % RX) * RW
	zy0 = oy + (slot // RX) * RH
	zx1 = zx0 + RW
	zy1 = zy0 + RH
	h = home_of(ox, oy, slot)
	c0 = h[0] * S + h[1]

	# mappa: albero di esplorazione (par, pd), frontiera, celle visitate, varchi extra
	par = {}
	pd = {}
	front = {}
	known = {}
	extra = {}
	cs = get_pos_x() * S + get_pos_y()
	par[cs] = -1
	pd[cs] = 0
	cur = [cs]

	def add_extra(c, e, n):
		if c in extra:
			extra[c].append(e)
		else:
			extra[c] = [e]
		if n in extra:
			extra[n].append(REV[e])
		else:
			extra[n] = [REV[e]]

	def probe(c):
		# prima visita: controlla le 4 direzioni e scopre i vicini
		k = []
		for e in range(4):
			if can_move(DIRS[e]):
				k.append(True)
				n = c + DD[e]
				if not n in par:
					par[n] = c
					pd[n] = e
					front[n] = 1
				elif SHORTCUT and par[c] != n and par[n] != c and not n in known:
					add_extra(c, e, n)
			else:
				k.append(False)
		known[c] = k
		if c in front:
			front.pop(c)

	def reprobe(c):
		# visite successive: solo i muri noti (possono essersi aperti)
		k = known[c]
		for e in range(4):
			if not k[e]:
				if can_move(DIRS[e]):
					k[e] = True
					n = c + DD[e]
					if not n in par:
						par[n] = c
						pd[n] = e
						front[n] = 1
					elif SHORTCUT:
						add_extra(c, e, n)

	def arrive():
		c = cur[0]
		if c in known:
			if REPROBE:
				reprobe(c)
		else:
			probe(c)

	def plan(a, b):
		# cammino nell'albero da a a b, come lista di direzioni
		anc = {}
		x = b
		k = 0
		while x != -1:
			anc[x] = k
			k += 1
			x = par[x]
		path = []
		x = a
		while not x in anc:
			path.append(REV[pd[x]])
			x = par[x]
		down = []
		y = b
		while y != x:
			down.append(pd[y])
			y = par[y]
		i = len(down)
		while i > 0:
			i -= 1
			path.append(down[i])
		return path

	def walk(path, watch):
		# segue path da cur[0]; watch = posizione del tesoro da sorvegliare (o None)
		# ritorna False se il tesoro si e' mosso (o il labirinto e' sparito)
		n = len(path)
		if SHORTCUT:
			idx = {}
			x = cur[0]
			for j in range(n):
				x = x + DD[path[j]]
				idx[x] = j + 1
		i = 0
		while i < n:
			arrive()
			c = cur[0]
			nd = path[i]
			ni = i + 1
			if SHORTCUT and c in extra:
				for e in extra[c]:
					mm = c + DD[e]
					if mm in idx and idx[mm] > ni:
						nd = e
						ni = idx[mm]
			if watch != None and measure() != watch:
				return False
			move(DIRS[nd])
			cur[0] = c + DD[nd]
			i = ni
		arrive()
		return True

	def nearest_front(tx, ty, zone):
		best = -1
		bd = 9999
		for f in front:
			fx = f // S
			fy = f % S
			if zone and (fx < zx0 or fx >= zx1 or fy < zy0 or fy >= zy1):
				continue
			d = abs(fx - tx) + abs(fy - ty)
			if d < bd:
				bd = d
				best = f
		return best

	def go_to(tc, tx, ty, watch):
		# raggiunge la cella tc = (tx, ty); ritorna True se ci arriva
		while cur[0] != tc:
			if tc in par:
				goal = tc
			else:
				goal = nearest_front(tx, ty, False)
				if goal == -1:
					return False
			if not walk(plan(cur[0], goal), watch):
				return False
		return True

	def idle(t):
		# il tesoro non e' mio: esplora la mia zona, poi torna al centro, poi aspetta
		if IDLE == 1:
			g = nearest_front(cur[0] // S, cur[0] % S, True)
			if g != -1:
				walk(plan(cur[0], g), t)
				return
		if IDLE > 0 and cur[0] != c0:
			if c0 in par:
				walk(plan(cur[0], c0), t)
				return
			g = nearest_front(c0 // S, c0 % S, False)
			if g != -1:
				walk(plan(cur[0], g), t)
				return
		while measure() == t:
			pass

	arrive()
	uses = 0
	while True:
		if num_items(GOLD) >= GOAL:
			return False
		t = measure()
		if t == None:
			return False
		tx = t[0]
		ty = t[1]
		tc = tx * S + ty
		if RACE or (tx >= zx0 and tx < zx1 and ty >= zy0 and ty < zy1):
			if RACE:
				ok = go_to(tc, tx, ty, t)
			else:
				ok = go_to(tc, tx, ty, None)
			if ok and can_harvest():
				if use_item(WS, AMOUNT):
					uses += 1
					if verbose and uses % PRINT_EVERY == 0:
						quick_print("riusi", uses, "oro", num_items(GOLD), get_time())
				elif get_entity_type() == Entities.Treasure:
					harvest()
					if verbose:
						quick_print("harvest", get_time(), "oro", num_items(GOLD))
					return True
		else:
			idle(t)


def work(k):
	# tempo di generazione: tutti i droni partono da (0,0) a 1000 tick e devono essere
	# dentro il proprio quadrato prima che un qualunque labirinto venga generato
	m = k % NM
	slot = k // NM
	ox = (m % NX) * M
	oy = (m // NX) * M
	dmax = 0
	for mm in range(NM):
		for s in range(DPM):
			h = home_of((mm % NX) * M, (mm // NX) * M, s)
			d = wdist(h[0], 0) + wdist(h[1], 0)
			if d > dmax:
				dmax = d
	t_gen = (1000 + 200 * dmax + 300) / TPS
	verbose = k == 0
	gen = slot == GEN_SLOT
	if gen:
		goto(ox + BUSH_OFF, oy + BUSH_OFF)
		plant(Entities.Bush)
		while get_time() < t_gen:
			pass
		use_item(WS, AMOUNT)
		if verbose:
			quick_print("labirinto generato", get_time())
	else:
		h = home_of(ox, oy, slot)
		goto(h[0], h[1])
		while measure() == None:
			pass
	while True:
		gen = serve_life(ox, oy, slot, verbose)
		if num_items(GOLD) >= GOAL:
			break
		if gen:
			# ho raccolto il tesoro: il quadrato e' libero, rigenero dal centro
			goto(ox + BUSH_OFF, oy + BUSH_OFF)
			plant(Entities.Bush)
			use_item(WS, AMOUNT)
			if verbose:
				quick_print("labirinto rigenerato", get_time())
		else:
			# l'altro drone rigenera: torno verso casa restando nel quadrato
			h = home_of(ox, oy, slot)
			goto(h[0], h[1])
			while measure() == None:
				if num_items(GOLD) >= GOAL:
					break
	if k == 0:
		while num_items(GOLD) < GOAL:
			pass
		quick_print("fine", get_time(), "oro", num_items(GOLD))
		clear()


def make_boot(k, lvl):
	def boot():
		j = lvl
		while j < 5:
			spawn_drone(make_boot(k + 2 ** j, j + 1))
			j += 1
		work(k)
	return boot


clear()
make_boot(0, 0)()
