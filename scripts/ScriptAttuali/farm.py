# Fattoria. Copia tutto in una finestra nuova e avvialo dal prato, non dal sottosuolo.
#
# MODO = "campo"  fieno, legna, carote, girasoli, zucche, cactus, bambu, ossa
# MODO = "riso"   solo riso: jump si puo' chiamare una volta per esecuzione
#
# Per saltare una coltura togli il nome da ORDINE.
# GIRI = 0 va avanti per sempre. OSSA_MAX = 0 riempie il campo (ossa = lunghezza^2).

MODO = "campo"
GIRI = 0
OSSA_MAX = 0
FIENO_PASSATE = 12
ACQUA = 0.5

ORDINE = [
	"fieno",
	"legna",
	"carote",
	"girasoli",
	"zucche",
	"cactus",
	"bambu",
	"ossa",
]

S = get_world_size()


def vai(tx, ty):
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


def lancia(fn):
	# Un drone per colonna. Se i droni non bastano, il principale fa il resto.
	handles = []
	fatti = []
	x = 0
	while x < S:
		h = None
		if x < S - 1 and num_drones() < max_drones():
			h = spawn_drone(fn, x)
		if h != None:
			handles.append(h)
		else:
			fatti.append(fn(x))
		x += 1
	somma = 0
	for v in fatti:
		if v != None:
			somma += v
	for h in handles:
		v = wait_for(h)
		if v != None:
			somma += v
	return somma


def annaffia():
	while get_water() < ACQUA and num_items(Items.Water) > 1000:
		if not use_item(Items.Water):
			return


def prato():
	# till() alterna suolo e prato: da suolo si torna a prato con una sola chiamata.
	if get_entity_type() != None:
		harvest()
	if get_ground_type() == Grounds.Soil:
		till()


def suolo():
	if get_entity_type() != None:
		harvest()
	if get_ground_type() == Grounds.Grassland:
		till()


def conviene(cosa, n, nome):
	# La mela non e' uno sblocco: arriva col cappello da dinosauro.
	if cosa != Entities.Apple and num_unlocked(cosa) == 0:
		quick_print(nome, "non sbloccato")
		return False
	costo = get_cost(cosa)
	if costo == None:
		return True
	for it in costo:
		if num_items(it) < costo[it] * n:
			quick_print(nome, "in pausa, manca materiale")
			return False
	return True


def fieno(x):
	vai(x, 0)
	for _ in range(S):
		prato()
		move(North)
	n = 0
	while n < FIENO_PASSATE:
		vai(x, 0)
		for _ in range(S):
			if can_harvest():
				harvest()
			move(North)
		n += 1
	return 0


def legna(x):
	vai(x, 0)
	messi = 0
	for y in range(S):
		prato()
		if (x + y) % 2 == 0:
			if plant(Entities.Tree):
				annaffia()
				messi += 1
		move(North)
	presi = 0
	while presi < messi:
		vai(x, 0)
		for y in range(S):
			if (x + y) % 2 == 0 and get_entity_type() == Entities.Tree and can_harvest():
				harvest()
				presi += 1
			elif can_harvest():
				harvest()
			move(North)
	return 0


def raccolto(ent, x):
	vai(x, 0)
	messi = 0
	for _ in range(S):
		suolo()
		if plant(ent):
			annaffia()
			messi += 1
		move(North)
	presi = 0
	while presi < messi:
		vai(x, 0)
		for _ in range(S):
			if get_entity_type() == ent and can_harvest():
				harvest()
				presi += 1
			move(North)
	return 0


def carote(x):
	return raccolto(Entities.Carrot, x)


def girasole_col(x):
	vai(x, 0)
	for _ in range(S):
		suolo()
		if plant(Entities.Sunflower):
			annaffia()
		move(North)
	while True:
		vai(x, 0)
		manca = False
		for _ in range(S):
			if get_entity_type() == Entities.Sunflower and not can_harvest():
				manca = True
			move(North)
		if not manca:
			return 0


def fai_girasoli():
	if not conviene(Entities.Sunflower, S * S, "girasoli"):
		return
	lancia(girasole_col)
	best = -1
	bx = 0
	by = 0
	for y in range(S):
		vai(0, y)
		for x in range(S):
			if get_entity_type() == Entities.Sunflower:
				p = measure()
				if p != None and p > best:
					best = p
					bx = x
					by = y
			move(East)
	vai(bx, by)
	harvest()
	for y in range(S):
		vai(0, y)
		for _ in range(S):
			if can_harvest():
				harvest()
			move(East)
	quick_print("energia", num_items(Items.Power))


def zucche(x):
	vai(x, 0)
	for _ in range(S):
		suolo()
		plant(Entities.Pumpkin)
		annaffia()
		move(North)
	while True:
		vai(x, 0)
		manca = False
		for _ in range(S):
			t = get_entity_type()
			if t == Entities.Dead_Pumpkin:
				harvest()
				if not plant(Entities.Pumpkin):
					return 0
				annaffia()
				manca = True
			elif t != Entities.Pumpkin:
				if not plant(Entities.Pumpkin):
					return 0
				annaffia()
				manca = True
			elif not can_harvest():
				manca = True
			move(North)
		if not manca:
			return 0


def fai_zucche():
	if not conviene(Entities.Pumpkin, S * S, "zucche"):
		return
	lancia(zucche)
	vai(0, 0)
	if can_harvest():
		prima = num_items(Items.Pumpkin)
		harvest()
		quick_print("zucche +", num_items(Items.Pumpkin) - prima)


def pianta_cactus(x, y):
	atteso = 0
	if S > 1:
		atteso = (9 * (x + y)) // (S + S - 2)
	if not plant(Entities.Cactus):
		return
	v = measure()
	n = 0
	while v != None and (v < atteso - 2 or v > atteso + 2) and n < 6:
		harvest()
		if get_entity_type() != None:
			return
		if not plant(Entities.Cactus):
			return
		v = measure()
		n += 1


def ordina_nord(x):
	scambi = 0
	fine = S - 1
	while fine > 0:
		vai(x, 0)
		ultimo = 0
		y = 0
		while y < fine:
			a = measure()
			b = measure(North)
			if a != None and b != None and a > b:
				swap(North)
				scambi += 1
				ultimo = y + 1
			move(North)
			y += 1
		if ultimo == 0:
			return scambi
		fine = ultimo
	return scambi


def ordina_est(y):
	scambi = 0
	fine = S - 1
	while fine > 0:
		vai(0, y)
		ultimo = 0
		x = 0
		while x < fine:
			a = measure()
			b = measure(East)
			if a != None and b != None and a > b:
				swap(East)
				scambi += 1
				ultimo = x + 1
			move(East)
			x += 1
		if ultimo == 0:
			return scambi
		fine = ultimo
	return scambi


def cactus_col(x):
	vai(x, 0)
	for y in range(S):
		suolo()
		pianta_cactus(x, y)
		move(North)
	return ordina_nord(x)


def fai_cactus():
	if not conviene(Entities.Cactus, S * S, "cactus"):
		return
	lancia(cactus_col)
	giri = 0
	while giri < S:
		scambi = lancia(ordina_est)
		scambi += lancia(ordina_nord)
		if scambi == 0:
			giri = S
		else:
			giri += 1
	vai(0, 0)
	if get_entity_type() == None:
		return
	while not can_harvest():
		pass
	prima = num_items(Items.Cactus)
	harvest()
	quick_print("cactus +", num_items(Items.Cactus) - prima)


def bambu(y):
	# Colonne pari = corridoio, dispari = bambu. Due tagli in cima, poi raccolto alto.
	if S % 2 != 0:
		return 0
	n = S // 2
	vai(0, y)
	tagli = []
	for _ in range(n):
		tagli.append(0)
	fatte = 0
	sicurezza = 0
	while fatte < n and sicurezza < n * 400:
		sicurezza += 1
		for i in range(n):
			if tagli[i] >= 3:
				move(East)
				move(East)
			else:
				m = measure(East)
				if tagli[i] >= 2:
					h = 18
				else:
					h = m
				if h != None and get_hover() != h:
					hover(h)
				move(East)
				if get_entity_type() != Entities.Bamboo:
					if get_entity_type() != None:
						harvest()
					if get_ground_type() == Grounds.Grassland:
						till()
					if plant(Entities.Bamboo):
						tagli[i] = 0
					else:
						tagli[i] = 3
						fatte += 1
				elif tagli[i] >= 2 and can_harvest():
					harvest()
					tagli[i] = 3
					fatte += 1
				elif m != None and measure() > m:
					tagli[i] += 1
				move(East)
	return 0


def fai_bambu():
	if S % 2 != 0:
		quick_print("bambu: il lato del campo deve essere pari")
		return
	if not conviene(Entities.Bamboo, (S // 2) * S, "bambu"):
		return
	prima = num_items(Items.Bamboo)
	lancia(bambu)
	quick_print("bambu +", num_items(Items.Bamboo) - prima)


def ciclo_ossa(n):
	d = []
	for _ in range(n - 1):
		d.append(East)
	for k in range(n - 1):
		if k == 0:
			for _ in range(n - 1):
				d.append(North)
		elif k % 2 == 0:
			for _ in range(n - 2):
				d.append(North)
		else:
			for _ in range(n - 2):
				d.append(South)
		d.append(West)
	for _ in range(n - 1):
		d.append(South)
	return d


def prepara(x):
	vai(x, 0)
	for _ in range(S):
		if get_ground_type() != Grounds.Soil:
			till()
		if get_entity_type() != None:
			harvest()
		move(North)
	return 0


def serpente(limite):
	m = S * S
	cyc = ciclo_ossa(S)
	px = []
	py = []
	idx = {}
	x = 0
	y = 0
	dx = {North: 0, East: 1, South: 0, West: -1}
	dy = {North: 1, East: 0, South: -1, West: 0}
	for k in range(m):
		px.append(x)
		py.append(y)
		idx[(x, y)] = k
		x += dx[cyc[k]]
		y += dy[cyc[k]]
	nb = []
	dirs = [North, East, South, West]
	for k in range(m):
		lst = []
		for d in dirs:
			nx = px[k] + dx[d]
			ny = py[k] + dy[d]
			if nx >= 0 and nx < S and ny >= 0 and ny < S:
				lst.append((d, idx[(nx, ny)]))
		nb.append(lst)

	vai(0, 0)
	change_hat(Hats.Dinosaur_Hat)
	if get_entity_type() != Entities.Apple:
		quick_print("ossa: nessuna mela, servono cactus")
		change_hat(Hats.Straw_Hat)
		return 0

	body = [0]
	occ = set()
	occ.add(0)
	h = 0
	lung = 1
	t_idx = -1
	tx = 0
	ty = 0
	while lung < limite and lung < m:
		sulla_mela = get_entity_type() == Entities.Apple
		if sulla_mela:
			tp = measure()
			if tp == None or not (tp in idx):
				t_idx = -1
			else:
				t_idx = idx[tp]
				tx = tp[0]
				ty = tp[1]
		elif t_idx == h:
			t_idx = -1

		nh = (h + 1) % m
		scelta = cyc[h]
		if t_idx >= 0:
			d_mela = (t_idx - h) % m
			if d_mela > 1:
				if lung > 1:
					d_coda = (body[0] - h) % m
				else:
					d_coda = m
				margine = 2 + 10 * lung // m
				lim = d_coda - margine
				if lim > d_mela + 1:
					lim = d_mela + 1
				best = abs(px[nh] - tx) + abs(py[nh] - ty)
				best_dd = 1
				for d, ni in nb[h]:
					dd = (ni - h) % m
					if dd > 1 and dd < lim and not (ni in occ):
						dist = abs(px[ni] - tx) + abs(py[ni] - ty)
						if dist < best or (dist == best and dd > best_dd):
							best = dist
							best_dd = dd
							scelta = d
							nh = ni
		if not move(scelta):
			mosso = False
			for d, ni in nb[h]:
				if not (ni in occ) and move(d):
					nh = ni
					mosso = True
					break
			if not mosso:
				quick_print("ossa: serpente bloccato a", lung)
				break
		h = nh
		body.append(h)
		occ.add(h)
		if sulla_mela:
			lung += 1
			if lung % 50 == 0:
				quick_print("ossa, lunghezza", lung)
			if t_idx < 0:
				break
		else:
			occ.remove(body.pop(0))
	change_hat(Hats.Straw_Hat)
	return lung


def fai_ossa():
	if S % 2 != 0:
		quick_print("ossa: il lato del campo deve essere pari")
		return
	limite = S * S
	if OSSA_MAX > 0 and OSSA_MAX < limite:
		limite = OSSA_MAX
	if not conviene(Entities.Apple, limite, "ossa"):
		return
	lancia(prepara)
	prima = num_items(Items.Bone)
	lung = serpente(limite)
	quick_print("ossa +", num_items(Items.Bone) - prima, "lunghezza", lung)


def pianta_riso():
	if plant(Entities.Rice):
		return True
	if get_ground_type() == Grounds.Dry_Rice_Terrace:
		use_item(Items.Water)
		if plant(Entities.Rice):
			return True
	n = 0
	while get_ground_type() != Grounds.Clay and n < 8:
		if get_entity_type() != None:
			harvest()
		if get_ground_type() == Grounds.Rock:
			return False
		dig()
		n += 1
	if get_ground_type() != Grounds.Clay:
		return False
	return plant(Entities.Rice)


def riso(y):
	vai(0, y)
	finite = 0
	while finite < S:
		finite = 0
		for _ in range(S):
			if can_harvest():
				harvest()
			if get_entity_type() == None:
				if not pianta_riso():
					finite += 1
			elif get_water() < ACQUA:
				use_item(Items.Water)
			move(East)
	return 0


def inventario():
	quick_print("fieno", num_items(Items.Hay), "legna", num_items(Items.Wood), "carote", num_items(Items.Carrot))
	quick_print("zucche", num_items(Items.Pumpkin), "cactus", num_items(Items.Cactus), "ossa", num_items(Items.Bone))
	quick_print("bambu", num_items(Items.Bamboo), "riso", num_items(Items.Rice), "energia", num_items(Items.Power))


def fai(nome):
	if nome == "fieno":
		lancia(fieno)
		quick_print("fieno", num_items(Items.Hay))
	elif nome == "legna":
		if conviene(Entities.Tree, S * S // 2, "legna"):
			lancia(legna)
			quick_print("legna", num_items(Items.Wood))
	elif nome == "carote":
		if conviene(Entities.Carrot, S * S, "carote"):
			lancia(carote)
			quick_print("carote", num_items(Items.Carrot))
	elif nome == "girasoli":
		fai_girasoli()
	elif nome == "zucche":
		fai_zucche()
	elif nome == "cactus":
		fai_cactus()
	elif nome == "bambu":
		fai_bambu()
	elif nome == "ossa":
		fai_ossa()


if MODO == "riso":
	if num_unlocked(Unlocks.Rice) == 0:
		quick_print("riso non sbloccato")
	else:
		quick_print("riso, parto da", num_items(Items.Rice))
		jump(Unlocks.Rice)
		lancia(riso)
		quick_print("riso totale", num_items(Items.Rice))
else:
	clear()
	quick_print("campo", S, "droni", max_drones())
	inventario()
	giro = 0
	while GIRI == 0 or giro < GIRI:
		giro += 1
		quick_print("--- giro", giro, "---")
		for nome in ORDINE:
			fai(nome)
		inventario()
