# DLC: fattoria di bambu'. Colonne pari = corridoio, colonne dispari = bambu'.
# Il bambu' cresce solo su soil/dirt/perlite: la prima volta la cella d'erba viene arata.
# Dal corridoio il drone regola l'altezza ed entra nel bambu':
#  - ai primi due fiori entra a measure() (fiore - 1): taglia la cima e il bambu' riparte;
#  - dopo due tagli entra alto (18) e raccoglie al terzo fiore (resa = altezza^2).
S = get_world_size()
N = S //2


def riga():
	tagli = []
	for _ in range(N):
		tagli.append(0)
	while True:
		for i in range(N):
			# sul corridoio: scegli l'altezza per entrare nel bambu' a est
			m = measure(East)
			if tagli[i] >= 2:
				h = 18
			else:
				h = m
			if h != None and get_hover() != h:
				hover(h)
			move(East)
			if get_entity_type() != Entities.Bamboo:
				if get_ground_type() == Grounds.Grassland:
					till()             # il bambu' cresce solo su soil/dirt/perlite
				plant(Entities.Bamboo)
				tagli[i] = 0
			elif tagli[i] >= 2:
				if can_harvest():
					harvest()
					plant(Entities.Bamboo)
					tagli[i] = 0
			elif m != None and measure() > m:
				tagli[i] += 1          # il taglio ha fatto avanzare il fiore
			move(East)             # torna su un corridoio


clear()
for _ in range(S - 1):
	spawn_drone(riga)
	move(North)
riga()