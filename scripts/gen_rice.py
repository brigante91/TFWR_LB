# Genera lb_rice_multi.py e lb_rice_single.py con i cicli srotolati (8 nov 2026).
# L'interprete del gioco conta 1 tick per ogni giro di for: srotolando le passate si tolgono 3 tick
# per cella a strato. In piu' alla semina si controlla l'acqua prima di chiamare la funzione
# (1 tick risparmiato per semina). Logica identica a lb_rice_multi v3 / lb_rice_single v2 inline.
# Uso: python3 gen_rice.py   (scrive i due file nella cartella corrente)

T = "\t"
# acqua in linea dopo la semina (v13): sotto W_LOW_RICH (0.25) con magazzino > RICH porta a W_RICH (0.5):
# da w in [0, 0.25) servono sempre 2 unita'; in modalita' povera sotto W_LOW (0.1) a W_POOR (0.25):
# sempre 1 unita'. Stesso comportamento della v12 (water_to arrotondava per eccesso), meno tick.
WBLK = [
    "w = get_water()",
    "if w < W_LOW_RICH:",
    "\tif num_items(WATER) > RICH:",
    "\t\tuse_item(WATER, 2)",
    "\telif w < W_LOW:",
    "\t\tuse_item(WATER, 1)",
]


def ind(lines, n):
    return [T * n + l if l else l for l in lines]


# ---------------------------------------------------------------- multi
def multi(DIAG=False):
    S = 32
    PREDIG = 0         # 4 nella v9: in gioco 1:53.9 e righe vuote
    PRELAYERS = 2
    KMIN = 20
    TAILB = 0          # 10 nella v6: in gioco peggio della v5
    FALLBACK = False   # piantagione di ripiego nella B
    GUARD = False      # in A2 aspetta se un vicino ha ancora riso
    # v19, A1 e A2 intrecciate nei primi SPL strati: raccogli le righe [0, CUT), scendi e pianta le
    # righe [0, CUT - LAG), raccogli [CUT, 32), scendi e pianta [CUT - LAG, 32). LAG = righe di
    # distanza fra lo scavo e il riso non raccolto (il cono del crollo arriva a 10 righe).
    SPL = 0 if DIAG else 2
    CUT = 18
    LAG = 12
    def a2(k):
      core = ([
        "while get_entity_type(East) == RICE or get_entity_type(West) == RICE:",
        T + "pass",
    ] if GUARD else []) + [
        "while get_ground_type() != CLAY:",
        T + "dig()",
    ] + ([
        "if get_ground_type() != CLAY:",
        T + "nsk += 1",
        T + "if nsk <= 3:",
        T + T + 'quick_print("drone", d, "salta x", get_pos_x(), "y", get_pos_y(), "z", get_pos_z(), get_ground_type(), "durezza", get_hardness(), "stab", get_stability(), "t", get_time())',
    ] if DIAG else []) + [
        "plant(RICE)",
      ] + WBLK
      if PREDIG and k < PREDIG:
        core = ["if get_entity_type() != RICE:"] + ind(core, 1)
      return core + ["move(North)"]
    def b(wf):
        return [
            "if can_harvest():",
            T + "harvest()",
            T + "dig()",
            T + "plant(RICE)",
        ] + ind(WBLK, 1) + [
            "elif get_entity_type() == RICE:",
            T + "wait_harvest()",
            T + "dig()",
            T + "plant(RICE)",
        ] + ind(WBLK, 1) + ([
            "elif plant(RICE):",
            T + wf + "()",
        ] if FALLBACK else []) + ([
            "else:",
            T + "nb += 1",
        ] if DIAG else []) + [
            "move(North)",
        ]
    def a1(k):
      return [
        "if can_harvest():",
        T + "harvest()",
        "elif get_entity_type() == RICE:",
    ] + ([
        T + "if pd == 0 and L <= PRELAYERS:",
        T + T + "pd = 1",
        T + T + "predig(%d)" % (S - k),
    ] if PREDIG and k >= KMIN else []) + [
        T + "wait_harvest()",
    ] + ([
        "else:",
        T + "na += 1",
    ] if DIAG else []) + [
        "move(North)",
    ]
    out = []
    out += HEAD_MULTI.splitlines()
    body = []
    if DIAG:
        body += ["nsk = 0", "nb = 0", "na = 0", "t0 = get_time()"]
    if DIAG or PREDIG:
        body += ["L = 0", "pd = 0"]
    if SPL:
        body.append("# A2 del primo strato: scendi all'argilla e pianta")
        for k in range(S):
            body += a2(k)
        DN = CUT - LAG
        for l in range(SPL):
            body.append("# strato %d: B, poi A1 intrecciata con la A2 dello strato dopo" % (l + 1))
            for k in range(S):
                body += b("wplant")
            body.append("# raccolta righe 0-%d" % (CUT - 1))
            for k in range(CUT):
                body += a1(k)
            body.append("# torna alla riga 0, scendi e pianta le righe 0-%d" % (DN - 1))
            body += ["move(North)"] * (S - CUT) if S - CUT <= CUT else ["move(South)"] * CUT
            for k in range(DN):
                body += a2(k)
            body.append("# avanti alla riga %d, raccolta righe %d-31" % (CUT, CUT))
            body += ["move(North)"] * LAG
            for k in range(CUT, S):
                body += a1(k)
            body.append("# avanti alla riga %d, scendi e pianta le righe %d-31" % (DN, DN))
            body += ["move(North)"] * DN
            for k in range(DN, S):
                body += a2(k)
    body.append("while True:")
    if DIAG or PREDIG:
        body += ind(["L += 1", "pd = 0"], 1)
    if DIAG:
        body += ind([
            "if d == 0:",
            T + 'quick_print("strato", L, "t", get_time(), "riso", num_items(RI), "acqua", num_items(WATER))',
            "if nsk + nb + na > 0:",
            T + 'quick_print("drone", d, "strato", L - 1, "salti", nsk, "vuote B", nb, "vuote A1", na, "t", get_time())',
            T + "nsk = 0",
            T + "nb = 0",
            T + "na = 0",
        ], 1)
    if not SPL:
        body.append(T + "# A2: scendi all'argilla e pianta (32 celle srotolate)")
        for k in range(S):
            body += ind(a2(k), 1)
    body.append(T + "rem = GOAL - num_items(RI) - LAYER")
    body.append(T + "if rem > LAYER + MARGIN:")
    body.append(T + T + "# strato normale: B e A1 senza controlli dell'obiettivo (srotolate)")
    for k in range(S):
        body += ind(b("wplant_head" if TAILB and k < S - TAILB else "wplant"), 2)
    for k in range(S):
        body += ind(a1(k), 2)
    body.append(T + "elif final_layer(rem):")
    body.append(T + T + "clear()")
    body.append(T + T + "return")
    if SPL:
        body.append(T + "# A2 dello strato dopo: scendi all'argilla e pianta (32 celle srotolate)")
        for k in range(S):
            body += ind(a2(k), 1)
    out.append("def worker(d):")
    out.append(T + "def fn():")
    out += ind([
        "if d <= 16:",
        T + "for _ in range(d):",
        T + T + "move(East)",
        "else:",
        T + "for _ in range(S - d):",
        T + T + "move(West)",
    ], 2)
    out += ind(body, 2)
    out.append(T + "return fn")
    out += TAIL_MULTI.splitlines()
    return "\n".join(out) + "\n"


HEAD_MULTI = '''# Classifica Rice (2e6 riso, 32 droni, 32x32). v19 del 10 nov 2026. GENERATO da gen_rice.py: non
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
# v19 = v18 + A1/A2 INTRECCIATE nei primi 2 strati (dove il drone aspetta la crescita ~7 e ~6 s).
#     Dopo la B: raccogli le righe 0-17, torna alla riga 0, scendi allo strato dopo e pianta le righe
#     0-5, vai alla 18, raccogli 18-31, vai alla 6, scendi e pianta 6-31. Le 32 mosse in piu' cadono
#     nelle attese; le righe 0-5 arrivano alla B dopo gia' mature e la seconda discesa e' piu' corta.
#     Lo scavo sta 12 righe dietro al riso non raccolto: il cono del crollo (3 livelli a riga su un
#     salto di 15-22) arriva fino a 10 righe. Tutti i droni fanno lo stesso percorso (niente scatto
#     per drone come nella v9). Sim haysim/rice/v4.py (SPL/CUTS/LAG): 110.6 -> 109.3 s su 8 seed,
#     2-7 celle perse a run; con 1 s di sfasamento fra droni il guadagno resta ~1.4 s. Con 3 strati
#     uguale, con 3 tagli (16, 24, 32) peggio (+0.9), con barriera sui vicini peggio (+1.2).
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

'''

TAIL_MULTI = '''

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


spawn_range(0, S)'''


# ---------------------------------------------------------------- single
def single():
    S = 8
    # percorso a serpentina: colonne pari verso Nord, dispari verso Sud, poi East (l'ultima fa il
    # giro e riporta a (0, 0))
    moves = []
    for c in range(S):
        moves += [("North" if c % 2 == 0 else "South")] * (S - 1) + ["East"]

    def a2(mv):
        return [
            "while get_ground_type() != CLAY and get_hardness() <= H_SKIP:",
            T + "dig()",
            "plant(RICE)",
            "if get_water() < S_LOW:",
            T + "water_full()",
            "move(%s)" % mv,
        ]

    def b(mv, check):
        l = [
            "if can_harvest():",
            T + "harvest()",
            T + "dig()",
            T + "plant(RICE)",
            T + "if get_water() < S_LOW:",
            T + T + "water_full()",
            "elif get_entity_type() == RICE:",
            T + "while not can_harvest():",
            T + T + "pass",
            T + "harvest()",
            T + "dig()",
            T + "if plant(RICE):",
            T + T + "if get_water() < S_LOW:",
            T + T + T + "water_full()",
            "else:",
            T + "plant(RICE)",
        ]
        if check:
            l += ["if num_items(RI) >= GOAL:", T + "return True"]
        return l + ["move(%s)" % mv]

    def a1(mv, check):
        l = [
            "if can_harvest():",
            T + "harvest()",
            "elif get_entity_type() == RICE:",
            T + "while not can_harvest():",
            T + T + "pass",
            T + "harvest()",
        ]
        if check:
            l += ["if num_items(RI) >= GOAL:", T + "return True"]
        return l + ["move(%s)" % mv]

    out = HEAD_SINGLE.splitlines()
    out.append("def sweep_a2():")
    for mv in moves:
        out += ind(a2(mv), 1)
    out.append("")
    out.append("")
    out.append("def sweep_bb():")
    for mv in moves:
        out += ind(b(mv, mv == "East"), 1)
    out.append(T + "return False")
    out.append("")
    out.append("")
    out.append("def sweep_aa():")
    for mv in moves:
        out += ind(a1(mv, mv == "East"), 1)
    out.append(T + "return False")
    out += TAIL_SINGLE.splitlines()
    return "\n".join(out) + "\n"


HEAD_SINGLE = '''# Classifica Rice_Single (1e5 riso, 1 drone, 8x8). v4 dell'8 nov 2026. GENERATO da gen_rice.py:
# non modificare a mano, cambiare il generatore.
# Storia: lb_rice.py v7 2:29.1; lb_rice_single v1 2:27.208 (#4); v2 2:26 (ultimo strato ad anello);
# versione inline dell'utente (sweep_a2/bb/aa) stimata -0.3/-0.5 s.
# v3 = versione inline con le passate srotolate (il for costa 1 tick a giro: -3 tick per cella a
#     strato) e l'acqua controllata prima di chiamare water_full() (-1 tick per semina).
# v4: in A2 e nel caso comune della B niente "if" attorno a plant() (-1 tick a semina).
#
# Schema: per strato tre passate a serpentina sulle 64 celle
#   A2: scendi all'argilla e pianta;  B: raccogli, scava la terrazza secca, pianta sul 2o blocco;
#   A1: raccogli il 2o blocco (la terrazza secca la toglie il crollo nella A2 dopo).
# Acqua: alla semina, se la cella e' sotto S_LOW, la si riempie a 1.0 (circa una volta per cella).
# Ultimo strato: si piantano solo le colonne che servono, si torna a (0, 0) e si raccoglie nello
# stesso ordine della semina. Controllo dell'obiettivo a fine colonna nelle passate normali (la run
# finisce sempre nell'ultimo strato) e a ogni raccolto nell'ultimo strato.

RICE = Entities.Rice
CLAY = Grounds.Clay
WATER = Items.Water
RI = Items.Rice
GOAL = 100000
H_SKIP = 6
S_LOW = 0.15
S = get_world_size()
HALF = S // 2
STEPS = S - 1


def water_full():
	n = (1.0 - get_water()) * 4 // 1
	if n >= 1:
		t = num_items(WATER) // 1
		if n > t:
			n = t
		if n >= 1:
			use_item(WATER, n)


def goto0():
	x = get_pos_x()
	y = get_pos_y()
	if x <= HALF:
		for _ in range(x):
			move(West)
	else:
		for _ in range(S - x):
			move(East)
	if y <= HALF:
		for _ in range(y):
			move(South)
	else:
		for _ in range(S - y):
			move(North)

'''

TAIL_SINGLE = '''

def final_round(cols):
	for c in range(cols):
		for _ in range(STEPS):
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			if plant(RICE):
				water_full()
			if c % 2 == 0:
				move(North)
			else:
				move(South)
		while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
			dig()
		if plant(RICE):
			water_full()
		move(East)
	goto0()
	for c in range(cols):
		for _ in range(STEPS):
			if can_harvest():
				harvest()
				if num_items(RI) >= GOAL:
					return True
			elif get_entity_type() == RICE:
				while not can_harvest():
					pass
				harvest()
				if num_items(RI) >= GOAL:
					return True
			if c % 2 == 0:
				move(North)
			else:
				move(South)
		if can_harvest():
			harvest()
			if num_items(RI) >= GOAL:
				return True
		elif get_entity_type() == RICE:
			while not can_harvest():
				pass
			harvest()
			if num_items(RI) >= GOAL:
				return True
		move(East)
	return False


while True:
	rem = GOAL - num_items(RI)
	c = (rem + 128 + S * 128 - 1) // (S * 128)
	if c < S:
		if final_round(c):
			clear()
			break
		goto0()
	sweep_a2()
	if sweep_bb():
		clear()
		break
	if sweep_aa():
		clear()
		break'''


if __name__ == "__main__":
    open("lb_rice_multi.py", "w").write(multi())
    open("lb_rice_diag.py", "w").write(multi(DIAG=True).replace("GENERATO da gen_rice.py", "VERSIONE DIAGNOSTICA (stampa le anomalie), GENERATO da gen_rice.py", 1))
    open("lb_rice_single.py", "w").write(single())
    print("scritti lb_rice_multi.py e lb_rice_single.py")
