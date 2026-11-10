# Piramidi:
#   RESTORE_PYRAMID       restaurare 1 piramide (e raccogliere il girasole che appare)
#   PYRAMID_RESTORER      200 piramidi -> lo script continua a scendere e restaurare
#   RESTORE_COLOR_PYRAMID COLORE = True: ricostruisce TUTTA la piramide con blocchi colorati
#   RESTORE_MAX_PYRAMID   base 29x29: usa LATO = 29 o 30 (circa 1 piramide su 13 e' da 29)
#
# Come funziona una piramide: base quadrata dispari su uno strato di calcare
# (Limestone), colonne di sabbia alte 1 + distanza dal bordo, 3-6 colonne
# mancanti (piene di terra) e 1-2 blocchi di terra sopra tutto.
# Si completa quando ogni colonna ha l'altezza giusta e niente sopra.

COLORE = False      # True per Colorful Pyramid
LATO = 29          # 7 = piramidi piccole e veloci; 29/30 per la Great Pyramid
OBIETTIVO = 200     # piramidi da restaurare in questa esecuzione
MAX_STRATI = 400    # strati scavati senza trovare piramidi prima di arrendersi

set_world_size(LATO)
S = get_world_size()
COLORI = [Grounds.Block_Red, Grounds.Block_Green, Grounds.Block_Blue]


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


def colpita(zign):
	g = get_ground_type()
	if g == Grounds.Sand:
		return True
	return g == Grounds.Limestone and get_pos_z() < zign


def scava_riga(y, zign):
	# scava di un blocco ogni colonna della riga che non ha ancora toccato la piramide
	hits = []
	vai(0, y)
	for x in range(S):
		if not colpita(zign):
			if get_entity_type() == Entities.Dynamite:
				harvest()
			dig()
		if colpita(zign):
			hits.append((x, y, get_ground_type(), get_pos_z()))
		move(East)
	return hits


def in_parallelo(funz, righe, arg):
	# esegue funz(y, arg) per ogni riga, un drone per riga; ritorna la lista unita
	droni = []
	resto = []
	for i in range(1, len(righe)):
		d = spawn_drone(funz, righe[i], arg)
		if d == None:
			resto.append(righe[i])
		else:
			droni.append(d)
	res = []
	for h in funz(righe[0], arg):
		res.append(h)
	for y in resto:
		for h in funz(y, arg):
			res.append(h)
	for d in droni:
		for h in wait_for(d):
			res.append(h)
	return res


def altezza(dx, dy, s):
	return 1 + min(dx, dy, s - 1 - dx, s - 1 - dy)


def svuota_e_colora(y, box):
	# COLORE: toglie tutta la sabbia della riga e la ricostruisce colorata
	x0, y0, s = box
	vai(x0, y)
	for i in range(s):
		n = 0
		while get_ground_type() != Grounds.Limestone and n < 30:
			dig()
			n += 1
		move(East)
	return []


def colora_riga(y, box):
	x0, y0, s = box
	vai(x0, y)
	for i in range(s):
		n = 0
		while get_ground_type() != Grounds.Limestone and n < 30:
			dig()
			n += 1
		for k in range(altezza(i, y - y0, s)):
			place(COLORI[(i + k) % 3])
		move(East)
	return []


def togli_calcare(y, box):
	x0, y0, s = box
	vai(x0, y)
	for i in range(s):
		if get_ground_type() == Grounds.Limestone:
			dig()
		move(East)
	return []


tutte = []
for y in range(S):
	tutte.append(y)

jump(Unlocks.Pyramid)
zign = 1000000000
fatte = 0
while fatte < OBIETTIVO:
	# 1) scava strato per strato finche' l'impronta della piramide smette di crescere
	prima = -1
	strati = 0
	hits = []
	while strati < MAX_STRATI:
		hits = in_parallelo(scava_riga, tutte, zign)
		strati += 1
		# le colonne mancanti toccano il calcare nello stesso strato in cui le
		# colonne esterne arrivano al livello del calcare: mi fermo subito,
		# cosi' non scavo intorno alla piramide piu' del necessario (frane)
		calcare = False
		for h in hits:
			if h[2] == Grounds.Limestone:
				calcare = True
		if calcare:
			break
		if len(hits) > 0 and len(hits) == prima:
			break
		prima = len(hits)
	if len(hits) == 0 or strati >= MAX_STRATI:
		quick_print("Nessuna piramide trovata, z =", get_pos_z())
		break

	minx = S
	maxx = -1
	miny = S
	maxy = -1
	mancanti = []
	zcalc = None
	for h in hits:
		x, y, g, z = h
		if g == Grounds.Limestone:
			zcalc = z
		minx = min(minx, x)
		maxx = max(maxx, x)
		miny = min(miny, y)
		maxy = max(maxy, y)
	s = maxx - minx + 1
	if s != maxy - miny + 1 or s % 2 == 0:
		quick_print("Impronta strana:", minx, miny, maxx, maxy, "- mi fermo")
		break
	box = (minx, miny, s)
	quick_print("Piramide base", s, "in", minx, miny, "z", get_pos_z())

	# 2) restauro
	righe = []
	for y in range(miny, miny + s):
		righe.append(y)
	quick_print("calcare a z", zcalc)
	if not COLORE:
		for h in hits:
			x, y, g, z = h
			if g == Grounds.Limestone:
				mancanti.append((x, y, altezza(x - minx, y - miny, s)))
		hmax = 0
		for m in mancanti:
			hmax = max(hmax, m[2])
		falliti = 0
		for livello in range(1, hmax + 1):
			for m in mancanti:
				if m[2] >= livello:
					vai(m[0], m[1])
					if not place(Grounds.Sand):
						falliti += 1
		quick_print("colonne mancanti", len(mancanti), "place sabbia falliti", falliti)

	# 3) raccolgo il girasole al centro (e' lui che conta per Steam)
	vai(minx + s // 2, miny + s // 2)
	if get_entity_type() != Entities.Sunflower:
		# sabbia non riuscita (o COLORE): ricostruisco tutto con blocchi colorati
		quick_print("ricostruzione con blocchi colorati")
		in_parallelo(svuota_e_colora, righe, box)
		in_parallelo(colora_riga, righe, box)
		vai(minx + s // 2, miny + s // 2)
	if get_entity_type() != Entities.Sunflower:
		quick_print("Piramide non completata (al centro c'e'", get_entity_type(), ") - diagnosi:")
		for y in range(miny, miny + s):
			for x in range(minx, minx + s):
				vai(x, y)
				h = altezza(x - minx, y - miny, s)
				if zcalc == None or get_pos_z() != zcalc + h or get_ground_type() == Grounds.Dirt:
					quick_print("colonna", x, y, "terreno", get_ground_type(), "z", get_pos_z(), "atteso", zcalc, "+", h)
		break
	while not can_harvest():
		pass
	harvest()
	fatte += 1
	quick_print("piramidi restaurate:", fatte, "potenza:", num_items(Items.Power))

	# 4) tolgo il vecchio calcare e riparto piu' in basso
	zign = get_pos_z()
	in_parallelo(togli_calcare, righe, box)
	