EXTRA = 100000000      # ossa da produrre
MARGIN_MIN = 2         # margine dalla coda con serpente corto
MARGIN_MAX = 12        # margine dalla coda con serpente quasi pieno
SHORTCUT_MAX_FILL = 1.0  # 1.0 = scorciatoie sempre (con la regola della coda)
REPORT_EVERY = 100     # stampa ogni N mele

S = get_world_size()
M = S * S
APPLE = Entities.Apple
DIRS = [North, East, South, West]
DX = {North: 0, East: 1, South: 0, West: -1}
DY = {North: 1, East: 0, South: -1, West: 0}


def build_cycle(N):
	d = []
	for i in range(N - 1):
		d.append(East)
	for k in range(N - 1):
		if k == 0:
			for i in range(N - 1):
				d.append(North)
		elif k % 2 == 0:
			for i in range(N - 2):
				d.append(North)
		else:
			for i in range(N - 2):
				d.append(South)
		d.append(West)
	for i in range(N - 1):
		d.append(South)
	return d


CYC = build_cycle(S)
POS = []
IDX = {}
x = 0
y = 0
for k in range(M):
	POS.append((x, y))
	IDX[(x, y)] = k
	x += DX[CYC[k]]
	y += DY[CYC[k]]

# per ogni indice: vicini come (direzione, cella, indice della cella)
NB = []
for k in range(M):
	px, py = POS[k]
	lst = []
	for d in DIRS:
		nx = px + DX[d]
		ny = py + DY[d]
		if nx >= 0 and nx < S and ny >= 0 and ny < S:
			lst.append((d, (nx, ny), IDX[(nx, ny)]))
	NB.append(lst)


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


def prep_column(cx):
	goto(cx, 0)
	for _ in range(S):
		if get_ground_type() != Grounds.Soil:
			till()
		if get_entity_type() != None:
			harvest()
		move(North)


def make_prep(cx):
	def fn():
		prep_column(cx)
	return fn


def prep_field():
	handles = []
	for cx in range(1, S):
		h = spawn_drone(make_prep(cx))
		if h != None:
			handles.append(h)
	prep_column(0)
	for h in handles:
		wait_for(h)


PX = []
PY = []
for k in range(M):
	PX.append(POS[k][0])
	PY.append(POS[k][1])


def run_snake():
	goto(0, 0)
	change_hat(Hats.Dinosaur_Hat)
	if get_entity_type() != APPLE:
		quick_print("Nessuna mela: servono cactus. Costo mela:", get_cost(APPLE), "cactus:", num_items(Items.Cactus))
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
	steps = 0
	tick0 = get_tick_count()
	time0 = get_time()

	while L < M:
		on_apple = get_entity_type() == APPLE
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
				# mossa di default: avanti di uno sul percorso
				best_dist = abs(PX[nh] - tx) + abs(PY[nh] - ty)
				best_dd = 1
				for d, n, ni in NB[h]:
					dd = (ni - h) % M
					if dd > 1 and dd < lim and not (ni in occ):
						dist = abs(PX[ni] - tx) + abs(PY[ni] - ty)
						if dist < best_dist or (dist == best_dist and dd > best_dd):
							best_dist = dist
							best_dd = dd
							choice = d
							nh = ni

		if not move(choice):
			moved = False
			for d, n, ni in NB[h]:
				if not (ni in occ) and move(d):
					nh = ni
					moved = True
					break
			if not moved:
				quick_print("serpente bloccato a lunghezza", L)
				break

		steps += 1
		h = nh
		body.append(h)
		occ.add(h)
		if on_apple:
			L += 1
			if L % REPORT_EVERY == 0:
				quick_print("L", L, "passi", steps, "passi/mela", steps // L, "tick/passo", (get_tick_count() - tick0) // steps, "secondi", get_time() - time0)
			if t_idx < 0:
				quick_print("mele finite (cactus?) a lunghezza", L)
				break
		else:
			occ.remove(body.pop(0))

	change_hat(Hats.Straw_Hat)
	return L

if S % 2 != 0:
	quick_print("Il lato del campo deve essere pari, ora e'", S)
else:
	TARGET = num_items(Items.Bone) + EXTRA
	quick_print("campo", S, "ossa", num_items(Items.Bone), "cactus", num_items(Items.Cactus), "costo mela", get_cost(APPLE))
	clear()
	while num_items(Items.Bone) < TARGET:
		t0 = get_time()
		b0 = num_items(Items.Bone)
		prep_field()
		L = run_snake()
		quick_print("SERPENTE: lunghezza", L, "ossa +", num_items(Items.Bone) - b0, "totale", num_items(Items.Bone), "secondi", get_time() - t0)
		if L < 2:
			break