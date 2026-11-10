# Classifica Rice (2e6 riso, tutti i droni) e Rice_Single (1e5, 1 drone, 8x8). v7 dell'8 nov 2026.
# Lo stesso file va bene per tutte e due: obiettivo, droni e percorso si scelgono da soli.
# v1 (lb_rice_v1.py): 3:19.882 in gioco su Rice. v2 (lb_rice_v2.py): 3:20.652, alcuni droni fermi.
# #1 1:51.9.
# v3 = v2 + diagnostica in output + celle troppo dure saltate (le abbassano i vicini col
# trascinamento, che non guarda la durezza). Sospetto per i droni fermi: chiazze di roccia
# (HardPatchesFeature, durezza 2 + 0.2*profondita') e strati senza argilla.
# v3 in gioco 2:06.618 (con H_SKIP 6 e 3 uguale). Stampe: strato ~15.5 s (A2 ~4 s, B+A1 ~11 s),
# attese di crescita ~5 s a strato nei primi 40 s (acqua 0) e ~1 s dopo, con 400-1400 acqua
# ferme in magazzino: le soglie 0.07/0.1 erano troppo basse.
# v4: acqua alla semina portata a W_RICH (0.5) quando in magazzino ce n'e' piu' di RICH; quando
# scarseggia va alle prime FIRST celle di ogni passata (le uniche con poco tempo di crescita,
# perche' le attese si accumulano e le celle dopo hanno piu' margine).
# v4 in gioco 2:05.689 (#5 con 2:06.492): attese quasi azzerate, ma ora conta lo scavo (~100 scavi
# per drone a strato, ~8 s su 15).
# v5: A1 non scava piu' la terrazza secca. Quando in A2 la cella prima scende, la terrazza secca
# (gia' raccolta) crolla da sola insieme alla roccia sotto (stabilita' 3), e le celle dopo vengono
# trascinate: ~1 scavo a cella in meno per strato. Sim: Rice 115 -> 103 s, Single 181 -> 151 s.
# v5 in gioco: Rice 1:57.01, Rice_Single 2:38.258 (#6; #1 2:19.3).
# v6 (solo single): 100k = 782 raccolti = 6 strati da 128 + 14. La v5 per gli ultimi 14 faceva
# scendere e piantare tutte le 64 celle. Ora nell'ultimo strato pianta solo le celle che servono,
# le annaffia a 1.0 (crescita <= 1.44 s) e torna indietro raccogliendole.
# Stampe v6 single: ~2 s d'attesa crescita a strato e 3300 acqua inutilizzate a fine run.
# v7 (solo single): alla semina, se la cella ha meno di S_LOW d'acqua la riempie a 1.0 in una
# azione. L'acqua resta nella colonna dopo gli scavi e cala ~1%/s: ogni cella si annaffia circa una
# volta in tutta la run, e con >= 0.15 la crescita massima e' 4.5 s, meno di una passata.
#
# Mondo della classifica (ClayFeature, decompilato del 6 nov): ogni strato di 16 blocchi ha terra
# (durezza 1, stabilita' 1) sopra, poi SOLO 2 blocchi d'argilla, poi roccia (durezza 2, stabilita' 3)
# fino alla fine dello strato. Quindi ogni 2 raccolti per cella bisogna scendere di ~14 blocchi.
# Roccia e terra sono "autodestroyWhenDugBeside": quando un drone scava la sua cella, i 4 vicini
# con roccia/terra in cima vengono abbassati fino al livello di prima della cella scavata
# (trascinamento gratis); argilla, terrazza e terrazza secca no. In piu' una cella crolla se un
# vicino (4 direzioni) e' piu' profondo di oltre 3 blocchi, e il crollo distrugge la pianta.
# La v1 scavava 14 blocchi in una cella accanto a celle col riso: crollavano e si perdeva quasi
# tutto il riso (simulato: ~14000 piante distrutte su ~16000).
#
# v2, tre passate per strato, in ordine su ogni cella del percorso:
#   A2: scava fino all'argilla e pianta (la prima cella scava ~14, le altre ~1 grazie al
#       trascinamento delle celle gia' scese: tutte le vicine sono gia' a roccia scoperta);
#   B:  raccoglie il riso del 1o blocco d'argilla, scava la terrazza secca, pianta sul 2o;
#   A1: raccoglie il riso del 2o blocco e scava la terrazza secca: resta la roccia scoperta.
# Nessuna cella scende mentre accanto c'e' riso dello strato vecchio, quindi niente crolli.
# Acqua (solo multi): quando si deve aspettare la crescita, e alla semina se la cella e' sotto 0.1.
# Simulatore (scratch, mondo e crolli trascritti dal decompilato): Rice 158 s (v1) -> 122 s,
# Rice_Single 238 s -> 180 s, 0 piante perse. Il sim dava 158 s alla v1 che in gioco ha fatto
# 200 s: aspettarsi tempi reali piu' alti in proporzione.
# A obiettivo raggiunto il drone che se ne accorge chiama clear() (ferma tutti gli altri).

S = get_world_size()
D = min(max_drones(), S)
if max_drones() <= 1:
	GOAL = 100000
else:
	GOAL = 2000000

RICE = Entities.Rice
CLAY = Grounds.Clay
WATER = Items.Water
RICE_ITEM = Items.Rice

DRY = Grounds.Dry_Rice_Terrace

W_TH = 0.25      # in attesa della crescita: porta l'acqua della cella a questo livello
W_PRE = 0.1      # alla semina (solo multi): livello minimo
FIRST = 8        # le prime FIRST celle di ogni passata ...
W_FIRST = 0.25   # ... alla semina vanno portate a questo livello
RICH = 100       # se in magazzino c'e' piu' acqua di cosi' ...
W_RICH = 0.5     # ... alla semina si porta la cella a questo livello
S_LOW = 0.15     # single: sotto questo livello alla semina la cella si riempie a 1.0
MAX_DIG = 24     # sicurezza: scavi massimi per trovare l'argilla
H_SKIP = 6       # durezza oltre la quale non si scava (dig = durezza / 25.6 s)
LOG = 3          # stampe per drone sui casi strani


def cols_of(d):
	return (d * S) // D, ((d + 1) * S) // D


def make_path(d):
	# ciclo sulle colonne [x0, x1): dirs[k] = mossa dopo il passo k, work[k] = cella da lavorare
	x0, x1 = cols_of(d)
	k = x1 - x0
	dirs = []
	work = []
	if k == 1:
		for _ in range(S):
			dirs.append(North)
			work.append(True)
		return dirs, work
	# serpentina: colonne pari verso Nord, dispari verso Sud
	for c in range(k):
		for _ in range(S - 1):
			if c % 2 == 0:
				dirs.append(North)
			else:
				dirs.append(South)
			work.append(True)
		dirs.append(East)
		work.append(True)
	# ritorno a (x0, 0) dopo l'ultima cella
	if k == S and k % 2 == 0:
		return dirs, work      # l'ultima East fa il giro (wrap) fino a (x0, 0)
	dirs[len(dirs) - 1] = West
	for _ in range(k - 2):
		dirs.append(West)
		work.append(False)
	if k % 2 == 1:
		dirs.append(North)     # finiti in alto (y = S-1): wrap a y = 0
		work.append(False)
	return dirs, work


def goto(tx, ty):
	x = get_pos_x()
	y = get_pos_y()
	dx = (tx - x) % S
	if dx <= S // 2:
		for _ in range(dx):
			move(East)
	else:
		for _ in range(S - dx):
			move(West)
	dy = (ty - y) % S
	if dy <= S // 2:
		for _ in range(dy):
			move(North)
	else:
		for _ in range(S - dy):
			move(South)


def water_to(target):
	# porta l'acqua della cella a target (0.25 a unita') con UNA azione, nei limiti del magazzino
	need = (target - get_water()) * 4
	if need <= 0:
		return
	n = need // 1
	if n < need:
		n += 1
	tank = num_items(WATER)
	if n > tank:
		n = tank // 1
	if n >= 1:
		use_item(WATER, n)


def pre_water(k):
	tgt = W_PRE
	if k < FIRST:
		tgt = W_FIRST
	if num_items(WATER) > RICH:
		tgt = W_RICH
	if get_water() < tgt:
		water_to(tgt)


def back(d):
	if d == North:
		return South
	if d == South:
		return North
	if d == East:
		return West
	return East


def final_round(dirs, lim, stat):
	# ultimo strato (solo single): scendi e pianta le prime lim celle, poi torna indietro raccogliendo
	for k in range(lim):
		m = 0
		while get_ground_type() != CLAY and m < MAX_DIG:
			if get_hardness() > H_SKIP:
				break
			dig()
			m += 1
		plant(RICE)
		water_to(1.0)
		move(dirs[k])
	for kk in range(lim):
		k = lim - 1 - kk
		move(back(dirs[k]))
		if get_entity_type() == RICE:
			wait_grown(stat)
			harvest()
			if num_items(RICE_ITEM) >= GOAL:
				clear()
				return True
	return False


def wait_grown(stat):
	if not can_harvest():
		t0 = get_time()
		water_to(W_TH)
		while not can_harvest():
			pass
		stat[2] += get_time() - t0


def worker(d):
	def fn():
		x0, x1 = cols_of(d)
		dirs, work = make_path(d)
		n = len(dirs)
		pre = (x1 - x0) * S < 40
		single = D == 1
		stat = [0, 0, 0]   # scavi in A2, massimo in una cella, secondi d'attesa crescita
		log = [0]
		goto(x0, 0)
		while True:
			# A2: scendi all'argilla dello strato nuovo e pianta
			t_pass = get_time()
			if D == 1:
				need = (GOAL - num_items(RICE_ITEM)) / 128
				lim = need // 1
				if lim < need:
					lim += 1
				if lim + 2 < n:
					if final_round(dirs, lim + 2, stat):
						return
			for k in range(n):
				if work[k]:
					m = 0
					while get_ground_type() != CLAY and m < MAX_DIG:
						h = get_hardness()
						if h > H_SKIP:
							if log[0] < LOG:
								log[0] += 1
								quick_print("drone", d, "durezza", h, get_ground_type(), "x", get_pos_x(), "y", get_pos_y(), "z", get_pos_z(), "t", get_time())
							break
						dig()
						m += 1
					stat[0] += m
					if m > stat[1]:
						stat[1] = m
					if m >= MAX_DIG and log[0] < LOG:
						log[0] += 1
						quick_print("drone", d, "niente argilla dopo", m, "scavi", get_ground_type(), "z", get_pos_z(), "t", get_time())
					if plant(RICE):
						if pre:
							pre_water(k)
						elif single and get_water() < S_LOW:
							water_to(1.0)
				move(dirs[k])
			if d == 0 or d == D // 2:
				quick_print("drone", d, "A2 t", t_pass, "->", get_time(), "z", get_pos_z(), "scavi", stat[0], "max", stat[1], "attesa", stat[2], "riso", num_items(RICE_ITEM), "acqua", num_items(WATER))
				stat[0] = 0
				stat[1] = 0
				stat[2] = 0
			# B: raccogli il 1o blocco, togli la terrazza secca, pianta sul 2o
			for k in range(n):
				if work[k]:
					if get_entity_type() == RICE:
						wait_grown(stat)
						harvest()
						if num_items(RICE_ITEM) >= GOAL:
							clear()
							return
						dig()
					if get_ground_type() == CLAY:
						if plant(RICE):
							if pre:
								pre_water(k)
							elif single and get_water() < S_LOW:
								water_to(1.0)
				move(dirs[k])
			# A1: raccogli il 2o blocco (la terrazza secca la toglie il crollo in A2)
			for k in range(n):
				if work[k]:
					if get_entity_type() == RICE:
						wait_grown(stat)
						harvest()
						if num_items(RICE_ITEM) >= GOAL:
							clear()
							return
				move(dirs[k])
	return fn


def spawn_range(lo, hi):
	while hi - lo > 1:
		mid = (lo + hi) // 2
		spawn_drone(spawn_range_task(mid, hi))
		hi = mid
	worker(lo)()


def spawn_range_task(lo, hi):
	def fn():
		spawn_range(lo, hi)
	return fn


spawn_range(0, D)
