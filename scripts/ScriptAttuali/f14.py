# MAZE_MASTER (2 milioni di oro in 1 minuto) e BIG_GOLD_FARMER (100 milioni totali).
# Invece di un labirinto 32x32 esplorato a caso: 16 labirinti 8x8, uno per drone.
# Ogni drone usa measure() per sapere dov'e' il tesoro e va dritto col
# percorso piu' breve (BFS), imparando i muri man mano. Poi riusa il
# labirinto (use_item sul tesoro = oro subito + tesoro spostato) fino al limite.

EXTRA = 100000000   # oro da produrre prima di fermarsi
R = 8               # lato di ogni labirinto (32 / R deve essere intero)

S = get_world_size()
WS = Items.Weird_Substance
AMOUNT = R * 2 ** (num_unlocked(Unlocks.Mazes) - 1)
TARGET = num_items(Items.Gold) + EXTRA
DIRS = [North, East, South, West]
DX = {North: 0, East: 1, South: 0, West: -1}
DY = {North: 1, East: 0, South: -1, West: 0}
OPP = {North: South, East: West, South: North, West: East}


def vai(tx, ty):
	while get_pos_x() < tx:
		move(East)
	while get_pos_x() > tx:
		move(West)
	while get_pos_y() < ty:
		move(North)
	while get_pos_y() > ty:
		move(South)


def bfs(x0, y0, muri, tx, ty):
	sx = get_pos_x()
	sy = get_pos_y()
	prec = {}
	prec[(sx, sy)] = None
	coda = [(sx, sy)]
	i = 0
	while i < len(coda):
		c = coda[i]
		i += 1
		if c == (tx, ty):
			break
		cx, cy = c
		for d in DIRS:
			nx = cx + DX[d]
			ny = cy + DY[d]
			if nx < x0 or ny < y0 or nx >= x0 + R or ny >= y0 + R:
				continue
			if (cx, cy, d) in muri:
				continue
			n = (nx, ny)
			if not (n in prec):
				prec[n] = (c, d)
				coda.append(n)
	inv = []
	c = (tx, ty)
	while prec[c] != None:
		p, d = prec[c]
		inv.append(d)
		c = p
	strada = []
	for k in range(len(inv)):
		strada.append(inv[len(inv) - 1 - k])
	return strada


def raggiungi(x0, y0, muri, tx, ty):
	# muri sconosciuti = aperti; se una mossa fallisce segno il muro e ricalcolo
	while get_pos_x() != tx or get_pos_y() != ty:
		for d in bfs(x0, y0, muri, tx, ty):
			x = get_pos_x()
			y = get_pos_y()
			if not move(d):
				muri.add((x, y, d))
				muri.add((x + DX[d], y + DY[d], OPP[d]))
				break


def lavora(x0, y0):
	bx = x0 + R // 2
	by = y0 + R // 2
	vai(bx, by)
	while num_items(Items.Gold) < TARGET:
		vai(bx, by)
		if get_entity_type() != None:
			harvest()
		plant(Entities.Bush)
		if not use_item(WS, AMOUNT):
			quick_print("Sostanza strana finita")
			return
		muri = set()
		while num_items(Items.Gold) < TARGET:
			t = measure()
			if t == None:
				break
			tx, ty = t
			raggiungi(x0, y0, muri, tx, ty)
			if get_entity_type() != Entities.Treasure:
				continue
			if not use_item(WS, AMOUNT):
				harvest()   # limite di riusi raggiunto: incasso e nuovo labirinto
				break
			attesa = 0
			while measure() == t and attesa < 300:
				attesa += 1  # aspetto che il tesoro si sposti


clear()
quick_print("oro", num_items(Items.Gold), "sostanza", num_items(WS), "per labirinto", AMOUNT)
N = S // R
for k in range(1, N * N):
	spawn_drone(lavora, R * (k % N), R * (k // N))
lavora(0, 0)
quick_print("fine, oro", num_items(Items.Gold))
