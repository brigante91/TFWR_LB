# Classifica Pumpkins: 2e8 zucche, 32 droni. v2 del 6 nov 2026 (mai inviata finora).
# Classifica Steam: #1 5:43, #10 5:59, #25 6:14. Stima di questo script: ~5:00-5:20.
#
# Regole (Pumpkin.cs, PumpkinController.cs, asset): crescita 2 s / (1 + 4*acqua); al termine
# della crescita 20% di probabilita' di morire (dead_pumpkin: harvest 200 e ripianta). Le zucche
# cresciute adiacenti si fondono nel quadrato piu' grande; la resa di un quadrato di lato L e'
# L^2 * min(L, 6) * 512: il 32x32 vale 3.145.728 -> servono 64 raccolti completi.
# Il raccolto toglie tutto il gruppo e si puo' fare da qualunque cella del gruppo.
#
# Il vecchio script rispawnava i 31 droni a ogni ciclo (catena di spawn + goto alla colonna:
# ~1.5 s x 64 cicli = ~100 s). Qui i worker sono persistenti: ognuno riempie la sua colonna e
# poi aspetta che la cella sotto di lui torni vuota (= il main ha raccolto). Il main riempie la
# colonna 0, aspetta MARGIN secondi e raccoglie: se una colonna e' in ritardo il quadrato e' 31
# di lato (resa -6%) e le celle avanzate restano per il ciclo dopo. Il worker aspetta a y in
# 1..30, righe sempre comprese in un quadrato >= 31 che contiene la colonna 0.
# Acqua: 25.6/s di accumulo, 4096 per portare tutto a 1.0: priorita' alle celle ripiantate dopo
# una morte (sono il percorso critico), 1 unita' alle altre quando c'e' scorta.
#a
# Barriera (test del 6 nov: raccogliere a tempo da' un quadrato 1x1 = 512 zucche e poi il campo
# resta frammentato per sempre): i gruppi sono QUADRATI e tutte le zucche di un gruppo hanno lo
# stesso measure() (quello della cella in basso a sinistra del quadrato). Dalla colonna 0,
# measure() == measure(West) (la cella (31, y) grazie al wrap) vuol dire che (0, y) e (31, y)
# stanno nello stesso quadrato, cioe' nel 32x32: solo allora il main raccoglie.
GOAL = 200000000

S = get_world_size()
PUMPKIN = Entities.Pumpkin
DEAD = Entities.Dead_Pumpkin
SOIL = Grounds.Soil
WATER = Items.Water


def goto_x(x):
	if x <= S // 2:
		for _ in range(x):
			move(East)
	else:
		for _ in range(S - x):
			move(West)


def step(n):
	# n = spostamento verso nord (mod S); sceglie il verso piu' corto
	n = n % S
	if n <= S // 2:
		for _ in range(n):
			move(North)
	else:
		for _ in range(S - n):
			move(South)


def water_to(target):
	# porta l'acqua della cella a target (0.25 per unita'); se il serbatoio non basta, meno
	w = get_water()
	need = (target - w) * 4
	n = need // 1
	if n < need:
		n += 1
	while n > 0:
		if use_item(WATER, n):
			return
		n -= 1


def replant():
	# ripiantata dopo una morte: e' sul percorso critico del ciclo (ogni generazione di morti
	# costa una crescita intera), quindi ha la priorita' sull'acqua
	plant(PUMPKIN)
	tank = num_items(WATER)
	if tank >= 60:
		water_to(1.0)
	elif tank >= 2:
		water_to(0.5)


def plant_fresh():
	# prima generazione: usa solo il surplus del serbatoio; l'acqua resta sulla cella
	# (decade ~1%/s), quindi ciclo dopo ciclo il campo si avvicina a 1.0
	plant(PUMPKIN)
	tank = num_items(WATER)
	if tank >= 400:
		water_to(1.0)
	elif tank >= 150:
		water_to(0.5)
	elif tank >= 30:
		water_to(0.25)


def fill(first):
	# riempie la colonna partendo dalla cella corrente (posizioni relative 0..S-1 verso nord)
	pending = []
	for i in range(S):
		if first and get_ground_type() != SOIL:
			till()
		t = get_entity_type()
		if t == DEAD:
			harvest()
			t = None
		if t == None:
			plant_fresh()
			pending.append(i)
		elif not can_harvest():
			pending.append(i)
		move(North)
	pos = 0
	while len(pending) > 0:
		left = []
		for i in pending:
			step(i - pos)
			pos = i
			t = get_entity_type()
			if t == DEAD:
				harvest()
				replant()
				left.append(i)
			elif t == None:
				# una cella piantata sparisce solo se il main ha raccolto il 32x32:
				# la colonna era completa, il ciclo e' finito
				return pos
			elif not can_harvest():
				if len(pending) <= 3:
					# poche celle: conviene aspettare qui invece di fare la spola
					while True:
						t = get_entity_type()
						if t == DEAD:
							harvest()
							replant()
						elif t == None:
							return pos
						elif can_harvest():
							break
				else:
					left.append(i)
		pending = left
	return pos


def worker(x):
	def fn():
		goto_x(x)
		first = True
		while True:
			fill(first)
			first = False
			while get_entity_type() != None:
				pass
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


clear()
spawn_drone(spawn_range_task(1, S))
first = True
c = 0
while True:
	fill(first)
	first = False
	t_fill = get_time()
	while measure() != measure(West):
		pass
	t_ok = get_time()
	before = num_items(Items.Pumpkin)
	harvest()
	c += 1
	quick_print("ciclo", c, "colonna finita a", t_fill, "campo completo a", t_ok, "raccolto", num_items(Items.Pumpkin) - before, "acqua", num_items(WATER))
	if num_items(Items.Pumpkin) >= GOAL:
		clear()
		break
