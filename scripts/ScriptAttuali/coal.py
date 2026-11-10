# DLC: scavo profondo continuo a strati (niente clear): ogni 16 strati
# ci sono nuove vene di quarzo e ferro. Il principale stampa i progressi.
S = get_world_size()


def riga():
	while True:
		for _ in range(S):
			dig()
			move(East)


clear()
for _ in range(S - 1):
	spawn_drone(riga)
	move(North)
while True:
	for _ in range(S):
		dig()
		move(East)
	quick_print("z", get_pos_z(), "carbone", num_items(Items.Coal), "ferro", num_items(Items.Iron), "quarzo", num_items(Items.Quartz))