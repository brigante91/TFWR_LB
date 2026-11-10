# Classifica Treasure_Map (115000 oro, 1 drone, 8x8). v1 dell'8 nov 2026.
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


def go_to(tx, ty):
	dx = (tx - get_pos_x()) % 8
	dy = (ty - get_pos_y()) % 8
	n = 0
	if dx <= 4:
		for _ in range(dx):
			move(East)
		n += dx
	else:
		for _ in range(8 - dx):
			move(West)
		n += 8 - dx
	if dy <= 4:
		for _ in range(dy):
			move(North)
		n += dy
	else:
		for _ in range(8 - dy):
			move(South)
		n += 8 - dy
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
		for k in range(4):
			n = nb[k] + base
			if n in S and n not in prev:
				prev[n] = c * 4 + k
				if n + 64 in S:
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
				fr.append(n)


n_tes = 0
t_start = get_time()
while True:
	# --- discesa al basalto e alla mappa
	t0 = get_time()
	d1 = 0
	while get_ground_type() != BASALT:
		dig()
		d1 += 1
	m = measure()
	mv = go_to(m[0], m[1])
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
	nm = 0
	while q != goal:
		if q + 64 not in S:
			q2 = route(S, q, base)
			q = q2
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
