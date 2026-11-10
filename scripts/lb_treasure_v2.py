# Classifica Treasure_Map (115000 oro, 1 drone, 8x8). v2 dell'8 nov 2026 (v1 in lb_treasure_v1.py: 27.936 s).
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
#   Codice cella: q = livello*64 + y*8 + x, livello 0 = mappa.
# v2: dal fondo del pozzo (sul basalto) si va alla mappa con move + dig: ogni dig abbassa le 4
#   colonne vicine fino a un blocco sopra la quota del drone, quindi ogni casella del tragitto
#   costa 1 scavo e sulla mappa ne restano 2, invece di ~7 della v1 (dig(direzione) e' vietato:
#   NoParams). Ricerca del percorso srotolata (meno tick).

GOAL = 115000
BASALT = Grounds.Basalt
TMAP = Grounds.Treasure_Map
GOLD = Items.Gold
DL = {"E": 1, "W": -1, "N": 8, "S": -8, "D": 64}
DIRS = [East, West, North, South]

# vicini con wrap per ogni cella 0..63 (ordine E, W, N, S)
NBQ = []
for p in range(64):
	x = p % 8
	y = p // 8
	NBQ.append([(x + 1) % 8 + y * 8, (x + 7) % 8 + y * 8, x + ((y + 1) % 8) * 8, x + ((y + 7) % 8) * 8])


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


def walk(prev, n):
	ks = []
	v = prev[n]
	while v >= 0:
		ks.append(v % 4)
		v = prev[v // 4]
	j = len(ks) - 1
	while j >= 0:
		move(DIRS[ks[j]])
		j -= 1
	return n


def route(S, q, base):
	# BFS sulle celle del percorso del livello: cella piu' vicina con percorso anche sotto.
	# Esegue le mosse e restituisce la cella d'arrivo.
	prev = {q: -1}
	fr = [q]
	i = 0
	while True:
		c = fr[i]
		i += 1
		nb = NBQ[c - base]
		c4 = c * 4
		n = nb[0] + base
		if n in S and n not in prev:
			prev[n] = c4
			if n + 64 in S:
				return walk(prev, n)
			fr.append(n)
		n = nb[1] + base
		if n in S and n not in prev:
			prev[n] = c4 + 1
			if n + 64 in S:
				return walk(prev, n)
			fr.append(n)
		n = nb[2] + base
		if n in S and n not in prev:
			prev[n] = c4 + 2
			if n + 64 in S:
				return walk(prev, n)
			fr.append(n)
		n = nb[3] + base
		if n in S and n not in prev:
			prev[n] = c4 + 3
			if n + 64 in S:
				return walk(prev, n)
			fr.append(n)


n_tes = 0
t_start = get_time()
while True:
	# --- pozzo fino al basalto, poi tunnel fino alla mappa
	t0 = get_time()
	d1 = 0
	while get_ground_type() != BASALT:
		dig()
		d1 += 1
	m = measure()
	mv = tunnel_to(m[0], m[1])
	d2 = 0
	while get_ground_type() != TMAP:
		dig()
		d2 += 1
	s = measure()
	t1 = get_time()
	k0 = get_tick_count()
	# --- lettura del percorso
	q = m[1] * 8 + m[0]
	S = {}
	for c in s:
		q += DL[c]
		S[q] = 1
	goal = q
	k1 = get_tick_count()
	# --- discesa lungo il percorso
	dig()
	q = m[1] * 8 + m[0] + 64
	base = 64
	while q != goal:
		if q + 64 not in S:
			q = route(S, q, base)
		dig()
		q += 64
		base += 64
	harvest()
	n_tes += 1
	g = num_items(GOLD)
	quick_print("tes", n_tes, "len", len(s), "oro", g, "scavi basalto", d1, "mosse", mv, "scavi mappa", d2,
		"t discesa", t1 - t0, "tick lettura", k1 - k0, "t percorso", get_time() - t1, "t tot", get_time() - t_start)
	if g >= GOAL:
		break
