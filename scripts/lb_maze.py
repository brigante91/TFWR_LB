# Classifica Maze: 9.863.168 oro = un labirinto 32x32 riusato 300 volte. NON ANCORA PROVATO.
# 32 drone sparsi nel labirinto; measure() da' la posizione del tesoro, ogni drone
# esplora puntando verso di essa. Il conteggio dei riusi passa dall'inventario di sostanza.
GOAL = 9863168
MAX_REUSE = 300

S = get_world_size()
WS = Items.Weird_Substance
HEDGE = Entities.Hedge
TREASURE = Entities.Treasure
AMOUNT = S * 2 ** (num_unlocked(Unlocks.Mazes) - 1)
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
		harvest()
		if num_items(Items.Gold) < GOAL:
			plant(Entities.Bush)
			use_item(WS, AMOUNT)  # labirinto nuovo


def explorer():
	while get_entity_type() != HEDGE and get_entity_type() != TREASURE:
		if num_items(Items.Gold) >= GOAL:
			return

	last_ws = -1
	visited = set()
	stack = []
	tx = 0
	ty = 0
	while num_items(Items.Gold) < GOAL:
		if get_entity_type() == TREASURE:
			on_treasure()
		ws = num_items(WS)
		x = get_pos_x()
		y = get_pos_y()
		if ws != last_ws:
			# tesoro spostato o labirinto nuovo: ricomincio puntando al tesoro
			last_ws = ws
			visited = set()
			visited.add((x, y))
			stack = []
			t = measure()
			if t != None:
				tx = t[0]
				ty = t[1]
		best = None
		best_p = None
		best_dist = 99999
		for d in DIRS:
			p = (x + DX[d], y + DY[d])
			if not (p in visited):
				dist = abs(p[0] - tx) + abs(p[1] - ty)
				if dist < best_dist and can_move(d):
					best = d
					best_p = p
					best_dist = dist
		if best != None:
			move(best)
			visited.add(best_p)
			stack.append(best)
		elif len(stack) > 0:
			move(OPP[stack.pop()])
		else:
			visited = set()
			visited.add((x, y))


def make_explorer(tx, ty):
	def fn():
		goto(tx, ty)
		explorer()
	return fn


clear()
for k in range(1, max_drones()):
	spawn_drone(make_explorer(4 * (k % 8) + 2, 8 * (k // 8) + 4))
goto(2, 4)
for i in range(3000):
	pass
plant(Entities.Bush)
use_item(WS, AMOUNT)
explorer()
