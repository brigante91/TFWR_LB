# Classifica Treasure_Map (115000 oro, 1 drone, 8x8). v4 dell'8 nov 2026 (v1 27.936, v2 ~27, v3 26.0 s).
# #1 Steam 19.434 s, #5 24.4 s.
#
# Regole (TreasureMapController.cs, decompiled_nov6):
# - ogni strato da 16 ha un blocco di basalto a tutto campo; measure() sul basalto da' (x, y)
#   della mappa, che sta subito sotto. measure() sulla mappa genera il percorso (stringa NESWD).
# - oro = 16 x lunghezza del percorso (treasure_map livello 5: profondita' 9, resa 2^4).
# - il gioco controlla solo che il drone stia su una cella del percorso (FindLastIndex), non
#   l'ordine: si puo' camminare tra celle del percorso dello stesso livello e scavare (D) da
#   qualunque cella che ha percorso anche nel livello sotto. ~13 mosse a tesoro invece di ~780.
# - il percorso non passa mai dal bordo (niente wrap), quindi la posizione e' q += delta.
#   Codice cella: q = livello*100 + y*10 + x, livello 0 = mappa (v1-v3: livello*64 + y*8 + x).
# v2: dal fondo del pozzo (sul basalto) si va alla mappa con move + dig: ogni dig abbassa le 4
#   colonne vicine fino a un blocco sopra la quota del drone, quindi ogni casella del tragitto
#   costa 1 scavo e sulla mappa ne restano 2, invece di ~7 della v1 (dig(direzione) e' vietato:
#   NoParams). Ricerca del percorso srotolata (meno tick).
# v3: la mappa del prossimo strato si prevede. Il seme dello strato k e' seme0 + k e System.Random
#   (Knuth, lineare nel seme) da' a ogni estrazione un passo costante: x_k = floor(4*frac(u + k*b))+2
#   con 4b = CX (x) e CY (y) (haysim/treasure/mappred.py: giusta ~69% dal 2o strato, ~95% dal 7o).
#   Si tiene per x e y l'intervallo della fase compatibile con le mappe gia' viste. Il pozzo si
#   scava nella colonna C che costa meno tra il tesoro, la mappa prevista e i suoi 4 vicini:
#   mosse con wrap + scavi in piu' per colonne poco profonde (livello piu' basso del percorso
#   precedente in C) + tunnel da C alla mappa. Se la previsione sbaglia: measure e tunnel.
# v4: codice cella q = livello*100 + y*10 + x. Nella BFS i vicini sono q+-1 e q+-10 senza tabelle:
#   le celle fuori campo (x = 8, x = -1, ...) non sono mai nel percorso, quindi niente controlli
#   di bordo. ~14 tick per nodo invece di ~24 (perde il passaggio dal bordo: +0.7 mosse a tesoro).

GOAL = 115000
BASALT = Grounds.Basalt
TMAP = Grounds.Treasure_Map
GOLD = Items.Gold
DL = {"E": 1, "W": -1, "N": 10, "S": -10, "D": 100}
DIRD = {1: East, -1: West, 10: North, -10: South}
DIRS = [East, West, North, South]
CX = 4 * 458365203 / 2147483647
CY = 4 * 969558243 / 2147483647
DG = 2.4   # costo di uno scavo in mosse

def tunnel_to(tx, ty):
	# il drone e' sul basalto. dig() abbassa sempre le 4 colonne vicine fino a un blocco sopra
	# la nuova quota (autodestroyWhenDugBeside, ClearGroundWithCaveins): la casella successiva
	# e' quindi gia' a basalto-1. A ogni passo: move, poi un dig (terra -> basalto) che abbassa
	# la prossima. Sulla mappa l'ultimo dig non si fa (ci pensa il ciclo "fino alla mappa").
	# Niente wrap (i crolli non attraversano il bordo; la mappa sta in [2, 6)).
	dx = tx - get_pos_x()
	dy = ty - get_pos_y()
	dxx = East
	if dx < 0:
		dxx = West
		dx = -dx
	dyy = North
	if dy < 0:
		dyy = South
		dy = -dy
	n = dx + dy
	k = n
	for _ in range(dx):
		move(dxx)
		k -= 1
		if k > 0:
			dig()
	for _ in range(dy):
		move(dyy)
		k -= 1
		if k > 0:
			dig()
	return n


def go_to(tx, ty):
	dx = (tx - get_pos_x()) % 8
	dy = (ty - get_pos_y()) % 8
	if dx <= 4:
		for _ in range(dx):
			move(East)
	else:
		for _ in range(8 - dx):
			move(West)
	if dy <= 4:
		for _ in range(dy):
			move(North)
	else:
		for _ in range(8 - dy):
			move(South)


def wdist(a, b):
	d = (a - b) % 8
	if d > 4:
		d = 8 - d
	return d


def fit(lo, hi, k, c, v):
	# restringe l'intervallo [lo, hi) della fase allo strato 0 con l'osservazione v allo strato k
	a = (v - 2) - k * c
	if lo < 0:
		a = a % 4
		return [a, a + 1]
	a -= 4 * ((a - lo + 2) // 4)
	if a > lo:
		lo = a
	if a + 1 < hi:
		hi = a + 1
	return [lo, hi]


def pred(lo, hi, k, c):
	m = (lo + hi) / 2 + k * c
	return (m % 4) // 1 + 2


def depth_lv(S, p):
	# livello piu' profondo (1..8) in cui la colonna p era percorso; 0 se mai
	lv = 8
	while lv > 0:
		if p + lv * 100 in S:
			return lv
		lv -= 1
	return 0


def walk(P, n, q):
	ks = []
	while n != q:
		c = P[n]
		ks.append(DIRD[n - c])
		n = c
	j = len(ks) - 1
	while j >= 0:
		move(ks[j])
		j -= 1


def route(S, q):
	# BFS sulle celle del percorso del livello: cella piu' vicina con percorso anche sotto.
	P = {q: q}
	fr = [q]
	i = 0
	while True:
		c = fr[i]
		i += 1
		n = c + 1
		if n in S and n not in P:
			P[n] = c
			if n + 100 in S:
				walk(P, n, q)
				return n
			fr.append(n)
		n = c - 1
		if n in S and n not in P:
			P[n] = c
			if n + 100 in S:
				walk(P, n, q)
				return n
			fr.append(n)
		n = c + 10
		if n in S and n not in P:
			P[n] = c
			if n + 100 in S:
				walk(P, n, q)
				return n
			fr.append(n)
		n = c - 10
		if n in S and n not in P:
			P[n] = c
			if n + 100 in S:
				walk(P, n, q)
				return n
			fr.append(n)


n_tes = 0
t_start = get_time()
X = [-1, -1]
Y = [-1, -1]
S = {}
gx = 0
gy = 0
first = True
while True:
	t0 = get_time()
	# --- scelta della colonna del pozzo
	if first:
		px = 3
		py = 3
		cx = 3
		cy = 3
		first = False
	else:
		px = pred(X[0], X[1], n_tes, CX)
		py = pred(Y[0], Y[1], n_tes, CY)
		cx = gx
		cy = gy
		best = (abs(px - gx) + abs(py - gy)) * (1 + DG)
		for dd in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]:
			ax = px + dd[0]
			ay = py + dd[1]
			if ax >= 0 and ax < 8 and ay >= 0 and ay < 8:
				cost = wdist(ax, gx) + wdist(ay, gy) + DG * (9 - depth_lv(S, ay * 10 + ax)) + (abs(dd[0]) + abs(dd[1])) * (1 + DG)
				if cost < best:
					best = cost
					cx = ax
					cy = ay
	go_to(cx, cy)
	# --- pozzo fino al basalto, poi tunnel fino alla mappa
	d1 = 0
	while get_ground_type() != BASALT:
		dig()
		d1 += 1
	m = measure()
	X = fit(X[0], X[1], n_tes, CX, m[0])
	Y = fit(Y[0], Y[1], n_tes, CY, m[1])
	mv = tunnel_to(m[0], m[1])
	d2 = 0
	while get_ground_type() != TMAP:
		dig()
		d2 += 1
	s = measure()
	t1 = get_time()
	k0 = get_tick_count()
	# --- lettura del percorso
	q = m[1] * 10 + m[0]
	S = {}
	for c in s:
		q += DL[c]
		S[q] = 1
	goal = q
	k1 = get_tick_count()
	# --- discesa lungo il percorso
	dig()
	q = m[1] * 10 + m[0] + 100
	while q != goal:
		if q + 100 not in S:
			q = route(S, q)
		dig()
		q += 100
	harvest()
	gx = goal % 10
	gy = (goal // 10) % 10
	n_tes += 1
	g = num_items(GOLD)
	quick_print("tes", n_tes, "mappa", m, "prev", px, py, "pozzo", cx, cy, "len", len(s), "oro", g, "scavi basalto", d1, "mosse", mv, "scavi mappa", d2,
		"t discesa", t1 - t0, "tick lettura", k1 - k0, "t percorso", get_time() - t1, "t tot", get_time() - t_start)
	if g >= GOAL:
		break
