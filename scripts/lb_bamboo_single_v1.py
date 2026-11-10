# Classifica Bamboo Single (8x8, 1 drone, obiettivo 2.5e7 bambu', resa 128 * pezzi^2 per taglio).
# Regole (decompiled_nov6 Bamboo.cs): il bambu' cresce di 1 blocco ogni 1/(1+4*acqua) s e si ferma ai fiori
# (f1, f2, F). Entrare in una cella a quota h taglia la pianta a h: a quota fiore-1 si toglie il fiore
# (1 pezzo) e la pianta riprende subito; a quota 1 si raccolgono F-1 pezzi e la pianta riparte da 2
# con gli STESSI fiori. Il drone non puo' scendere sopra un bambu' piu' alto della quota voluta.
# Schema: ciclo chiuso di R*8 celle con (0,0) vuota (ascensore, unico punto dove si cambia quota).
# Ogni pianta viene ritirata finche' f1 == T1 (measure subito dopo la semina) e f2 - f1 == D
# (controllato dopo il primo fiore). Poi ogni ciclo sono 3 passate a quota costante, solo move():
# fiore 1 a quota T1-1, fiore 2 a quota T1+D-1, taglio a quota 1 (resa (F-1)^2).
# Simulatore: haysim/bamboo/prog.py (R=6, T1=5, D=4: ~201 s).

S = get_world_size()
GOAL = 25000000
BAMBOO = Entities.Bamboo
WATER = Items.Water
ITEM = Items.Bamboo

T1 = 5          # altezza voluta del primo fiore
D = 4           # distanza voluta tra primo e secondo fiore
M1 = T1 - 1     # quota per il primo fiore (= measure() di una pianta nuova buona)
M2 = T1 + D - 1 # quota per il secondo fiore
R = 6           # righe usate (pari): ciclo di R*S celle
W_FILL = 1.0    # riempimento dell'acqua ...
W_LOW = 0.5     # ... quando scende sotto questo livello
MARGIN = 0.05   # secondi di sicurezza sulle attese di crescita
ACT = 0.031     # stima per difetto della durata di una move (s)
LOG = True


def make_dirs():
	xs = []
	ys = []
	for x in range(S):
		xs.append(x)
		ys.append(0)
	for y in range(1, R):
		for i in range(S - 1):
			if y % 2 == 1:
				xs.append(S - 1 - i)
			else:
				xs.append(1 + i)
			ys.append(y)
	for i in range(R - 1):
		xs.append(0)
		ys.append(R - 1 - i)
	n = len(xs)
	dirs = []
	for i in range(n):
		j = (i + 1) % n
		if xs[j] == xs[i] + 1:
			dirs.append(East)
		elif xs[j] == xs[i] - 1:
			dirs.append(West)
		elif ys[j] == ys[i] + 1:
			dirs.append(North)
		else:
			dirs.append(South)
	return dirs


DIRS = make_dirs()
N = len(DIRS)
CELLS = N - 1                     # celle col bambu' (l'ascensore no)
INNER = []                        # le mosse che entrano in una cella col bambu'
for i in range(CELLS):
	INNER.append(DIRS[i])
LAST = DIRS[N - 1]                # rientro nell'ascensore
SWEEP = CELLS * ACT


def water_to(tgt, low):
	# ritorna l'acqua della cella dopo l'eventuale innaffiatura
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


def main():
	t_start = get_time()
	# semina
	wmin = 1.0
	for d in INNER:
		move(d)
		if get_ground_type() != Grounds.Soil:
			till()
		new_plant()
		w = water_to(W_FILL, W_FILL)
		if w < wmin:
			wmin = w
	move(LAST)
	prev_end = get_time()
	need1 = M1                    # blocchi di crescita prima del primo fiore (dalla semina)
	cycles = 0
	rerolls = 0
	waited = 0
	while True:
		# 1) primo fiore a quota M1; controllo del secondo fiore
		t = prev_end + need1 / (1 + 4 * wmin) + MARGIN - SWEEP
		if get_time() < t:
			waited += t - get_time()
			wait_until(t)
		need1 = T1 - 2
		hover(M1)
		for d in INNER:
			move(d)
			m = measure()
			if m != M2 and m != M1:
				# secondo fiore sbagliato: nuova pianta (verra' tagliata a quota 1 e ripartira')
				harvest()
				new_plant()
				hover(M1)
				rerolls += 1
		move(LAST)
		prev_end = get_time()
		# 2) secondo fiore a quota M2
		t = prev_end + D / (1 + 4 * wmin) + MARGIN - SWEEP
		if get_time() < t:
			waited += t - get_time()
			wait_until(t)
		hover(M2)
		emax = 3
		for d in INNER:
			move(d)
			e = measure() - M2
			if e > emax:
				emax = e
		if emax > 5:
			emax = 5
		move(LAST)
		prev_end = get_time()
		# 3) taglio a quota 1 + acqua
		t = prev_end + emax / (1 + 4 * wmin) + MARGIN - SWEEP
		if get_time() < t:
			waited += t - get_time()
			wait_until(t)
		hover(1)
		wm = 1.0
		for d in INNER:
			move(d)
			if num_items(ITEM) >= GOAL:
				if LOG:
					quick_print("cicli", cycles, "ritiri", rerolls, "attese", waited, "tempo", get_time() - t_start)
				clear()
				return
			w = water_to(W_FILL, W_LOW)
			if w < wm:
				wm = w
		cycles += 1
		move(LAST)
		prev_end = get_time()
		wmin = wm * 0.97


main()
