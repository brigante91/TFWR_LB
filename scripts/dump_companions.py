# In-game script (The Farmer Was Replaced): save as a code window named
# "dump_companions", then from another window run e.g.
#   simulate("dump_companions", Unlocks, {}, {}, 12345, 64)
# and paste the output into parse_companion_dump() / calibrate_startup().
# It only moves and reads, so it does not advance the companion stream.
n = get_world_size()
for x in range(n):
	for y in range(n):
		c = get_companion()
		if c != None:
			quick_print(x, y, c[0], c[1][0], c[1][1])
		move(North)
	move(East)
