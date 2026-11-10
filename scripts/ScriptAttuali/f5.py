# DLC: salta alla prima vena del minerale scelto e scava a strati da li' in giu'.
# jump() si puo' usare una sola volta per script: va chiamato prima di creare i droni.
META = Unlocks.Coal        # oppure Unlocks.Quartz
S = get_world_size()


def riga():
	while True:
		for _ in range(S):
			dig()
			move(East)


clear()
jump(META)
for _ in range(S - 1):
	spawn_drone(riga)
	move(North)
while True:
	for _ in range(S):
		dig()
		move(East)
	quick_print("z", get_pos_z(), "carbone", num_items(Items.Coal), "ferro", num_items(Items.Iron), "quarzo", num_items(Items.Quartz))