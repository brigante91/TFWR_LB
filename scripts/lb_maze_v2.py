# Classifica Maze: 9.863.168 oro = 301 x 32768 = un solo labirinto 32x32 (tutto il campo)
# riusato 300 volte + harvest finale, con tutti i 32 droni dentro.
# Progettato e validato con haysim/mazesim.py (che esegue questo stesso file).
#
# Perche' un solo labirinto: l'oro vale 301 x lato^2 x 32 per labirinto, quindi la somma dei
# lato^2 deve fare 1024 (16 da 8x8, 4 da 16x16 o 1 da 32x32): la densita' di droni e' la
# stessa, ma il "piu' vicino fra 32" ha una coda molto piu' corta del "piu' vicino fra 2"
# (modello a conoscenza perfetta: 8x8/2 droni 84 s, 16x16/8 63 s, 32x32/32 60 s).
# Il labirinto copre tutto il campo: nessun vincolo di posizionamento, una sola generazione,
# un solo harvest, e le aperture dei muri (p = 0.002 per adiacenza a ogni riuso) si
# accumulano tutte nello stesso labirinto (cammini ad albero 96 s vs cammini reali 60 s).
#
# Regole (dal sorgente): use_item(WS, 1024) su un cespuglio (anche non cresciuto) genera il
# labirinto 32x32 da qualunque cella; measure() da una siepe = (x, y) del tesoro (quella
# vecchia durante il trasloco); use_item(WS, 1024) sul tesoro da' 32768 oro e lo sposta in
# 200 tick in una cella casuale; un secondo use_item durante il trasloco fallisce ma costa
# 200 (si evita con can_harvest()); dopo 300 riusi use_item fallisce (1 tick) e harvest()
# del tesoro da' gli ultimi 32768 rimuovendo il labirinto. ATTENZIONE: harvest() su una
# SIEPE distrugge il labirinto senza oro: si raccoglie solo se get_entity_type() e' Treasure.
# I muri esterni sono chiusi: i droni devono essere gia' dentro (tutto il campo lo e').
#
# Strategia per drone (nessuna comunicazione): casa al centro di un blocco 4x8; mappa dei
# muri appresa con can_move (ricontrollando i muri noti a ogni passaggio: si aprono);
# albero di cammini radicato a casa (profondita' coerenti -> cammino fra due celle per
# risalita), scorciatoie adottate quando si scopre un varco verso una cella meno profonda,
# ricostruzione BFS dell'albero da fermo. Da fermo esplora (DFS fisico) la palla di raggio
# RAD (in distanza d'albero) attorno a casa. Quando il tesoro cade in una cella che conosce
# a distanza d parte subito se d <= R_GO, altrimenti dopo (d - R_GO) * STAG tick: cosi' il
# drone piu' vicino nel labirinto arriva per primo e gli altri non si ammassano. Se la
# cella e' sconosciuta, dopo W0 tick la cerca il proprietario del blocco (Manhattan).
GOAL = 9863168
R_GO = 4          # parto subito se il cammino noto e' <= R_GO
STAG = 150        # tick di attesa per ogni passo oltre R_GO
R_MAX = 14        # non calcolo nemmeno il cammino se |dx|+|dy| > R_MAX (salvo blocco mio)
W0 = 400          # tick di attesa del proprietario del blocco prima di cercare una cella ignota
RAD = 20          # raggio (profondita' nell'albero) dell'esplorazione da fermo (0: niente)
REBUILD = 10      # ogni quanti round (da fermo) ricostruire l'albero BFS sul grafo noto (0: mai)
REPROBE = 1       # ricontrolla i muri noti a ogni passaggio (muri che si aprono)
FW = 1            # peso della distanza da me nella scelta della frontiera verso un bersaglio
PRINT_EVERY = 50
DEBUG = 0         # 1: stampe diagnostiche (solo nel simulatore)
T_GEN = 1.09      # secondi: tutti i droni sono a casa (spawn 1000 tick + 26 mosse)

S = get_world_size()
WS = Items.Weird_Substance
GOLD = Items.Gold
AMOUNT = S * 2 ** (num_unlocked(Unlocks.Mazes) - 1)
YIELD = S * S * 32
TPS = 6075
DIRS = [North, East, South, West]
DD = [1, S, -1, -S]       # delta dell'id di cella (id = x * S + y)
REV = [2, 3, 0, 1]
BW = 4                    # blocco di un drone: 4 (x) per 8 (y) -> 8 x 4 = 32 blocchi
BH = 8
NBX = S // BW


def goto(tx, ty):
	# campo aperto (prima della generazione), con wrap
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


def work(k):
	bx = k % NBX
	by = k // NBX
	x0 = bx * BW
	y0 = by * BH
	x1 = x0 + BW
	y1 = y0 + BH
	hx = x0 + BW // 2
	hy = y0 + BH // 2
	home = hx * S + hy
	gen = k == 0
	goto(hx, hy)
	if gen:
		plant(Entities.Bush)
		while get_time() < T_GEN:
			pass
		use_item(WS, AMOUNT)
		quick_print("labirinto generato", get_time())
	else:
		while measure() == None:
			pass

	# mappa: op[c] = [N, E, S, W] True se si puo' passare (celle visitate);
	# albero: up[c] = direzione verso il genitore, dep[c] = profondita' (strettamente
	# crescente lungo i genitori); front = celle scoperte ma non visitate
	op = {}
	up = {}
	dep = {}
	front = {}
	cur = [home]
	up[home] = -1
	dep[home] = 0
	state = [0, 0]   # round visti, round dell'ultima ricostruzione

	def attach(c, e, n):
		# varco c -> n scoperto
		if not n in up:
			up[n] = REV[e]
			dep[n] = dep[c] + 1
			front[n] = 1
		elif dep[n] + 1 < dep[c]:
			# scorciatoia: c si riaggancia a n (profondita' restano crescenti)
			up[c] = e
			dep[c] = dep[n] + 1

	def arrive():
		c = cur[0]
		if c in op:
			if REPROBE:
				o = op[c]
				for e in range(4):
					if not o[e]:
						if can_move(DIRS[e]):
							o[e] = True
							attach(c, e, c + DD[e])
		else:
			o = []
			for e in range(4):
				if can_move(DIRS[e]):
					o.append(True)
					attach(c, e, c + DD[e])
				else:
					o.append(False)
			op[c] = o
			if c in front:
				front.pop(c)

	def plan(a, b):
		# cammino nell'albero da a a b (lista di direzioni) per risalita
		pa = []
		pb = []
		while a != b:
			if dep[a] >= dep[b]:
				e = up[a]
				pa.append(e)
				a = a + DD[e]
			else:
				e = up[b]
				pb.append(REV[e])
				b = b + DD[e]
		i = len(pb)
		while i > 0:
			i -= 1
			pa.append(pb[i])
		return pa

	def walk(path, t):
		# segue path; si ferma (False) se il tesoro si muove (t = posizione sorvegliata)
		for e in path:
			if measure() != t:
				return False
			move(DIRS[e])
			cur[0] += DD[e]
			arrive()
		return True

	def nearest_front(tx, ty, rad):
		# frontiera che minimizza distanza dal bersaglio (+ FW * distanza da me);
		# rad > 0: solo celle con profondita' <= rad
		best = -1
		bd = 9999
		cx = cur[0] // S
		cy = cur[0] % S
		for f in front:
			if rad > 0 and dep[f] > rad:
				continue
			fx = f // S
			fy = f % S
			d = abs(fx - tx) + abs(fy - ty) + FW * (abs(fx - cx) + abs(fy - cy))
			if d < bd:
				bd = d
				best = f
		return best

	def go_to(tc, tx, ty, t):
		# raggiunge tc esplorando se serve; False se il tesoro si e' mosso
		while cur[0] != tc:
			if tc in up:
				g = tc
			else:
				g = nearest_front(tx, ty, 0)
				if g == -1:
					return False
			if not walk(plan(cur[0], g), t):
				return False
		return True

	def mine(tx, ty):
		return tx >= x0 and tx < x1 and ty >= y0 and ty < y1

	def rebuild(t):
		# BFS da casa sul grafo noto: cammini minimi che usano i varchi apertisi.
		# Interrompibile: ogni 8 celle controlla il tesoro; se e' mio abbandona.
		np = {}
		nd = {}
		np[home] = -1
		nd[home] = 0
		q = [home]
		i = 0
		while i < len(q):
			c = q[i]
			i += 1
			if i % 8 == 0:
				t2 = measure()
				if t2 != t:
					if t2 == None or mine(t2[0], t2[1]):
						return False
					t = t2
			if c in op:
				o = op[c]
				for e in range(4):
					if o[e]:
						m = c + DD[e]
						if not m in np:
							np[m] = REV[e]
							nd[m] = nd[c] + 1
							q.append(m)
		for x in np:
			up[x] = np[x]
			dep[x] = nd[x]
		return True

	def explore_step(t):
		# un passo di esplorazione da fermo: vicino inesplorato se c'e', altrimenti la
		# frontiera piu' vicina (Manhattan) entro il raggio. False se non c'e' nulla.
		c = cur[0]
		o = op[c]
		for e in range(4):
			if o[e]:
				n = c + DD[e]
				if n in front and dep[n] <= RAD:
					walk([e], t)
					return True
		g = nearest_front(c // S, c % S, RAD)
		if g == -1:
			return False
		walk(plan(c, g), t)
		return True

	def idle(t):
		if RAD > 0 and explore_step(t):
			return
		if REBUILD > 0 and state[0] - state[1] >= REBUILD:
			state[1] = state[0]
			rebuild(t)
			return
		while measure() == t:
			pass

	def wait_until(tgo, t):
		# aspetta l'istante tgo (secondi) o che il tesoro si muova
		while get_time() < tgo:
			if measure() != t:
				return

	def try_use(t):
		# sono sul tesoro: riuso, oppure harvest finale (solo se e' davvero il tesoro)
		if use_item(WS, AMOUNT):
			n = num_items(GOLD) // YIELD
			if n % PRINT_EVERY == 0:
				quick_print("riusi", n, "oro", n * YIELD, get_time())
			return True
		if can_harvest() and measure() == t and get_entity_type() == Entities.Treasure:
			harvest()
			quick_print("harvest finale", get_time(), "oro", num_items(GOLD))
			return True
		return False

	arrive()
	last = None
	tseen = 0
	while num_items(GOLD) < GOAL:
		t = measure()
		if t == None:
			break
		if t != last:
			last = t
			tseen = get_time()
			state[0] += 1
		tx = t[0]
		ty = t[1]
		tc = tx * S + ty
		c = cur[0]
		if c == tc:
			# sono sul tesoro (o sta traslocando sotto di me)
			if can_harvest():
				try_use(t)
			continue
		own = mine(tx, ty)
		if tc in up:
			if own or abs(tx - c // S) + abs(ty - c % S) <= R_MAX:
				path = plan(c, tc)
				d = len(path)
				tgo = tseen
				if d > R_GO:
					tgo = tseen + (d - R_GO) * STAG / TPS
				if get_time() >= tgo:
					if walk(path, t) and can_harvest():
						try_use(t)
				else:
					wait_until(tgo, t)
				continue
		elif own:
			tgo = tseen + W0 / TPS
			if get_time() >= tgo:
				if go_to(tc, tx, ty, t) and can_harvest():
					try_use(t)
			else:
				wait_until(tgo, t)
			continue
		idle(t)
	if DEBUG:
		quick_print("mappa: note", len(op), "frontiera", len(front), "round visti", state[0])
	if gen:
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
