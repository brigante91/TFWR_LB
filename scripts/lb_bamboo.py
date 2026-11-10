# Classifica Bamboo (32x32, 32 droni, obiettivo 5e8 bambu', resa 128 * pezzi^2 per taglio).
# Stesse regole e stesso schema di lb_bamboo_single.py, un drone per riga:
# la cella x=0 di ogni riga resta vuota (ascensore), le altre 31 hanno il bambu'; ogni passata e'
# un giro di 32 move(East) a quota costante. Ogni pianta viene ritirata finche' f1 == T1 e f2 - f1 == D;
# poi ogni ciclo: fiore 1 a quota T1-1, fiore 2 a quota T1+D-1, taglio a quota 1 (resa (F-1)^2).
# Qui comanda l'acqua (serbatoio 25.6/s per 1024 celle): ogni passata di taglio alza tutta la riga
# di W_RISE alla volta, cosi' l'acqua resta uniforme e le attese (calcolate sulla cella piu' secca) brevi.
# Simulatore: haysim/bamboo/prog.py mode=2 (W_TOP 0.8, W_RISE 0.1: ~211 s per riga media).

S = get_world_size()
GOAL = 500000000
BAMBOO = Entities.Bamboo
WATER = Items.Water
ITEM = Items.Bamboo

T1 = 5          # altezza voluta del primo fiore
D = 4           # distanza voluta tra primo e secondo fiore
M1 = T1 - 1
M2 = T1 + D - 1
W_SEED = 0.5    # acqua alla semina (se c'e')
W_TOP = 0.8     # livello massimo a cui si porta l'acqua
W_RISE = 0.1    # a ogni passata si porta la riga a (minimo della riga + W_RISE)
MARGIN = 0.05
ACT = 0.031
SWEEP = (S - 1) * ACT


def water_to(tgt, low):
	w = get_water()
	if w < low:
		k = (tgt - w) * 4 // 1
		if k < 1:
			k = 1
		tank = num_items(WATER) // 1
		if k > tank:
			k = tank
		if k >= 1:
			use_item(WATER, k)
			w = w + k * 0.25
	return w


def new_plant():
	plant(BAMBOO)
	while measure() != M1:
		harvest()
		plant(BAMBOO)


def wait_until(t):
	while get_time() < t:
		pass


def row():
	inner = S - 1
	# semina (il drone parte sull'ascensore x=0)
	wmin = 1.0
	for _ in range(inner):
		move(East)
		if get_ground_type() != Grounds.Soil:
			till()
		new_plant()
		w = water_to(W_SEED, W_SEED)
		if w < wmin:
			wmin = w
	move(East)
	prev_end = get_time()
	need1 = M1
	while True:
		# 1) primo fiore a quota M1; controllo del secondo
		wait_until(prev_end + need1 / (1 + 4 * wmin) + MARGIN - SWEEP)
		need1 = T1 - 2
		hover(M1)
		for _ in range(inner):
			move(East)
			m = measure()
			if m != M2 and m != M1:
				harvest()
				new_plant()
				hover(M1)
		move(East)
		prev_end = get_time()
		# 2) secondo fiore a quota M2
		wait_until(prev_end + D / (1 + 4 * wmin) + MARGIN - SWEEP)
		hover(M2)
		emax = 3
		for _ in range(inner):
			move(East)
			e = measure() - M2
			if e > emax:
				emax = e
		if emax > 5:
			emax = 5
		move(East)
		prev_end = get_time()
		# 3) taglio a quota 1 + acqua uniforme
		wait_until(prev_end + emax / (1 + 4 * wmin) + MARGIN - SWEEP)
		hover(1)
		tgt = wmin / 0.97 + W_RISE
		if tgt > W_TOP:
			tgt = W_TOP
		wm = 1.0
		for _ in range(inner):
			move(East)
			if num_items(ITEM) >= GOAL:
				clear()
				return
			w = water_to(tgt, tgt)
			if w < wm:
				wm = w
		move(East)
		prev_end = get_time()
		wmin = wm * 0.97


for _ in range(S - 1):
	spawn_drone(row)
	move(North)
row()
