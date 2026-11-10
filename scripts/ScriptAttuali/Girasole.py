clear()

def harvest_column():
	while True: 
		if get_pos_y() != 0:
			move_to(get_pos_x(), 0) 
			
		for _ in range(get_world_size()):
			if get_ground_type() != Grounds.Soil:
				till()
				
			if get_water() < 0.75:
				use_item(Items.Water)
			
			if can_harvest():
				harvest()
			
			if get_entity_type() == None:
				plant(Entities.Sunflower)
				
			move(North)
		
def main_loop():
	world_size = get_world_size()

	for i in range(world_size - 1):
		if spawn_drone(harvest_column):
			move(East)
	harvest_column()
	
while True:
	main_loop()
	