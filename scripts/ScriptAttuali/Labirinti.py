EXTRA = 100000000   # oro da produrre
MAX_REUSE = 50      # quante volte spostare il tesoro prima di raccogliere

S = get_world_size()
WS = Items.Weird_Substance
HEDGE = Entities.Hedge
TREASURE = Entities.Treasure
AMOUNT = S * 2 ** (num_unlocked(Unlocks.Mazes) - 1)
TARGET = num_items(Items.Gold) + EXTRA
START_WS = num_items(WS)

DIRS = [North, East, South, West]
DX = {North: 0, East: 1, South: 0, West: -1}
DY = {North: 1, East: 0, South: -1, West: 0}
OPP = {North: South, East: West, South: North, West: East}


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


def on_treasure():
	used = (START_WS - num_items(WS)) // AMOUNT
	if used % (MAX_REUSE + 1) != 0:
		use_item(WS, AMOUNT)  # sposta il tesoro
	else:
		g = num_items(Items.Gold)
		harvest()
		quick_print("oro +", num_items(Items.Gold) - g, "totale", num_items(Items.Gold), "sostanza", num_items(WS))
		plant(Entities.Bush)
		use_item(WS, AMOUNT)  # nuovo labirinto


def explorer(k):
	order = []
	for i in range(4):
		order.append(DIRS[(i + k) % 4])  # ogni drone esplora in un ordine diverso

	# aspetta che il labirinto esista
	while get_entity_type() != HEDGE and get_entity_type() != TREASURE:
		pass

	last_ws = num_items(WS)
	visited = set()
	visited.add((get_pos_x(), get_pos_y()))
	stack = []

	while num_items(Items.Gold) < TARGET:
		if get_entity_type() == TREASURE:
			on_treasure()
		ws = num_items(WS)
		if ws != last_ws:
			# il tesoro si e' spostato (o labirinto nuovo): ricomincia la ricerca da qui
			last_ws = ws
			visited = set()
			visited.add((get_pos_x(), get_pos_y()))
			stack = []
		x = get_pos_x()
		y = get_pos_y()
		moved = False
		for d in order:
			p = ((x + DX[d]) % S, (y + DY[d]) % S)
			if p not in visited and can_move(d):
				move(d)
				visited.add(p)
				stack.append(d)
				moved = True
				break
		if not moved:
			if len(stack) > 0:
				move(OPP[stack.pop()])
			else:
				visited = set()
				visited.add((x, y))


def make_explorer(k, tx, ty):
	def fn():
		goto(tx, ty)
		explorer(k)
	return fn


clear()
quick_print("lato", S, "sostanza per labirinto", AMOUNT, "disponibile", START_WS, "oro", num_items(Items.Gold))

# 32 posti su una griglia 8x4 (passo 4 in x, 8 in y)
for k in range(1, max_drones()):
	spawn_drone(make_explorer(k, 4 * (k % 8) + 2, 8 * (k // 8) + 4))

goto(2, 4)
for i in range(3000):  # lascia arrivare gli altri drone
	pass
plant(Entities.Bush)
use_item(WS, AMOUNT)
explorer(0)