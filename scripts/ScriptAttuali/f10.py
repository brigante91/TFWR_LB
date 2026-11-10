# DYNAMITE_DISPOSAL_SPECIALIST - Con Riduzione a Catena dei Vincoli (3+ numeri)
S = get_world_size()
N = S * S
MAXSCAVI = 60


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


NB = []
for i in range(N):
	x = i % S
	y = i // S
	l = []
	for dy in [-1, 0, 1]:
		for dx in [-1, 0, 1]:
			if dx != 0 or dy != 0:
				nx = x + dx
				ny = y + dy
				if nx >= 0 and nx < S and ny >= 0 and ny < S:
					l.append(ny * S + nx)
	NB.append(l)

K = []
M = []
SIC = []
for i in range(N):
	K.append(-1)
	M.append(False)
	SIC.append(False)


def compito_scendi(y, zstop):
	def fn():
		goto(0, y)
		for _ in range(S):
			n = 0
			while n < MAXSCAVI and get_pos_z() > zstop:
				dig()
				n += 1
			move(East)
	return fn


def fase1(zstop):
	droni = []
	for y in range(1, S):
		d = spawn_drone(compito_scendi(y, zstop))
		if d != None:
			droni.append(d)
	compito_scendi(0, zstop)()
	for d in droni:
		wait_for(d)


def compito_lista(celle, zl):
	def fn():
		out = []
		for i in celle:
			goto(i % S, i // S)
			if get_ground_type() == Grounds.Dynamite and get_pos_z() == zl:
				dig()
			v = measure()
			if v == None:
				v = -1
			out.append([i, v])
		return out
	return fn


def giro(celle, zl):
	md = max_drones()
	tot = len(celle)
	per = (tot + md - 1) // md
	if per < 1:
		per = 1

	gruppi = []
	g = []
	for i in celle:
		g.append(i)
		if len(g) == per:
			gruppi.append(g)
			g = []
	if len(g) > 0:
		gruppi.append(g)

	droni = []
	ris = []
	for k in range(1, len(gruppi)):
		d = spawn_drone(compito_lista(gruppi[k], zl))
		if d == None:
			ris.append(compito_lista(gruppi[k], zl)())
		else:
			droni.append(d)
	ris.append(compito_lista(gruppi[0], zl)())
	for d in droni:
		ris.append(wait_for(d))
	for r in ris:
		for p in r:
			if p[1] >= 0:
				K[p[0]] = p[1]


def vincoli():
	V = []
	for i in range(N):
		if K[i] >= 0:
			u = []
			f = 0
			for j in NB[i]:
				if M[j]:
					f += 1
				elif K[j] < 0 and not SIC[j]:
					u.append(j)
			if len(u) > 0:
				V.append([u, K[i] - f])
	return V


def deduci():
	while True:
		cambiato = False
		V = vincoli()

		# Anello interno: riduce anche i vincoli A sottoinsieme di B (B = B - A)
		# permettendo deduzioni a catena su 3 o 4 numeri!
		ridotto = True
		while ridotto:
			ridotto = False

			# 1. Regole base su V (inclusi i nuovi vincoli ridotti!)
			for v in V:
				u = v[0]
				r = v[1]
				if len(u) > 0:
					if r <= 0:
						for j in u:
							if not SIC[j]:
								SIC[j] = True
								cambiato = True
						v[0] = []
					elif r == len(u):
						for j in u:
							if not M[j]:
								M[j] = True
								cambiato = True
						v[0] = []

			if cambiato:
				break

			# Indicizza in quali vincoli compare ogni cella
			dove = {}
			for k in range(len(V)):
				for j in V[k][0]:
					if not (j in dove):
						dove[j] = []
					dove[j].append(k)

			# 2. Confronto coppie (Sottoinsiemi con riduzione + Intersezione 1-2)
			for a in range(len(V)):
				ua = V[a][0]
				if len(ua) == 0:
					continue
				ra = V[a][1]
				visti = {}
				for j in ua:
					for b in dove[j]:
						if b != a and not (b in visti):
							visti[b] = True
							ub = V[b][0]
							if len(ub) == 0:
								continue
							rb = V[b][1]

							diffAB = []
							for c in ua:
								in_b = False
								for cb in ub:
									if c == cb:
										in_b = True
										break
								if not in_b:
									diffAB.append(c)

							diffBA = []
							for cb in ub:
								in_a = False
								for c in ua:
									if cb == c:
										in_a = True
										break
								if not in_a:
									diffBA.append(cb)

							# Caso 1: A e' sottoinsieme stretto di B -> Riduci B in (B - A, rB - rA)!
							if len(diffAB) == 0 and len(diffBA) > 0:
								V[b][0] = diffBA
								V[b][1] = rb - ra
								ridotto = True
								break

							# Caso 2: Regola generale di intersezione (es. 1-2, 1-2-1)
							if len(diffAB) > 0 or len(diffBA) > 0:
								if ra - rb == len(diffAB):
									for c in diffAB:
										if not M[c]:
											M[c] = True
											cambiato = True
									for c in diffBA:
										if not SIC[c]:
											SIC[c] = True
											cambiato = True

					if ridotto or cambiato:
						break
				if ridotto or cambiato:
					break

		if not cambiato:
			break


def indovina(mine_totali):
	V = vincoli()
	rischio_max = {}

	for v in V:
		p = v[1] / len(v[0])
		for j in v[0]:
			if not (j in rischio_max) or p > rischio_max[j]:
				rischio_max[j] = p

	ignote = 0
	segnate = 0
	for i in range(N):
		if M[i]:
			segnate += 1
		elif K[i] < 0 and not SIC[i]:
			ignote += 1
	if ignote == 0:
		return -1

	rem = mine_totali - segnate
	if rem < 1:
		rem = 1
	dens = rem / ignote

	best = -1
	bp = 999.0
	for i in range(N):
		if K[i] < 0 and not M[i] and not SIC[i]:
			if i in rischio_max:
				p = rischio_max[i]
			else:
				p = dens
				x = i % S
				y = i // S
				if (x == 0 or x == S - 1) and (y == 0 or y == S - 1):
					p = p * 0.85
				elif x == 0 or x == S - 1 or y == 0 or y == S - 1:
					p = p * 0.93

			if p < bp:
				bp = p
				best = i

	if best >= 0:
		SIC[best] = True
		quick_print("indovino", best % S, best // S, "rischio", bp)
	return best


# --- AVVIO ---
if get_pos_z() > -590:
	quick_print("Sei a z", get_pos_z(), ": troppo in alto. Esegui f19 finche' stampa z <= -600.")
	while True:
		pass

n = 0
while get_ground_type() != Grounds.Dynamite and n < 60:
	dig()
	n += 1

ZL = get_pos_z()
quick_print("strato a z", ZL, "terreno", get_ground_type(), "campo", S)
MINE = (N * 17 + 50) // 100
fase1(ZL)

# Apre subito tutte le 9 celle centrali sicure
cx = S // 2
cy = S // 2
celle = []
for dy in [-1, 0, 1]:
	for dx in [-1, 0, 1]:
		idx = (cy + dy) * S + (cx + dx)
		SIC[idx] = True
		celle.append(idx)

esploso = False
while True:
	giro(celle, ZL)
	for i in celle:
		if K[i] < 0:
			quick_print("misura fallita in", i % S, i // S, "- esploso!")
			esploso = True
	if esploso:
		break

	deduci()

	celle = []
	for k in range(N):
		if SIC[k] and K[k] < 0 and not M[k]:
			celle.append(k)

	if len(celle) == 0:
		g = indovina(MINE)
		if g < 0:
			break
		celle = [g]

noti = 0
mine = 0
for i in range(N):
	if K[i] >= 0:
		noti += 1
	if M[i]:
		mine += 1
quick_print("FINE: celle misurate", noti, "mine segnate", mine, "esploso", esploso, "dinamite", num_items(Items.Dynamite))