# Classifica Rice (2e6 riso, 32 droni, 32x32). v18 del 9 nov 2026. GENERATO da gen_rice.py: non
# modificare a mano, cambiare il generatore.
# Storia: lb_rice.py v5 1:57.01; lb_rice_multi v1 1:53.712; v2 1:51.13x di media (#1); v3 1:51.024
# su 4 run (cicli in linea, niente controllo dell'obiettivo negli strati normali).
# v4 = v3 con le passate srotolate (il for costa 1 tick a giro: -3 tick per cella a strato) e il
#     livello dell'acqua controllato prima di chiamare wplant() (-1 tick per semina).
# v4 in gioco ~1:50.97. v5: in A2 e nel caso comune della B niente "if" attorno a plant() (-1 tick
#     a semina; annaffiare una cella saltata e' innocuo). Il controllo dell'acqua nella B resta:
#     nel simulatore toglierlo costa +1.6 s.
# v6: acqua mirata nella B quando scarseggia (magazzino <= RICH). La B pianta a 0.18 s/cella e la A1
#     raccoglie a 0.07 s/cella, quindi la A1 raggiunge le piante giovani: le celle tirate sono le
#     ULTIME della colonna, ma prima l'acqua la prendevano le prime e il serbatoio si svuotava.
#     Ora con poca acqua la B annaffia solo le ultime TAILB celle (a 0.25); con molta acqua tutte
#     (a 0.5) come prima. Sim (haysim/rice/v2.py, BSCARCE/TAILB): 110.8 -> 109.4 s; con acqua
#     infinita 97.9, quindi le attese per l'acqua valgono ancora ~11 s.
# v7: niente piantagione di ripiego nella B. Una cella saltata in A2 (roccia dura) veniva piantata
#     nella B e nella A1 non era cresciuta: il drone aspettava fino a 7 s, i vicini iniziavano la
#     discesa accanto al suo riso e TUTTA la sua colonna crollava (visto in gioco: colonne intere
#     vuote e il drone una passata indietro). Il ripiego valeva 128 riso, il crollo ~30 raccolti.
#     Opzione GUARD (spenta, ~0.2 s per drone): in A2 prima di scendere aspetta finche' le celle
#     vicine a Est e Ovest hanno riso.
# In gioco: v6 media 1:51.135, v7 1:52.087 dopo 7 run, contro 1:50.97 della v5: l'acqua mirata in
#     coda (v6) non rende come nel simulatore. v8 = acqua della v5 (TAILB = 0, tutte le celle con
#     wplant) + niente ripiego nella B (v7). In gioco 1:51.091 su 12 run (= v5): il ripiego non
#     c'entrava. Diagnostica (lb_rice_diag.py): zero salti per durezza, ~1 cella vuota ogni tanto,
#     riso pieno (262k/strato); strati 20.3 / 17.3 / 13.7 / poi 12.75 s: ~12 s di attese nei primi
#     3 strati (acqua), poi solo lavoro.
# v9: PRE-SCAVO. Nei primi PRELAYERS strati, quando in A1 il drone deve aspettare la crescita su una
#     cella >= KMIN (coda della colonna, attesa di 3-5 s), torna alla cella 0, scava la discesa
#     dello strato dopo (i 14 blocchi) e pianta gia' le prime PREDIG celle, poi torna indietro.
#     La A2 successiva salta le celle gia' piantate: niente 14 scavi (-1 s) e la cella 0 arriva
#     alla B gia' matura. Costo: la cella 31 (adiacente alla 0 col wrap) e fino a 3 celle dei
#     vicini crollano (~0.5k riso). Sim con evaporazione (tarato sugli strati del gioco):
#     113.2 -> 112.3 s su 6 seed; con 8-12 celle o col controllo dei vicini tornano i crolli.
#     IN GIOCO v9: 1:53.9 su 13 run e RIGHE VUOTE: la discesa alla cella 0 fa crollare le celle 0-3
#     delle colonne vicine (col riso, se il vicino non le ha ancora raccolte); lo scatto (prima
#     attesa su cella >= 20) nel gioco arriva spesso prima (cella ~10) e divide i droni in due
#     gruppi. Variante "all'inizio della A1" (sim PRESTART): 141 s, 360 celle perse. SCARTATO.
# v10 = v8 (PREDIG = 0): acqua v5, niente ripiego, niente pre-scavo.
# v18 = v17 con clear() di nuovo a fine run: SERVE. Senza, la run finisce solo quando tutti i droni
#     escono (alcuni stanno aspettando una pianta per secondi): v15 1:56.0, v17 1:55.365.
# v17 = v16 ma, come la v13, se la pianta crolla durante l'attesa la cella si scava e ripianta
#     comunque (v15 in gioco: 1:56.0 alla prima run; v13 1:50.489 dopo 3 run).
# v16 = v15 senza controllo dell'obiettivo in bb() (non puo' scattare sulle prime kneed celle),
#     letterali 32/16/4096 al posto di S, S // 2, S * 128, tolte W_POOR e W_RICH (non usate).
# v15 = v14 con l'acqua in linea anche in bb() (ultimo strato, niente piu' wplant) e senza clear()
#     a fine run (l'obiettivo e' gia' raggiunto). Stesso comportamento, pochi tick in meno.
# v14 = v13 con wait_harvest(): attesa + raccolta in una funzione; se la pianta crolla durante
#     l'attesa niente harvest/dig/plant sulla cella crollata; acqua in linea anche dopo l'attesa nella B.
#     In gioco v13: 1:50.541 dopo 17 run.
# v13 = v12 con l'acqua scritta in linea dopo ogni semina (niente chiamate wplant/water_to: le
#     quantita' sono sempre 2 unita' col magazzino pieno e 1 in modalita' povera e in attesa).
#     Stesso comportamento, ~18 tick in meno per annaffiatura.
# v12 = v11 senza get_hardness() nella discesa (in gioco mai una cella saltata; -2/3 tick a cella)
#     e margine dell'ultimo strato +4 invece di +3 (sim haysim/rice/v3.py: con +3 1 run su 24
#     non chiude l'obiettivo nell'ultimo strato, +4 mai e ~0.03 s meglio).
# v11 = v10 + uscita da wait_grown se la pianta crolla. In gioco v10: run da 1:50.6 e da 2:10.2 con
#     droni fermi: un drone che aspettava in A1 restava indietro, il vicino scendeva nella A2 accanto
#     alle sue piante, la pianta attesa crollava e il drone girava a vuoto per sempre.
#
# Schema: ogni drone ha una colonna di 32 celle e la percorre verso Nord (wrap). Per strato:
#   A2: scendi all'argilla e pianta;  B: raccogli, scava la terrazza secca, pianta sul 2o blocco;
#   A1: raccogli il 2o blocco (la terrazza secca la toglie il crollo nella A2 dopo).
# Acqua alla semina: sotto W_LOW_RICH si porta a W_RICH se in magazzino ce n'e' piu' di RICH,
# altrimenti sotto W_LOW si porta a W_POOR; in attesa della crescita si porta a W_WAIT.
# Ultimo strato (mancano meno di un blocco intero + MARGIN prima della B): B scava e ripianta solo
# sulle prime kneed celle, controllo dell'obiettivo a ogni raccolto.

RICE = Entities.Rice
CLAY = Grounds.Clay
WATER = Items.Water
RI = Items.Rice
GOAL = 2000000
W_LOW = 0.1
RICH = 100
W_LOW_RICH = 0.25
W_WAIT = 0.25
S = 32              # lato del campo: un drone per colonna
LAYER = 131072      # riso di un blocco d'argilla su tutto il campo (32*32*128)
MARGIN = 25600      # sicurezza sul passaggio alla versione con i controlli (200*128)


def wait_harvest():
	# aspetta la crescita e raccoglie. Se la pianta crolla durante l'attesa (vicino che scende
	# accanto) esce senza raccogliere; chi chiama scava e ripianta comunque (come la v13: saltare
	# la cella nella v14-v16 lasciava buchi, run da 1:56). Sotto W_WAIT (0.25) basta 1 unita'.
	if get_water() < W_WAIT:
		use_item(WATER, 1)
	while not can_harvest():
		if get_entity_type() != RICE:
			return
	harvest()


def bb():
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		wait_harvest()
	else:
		return
	dig()
	plant(RICE)
	w = get_water()
	if w < W_LOW_RICH:
		if num_items(WATER) > RICH:
			use_item(WATER, 2)
		elif w < W_LOW:
			use_item(WATER, 1)


def aa():
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		wait_harvest()
	else:
		return False
	return num_items(RI) >= GOAL


def final_layer(rem):
	# ultimo strato: c2 solo sulle prime kneed celle, controlli a ogni raccolto. True = obiettivo
	# niente controllo dell'obiettivo nella bb(): l'obiettivo arriva dopo ~32-k celle della B
	# quando kneed = 4-k, quindi mai sulle prime kneed celle (al massimo uno scavo in piu', poi aa() se ne accorge)
	kneed = 32
	if rem < LAYER:
		kneed = rem // 4096 + 4
		if kneed > 32:
			kneed = 32
		elif kneed < 0:
			kneed = 0
	for _ in range(kneed):
		bb()
		move(North)
	for _ in range(32 - kneed):
		if aa():
			return True
		move(North)
	for _ in range(S):
		if aa():
			return True
		move(North)
	return False

def worker(d):
	def fn():
		if d <= 16:
			for _ in range(d):
				move(East)
		else:
			for _ in range(S - d):
				move(West)
		while True:
			# A2: scendi all'argilla e pianta (32 celle srotolate)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			while get_ground_type() != CLAY:
				dig()
			plant(RICE)
			w = get_water()
			if w < W_LOW_RICH:
				if num_items(WATER) > RICH:
					use_item(WATER, 2)
				elif w < W_LOW:
					use_item(WATER, 1)
			move(North)
			rem = GOAL - num_items(RI) - LAYER
			if rem > LAYER + MARGIN:
				# strato normale: B e A1 senza controlli dell'obiettivo (srotolate)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				elif get_entity_type() == RICE:
					wait_harvest()
					dig()
					plant(RICE)
					w = get_water()
					if w < W_LOW_RICH:
						if num_items(WATER) > RICH:
							use_item(WATER, 2)
						elif w < W_LOW:
							use_item(WATER, 1)
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_harvest()
				move(North)
			elif final_layer(rem):
				clear()
				return
	return fn


def spawn_range(lo, hi):
	while hi - lo > 1:
		mid = (lo + hi) // 2
		spawn_drone(spawn_range_task(mid, hi))
		hi = mid
	worker(lo)()


def spawn_range_task(lo, hi):
	def fn():
		spawn_range(lo, hi)
	return fn


spawn_range(0, S)
