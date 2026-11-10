# Classifica Cactus v16: hybrid reroll + shaker, due fasi con wait_for.
# (send/receive NON sono API giocatore — v15 non parte.)
GOAL = 33554432
K_REROLL = 4
SLACK = 2

S = get_world_size()
CACTUS = Entities.Cactus
DIAG = 2 * S - 1


def home():
	for _ in range(get_pos_x()):
		move(West)
	for _ in range(get_pos_y()):
		move(South)


def shaker(fwd, back):
	lo = 0
	hi = S - 1
	while lo < hi:
		last = lo
		cur = measure()
		k = lo
		while k < hi:
			nxt = measure(fwd)
			if cur > nxt:
				swap(fwd)
				last = k
			else:
				cur = nxt
			move(fwd)
			k += 1
		for _ in range(hi - last):
			move(back)
		hi = last
		if lo >= hi:
			return
		last = hi
		cur = measure()
		k = hi
		while k > lo:
			nxt = measure(back)
			if cur < nxt:
				swap(back)
				last = k
			else:
				cur = nxt
			move(back)
			k -= 1
		for _ in range(last - lo):
			move(fwd)
		lo = last


def column_worker():
	x = get_pos_x()
	for _ in range(S):
		till()
		plant(CACTUS)
		move(North)

	for _ in range(K_REROLL):
		bad = 0
		ready = True
		for y in range(S):
			t = ((x + y) * 10) // DIAG
			m = measure()
			if not can_harvest():
				ready = False
			elif m < t - SLACK or m > t + SLACK:
				till()
				till()
				plant(CACTUS)
				bad += 1
			move(North)
		if bad == 0 and ready:
			break

	shaker(North, South)


def row_worker():
	shaker(East, West)


def run_across(task, step_dir):
	handles = []
	for _ in range(S - 1):
		h = spawn_drone(task)
		if h != None:
			handles.append(h)
		move(step_dir)
	task()
	for h in handles:
		wait_for(h)


clear()
run_across(column_worker, East)
home()
run_across(row_worker, North)
while not can_harvest():
	pass
harvest()
