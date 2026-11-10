# Mappe del tesoro:
#   FIND_TREASURE_MAP    trovare 1 tesoro con la mappa
#   TREASURE_OPTIMAL     senza passare due volte sullo stesso blocco
#   TREASURE_MAP_FINDER  200 tesori (lo script continua a scendere e cercarne altri)
# Il percorso dato da measure() puo' incrociarsi: il gioco accetta di saltare
# avanti lungo il percorso, quindi ad ogni passo vado al punto PIU' AVANTI
# raggiungibile con una sola mossa/scavo. Cosi' non ripasso mai su un blocco.

OBIETTIVO = 200
LATO = 12           # campo piu' piccolo = scavi piu' rapidi (minimo 4)
MAX_SCAVI = 8000    # sicurezza: scavi massimi per trovare il prossimo basalto

set_world_size(LATO)
S = get_world_size()
MOSSA = {"N": North, "E": East, "S": South, "W": West}
PX = {"N": 0, "E": 1, "S": 0, "W": -1, "D": 0}
PY = {"N": 1, "E": 0, "S": -1, "W": 0, "D": 0}
PZ = {"N": 0, "E": 0, "S": 0, "W": 0, "D": -1}


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


def scava():
	if get_entity_type() == Entities.Dynamite:
		harvest()
	dig()


def trova_basalto():
	n = 0
	while n < MAX_SCAVI:
		if get_ground_type() == Grounds.Basalt:
			p = measure()
			if p != None:
				return p
		scava()
		n += 1
	return None


def segui(percorso):
	# posizioni relative del percorso (x, y, z), partenza = mappa
	P = [(0, 0, 0)]
	x = 0
	y = 0
	z = 0
	for c in percorso:
		x += PX[c]
		y += PY[c]
		z += PZ[c]
		P.append((x, y, z))
	n = len(P) - 1
	i = 0
	passi = 0
	while i < n:
		ax, ay, az = P[i]
		best = i + 1
		for j in range(n, i + 1, -1):
			bx, by, bz = P[j]
			if bz == az and abs(bx - ax) + abs(by - ay) == 1:
				best = j
				break
			if bz == az - 1 and bx == ax and by == ay:
				best = j
				break
		bx, by, bz = P[best]
		if bz < az:
			dig()
		elif bx > ax:
			move(East)
		elif bx < ax:
			move(West)
		elif by > ay:
			move(North)
		else:
			move(South)
		passi += 1
		i = best
	return passi


jump(Unlocks.Treasure_Map)
trovate = 0
while trovate < OBIETTIVO:
	p = trova_basalto()
	if p == None:
		quick_print("STOP: basalto non trovato dopo", MAX_SCAVI, "scavi, z =", get_pos_z())
		break
	mx, my = p
	vai(mx, my)
	n = 0
	while get_ground_type() != Grounds.Treasure_Map and n < 60:
		scava()
		n += 1
	if get_ground_type() != Grounds.Treasure_Map:
		quick_print("STOP: mappa non raggiunta a", mx, my, "terreno", get_ground_type())
		break
	percorso = measure()
	passi = segui(percorso)
	if get_entity_type() == Entities.Underground_Treasure:
		g = num_items(Items.Gold)
		harvest()
		trovate += 1
		quick_print("tesoro", trovate, "oro +", num_items(Items.Gold) - g, "z", get_pos_z(), "passi", passi, "su", len(percorso))
	else:
		quick_print("STOP: fine percorso senza tesoro: entita'", get_entity_type(), "terreno", get_ground_type())
		break
		