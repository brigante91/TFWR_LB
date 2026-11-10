# DYNAMITE_DISPOSAL_SPECIALIST - Architettura Ibrida:
#  1. Droni Autonomi di Quadrante/Settore: ogni drone scava E deduce localmente nel suo settore
#     continuando a scavare sul posto senza ripassare dal principale!
#  2. Sincronizzazione Globale: quando i settori si fermano, il principale unisce tutte le scoperte
#     e applica Sottoinsiemi, Intersezioni (1-2) e Prova per Assurdo su tutta la mappa 32x32!

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


#Ogni drone lavora sul suo quadrante/settore e DEDUCE DA SOLO sul posto!
def compito_quadrante(celle_iniziali, zl, x_min, x_max, y_min, y_max):
	def fn():
		out_k = []
		out_m = []
		coda = []
		in_coda = {}
		for c in celle_iniziali:
			coda.append(c)
			in_coda[c] = True

		# Area di competenza allargata di 2 celle per non fare viaggi lunghi fuori quadrante
		idx = 0
		while idx < len(coda):
			# Ordina: scegli nella coda la cella piu' vicina alla posizione attuale del drone!
			px = get_pos_x()
			py = get_pos_y()
			best_k = idx
			best_d = 999
			for k in range(idx, len(coda)):
				c = coda[k]
				cx = c % S
				cy = c // S
				dx = abs(cx - px)
				dy = abs(cy - py)
				if dx + dy < best_d:
					best_d = dx + dy
					best_k = k
			# Scambia con idx
			c = coda[best_k]
			coda[best_k] = coda[idx]
			coda[idx] = c
			idx += 1

			goto(c % S, c // S)
			if get_ground_type() == Grounds.Dynamite and get_pos_z() == zl:
				dig()
			v = measure()
			if v == None:
				v = -1
			K[c] = v
			SIC[c] = True
			out_k.append([c, v])
			if v < 0:
				# Esploso! Interrompi subito
				return [out_k, out_m]

			# --- MINI-SOLVER LOCALE DEL DRONE SUL SUO QUADRANTE ---
			# Controlla i numeri nel raggio di 2 celle intorno alla cella appena scavata
			controlla = [c]
			for j in NB[c]:
				if K[j] >= 0:
					controlla.append(j)
				for j2 in NB[j]:
					if K[j2] >= 0:
						controlla.append(j2)

			loop_loc = True
			while loop_loc:
				loop_loc = False
				for num_c in controlla:
					kv = K[num_c]
					if kv >= 0:
						ign = []
						m_cnt = 0
						for v_nb in NB[num_c]:
							if M[v_nb]:
								m_cnt += 1
							elif K[v_nb] < 0 and not SIC[v_nb]:
								ign.append(v_nb)
						rem = kv - m_cnt
						if len(ign) > 0:
							if rem == 0:
								# Tutte sicure! Se sono nel mio quadrante le scavo SUBITO io!
								for s_c in ign:
									SIC[s_c] = True
									sx = s_c % S
									sy = s_c // S
									if sx >= x_min and sx <= x_max and sy >= y_min and sy <= y_max:
										if not (s_c in in_coda) and len(coda) < 45:
											in_coda[s_c] = True
											coda.append(s_c)
								loop_loc = True
							elif rem == len(ign):
								# Tutte mine! Segnale subito per sbloccare altri numeri vicini!
								for m_c in ign:
									if not M[m_c]:
										M[m_c] = True
										out_m.append(m_c)
								loop_loc = True

		return [out_k, out_m]
	return fn


def giro_quadranti(celle, zl):
	# Divide la mappa 32x32 in 16 quadranti 8x8 (4x4 griglia)
	# Ogni quadrante con celle sicure da scavare riceve un drone dedicato!
	quads = {}
	for c in celle:
		x = c % S
		y = c // S
		qx = x // 8
		qy = y // 8
		qid = qy * 4 + qx
		if not (qid in quads):
			quads[qid] = []
		quads[qid].append(c)

	lista_q = []
	for qid in quads:
		qx = qid % 4
		qy = qid // 4
		# Confini del quadrante 8x8 con 2 celle di margine elastico
		xmin = qx * 8 - 2
		xmax = qx * 8 + 9
		ymin = qy * 8 - 2
		ymax = qy * 8 + 9
		lista_q.append([quads[qid], xmin, xmax, ymin, ymax])

	# Se ci sono poche celle, splitta ulteriormente per usare piu' droni possibili
	if len(lista_q) == 1 and len(celle) > 1 and len(celle) <= max_drones():
		lista_q = []
		for c in celle:
			x = c % S
			y = c // S
			lista_q.append([[c], x - 4, x + 4, y - 4, y + 4])

	droni = []
	ris = []
	for k in range(1, len(lista_q)):
		q = lista_q[k]
		d = spawn_drone(compito_quadrante(q[0], zl, q[1], q[2], q[3], q[4]))
		if d == None:
			ris.append(compito_quadrante(q[0], zl, q[1], q[2], q[3], q[4])())
		else:
			droni.append(d)

	q0 = lista_q[0]
	ris.append(compito_quadrante(q0[0], zl, q0[1], q0[2], q0[3], q0[4])())
	for d in droni:
		ris.append(wait_for(d))

	# Unisce nella memoria globale tutte le celle scavate e le mine scoperte dai quadranti!
	for r in ris:
		out_k = r[0]
		out_m = r[1]
		for p in out_k:
			c = p[0]
			v = p[1]
			if v >= 0:
				K[c] = v
				SIC[c] = True
				if v == 0:
					for j in NB[c]:
						if not M[j]:
							SIC[j] = True
		for m_c in out_m:
			M[m_c] = True


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


def porta_ad_assurdo(V, target, ipotesi_mina):
	m_temp = {}
	s_temp = {}
	if ipotesi_mina:
		m_temp[target] = True
	else:
		s_temp[target] = True

	loop = True
	while loop:
		loop = False
		for v in V:
			u = v[0]
			r = v[1]
			m_cnt = 0
			ignote = []
			for j in u:
				if j in m_temp:
					m_cnt += 1
				elif not (j in s_temp):
					ignote.append(j)
			rem = r - m_cnt
			if rem < 0 or rem > len(ignote):
				return True
			if len(ignote) > 0:
				if rem == 0:
					for j in ignote:
						s_temp[j] = True
					loop = True
				elif rem == len(ignote):
					for j in ignote:
						m_temp[j] = True
					loop = True
	return False


def deduci():
	while True:
		cambiato = False
		V = vincoli()

		ridotto = True
		while ridotto:
			ridotto = False
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

			dove = {}
			for k in range(len(V)):
				for j in V[k][0]:
					if not (j in dove):
						dove[j] = []
					dove[j].append(k)

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

							if len(diffAB) == 0 and len(diffBA) > 0:
								V[b][0] = diffBA
								V[b][1] = rb - ra
								ridotto = True
								break

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

		if cambiato:
			continue

		V = vincoli()
		fronte = {}
		for v in V:
			for j in v[0]:
				fronte[j] = True

		for cand in fronte:
			if porta_ad_assurdo(V, cand, True):
				SIC[cand] = True
				cambiato = True
			elif porta_ad_assurdo(V, cand, False):
				M[cand] = True
				cambiato = True

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

# Partenza: le 9 celle sicure al centro vengono divise nei 4 quadranti centrali!
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
	giro_quadranti(celle, ZL)
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