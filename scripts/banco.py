# BANCO DI PROVA: confronta due script col motore vero del gioco (simulate) sugli stessi semi.
# Copialo nel gioco come file "banco", scegli CLASSIFICA, A, B e SEMI, premi play.
# Stampa il tempo di A e di B per ogni seme e alla fine media, differenza media B - A e il suo
# errore standard: se |differenza| > 2 x errore, la differenza e' reale e non fortuna.
#
# Condizioni come in classifica (lette in decompiled_full/Core/BuiltinFunctions.cs):
# - passare Unlocks (o una lista di sblocchi senza livello) mette tutto al livello MASSIMO,
#   come everythingUnlocked delle classifiche (la descrizione del gioco dice "i tuoi livelli",
#   ma il codice usa maxUnlockLevel);
# - classifiche singole: niente Megafarm (1 drone) ed Expand al livello 5 (campo 8x8);
# - oggetti iniziali: hay power 1e9; girasoli carote 1e9 e power 0 (meta' velocita').
# Unica differenza nota: la simulazione genera anche il sottosuolo (non conta per questi script).

CLASSIFICA = "sunsingle"   # "sunsingle", "sunflowers", "hay"
A = "sun_single_v9"        # nome del file nel gioco, senza .py
B = "sun_single_v10"
SEMI = 20                  # semi 1..SEMI, uguali per A e B
SPEEDUP = 1000             # il gioco lo abbassa da solo se non ce la fa

if CLASSIFICA == "hay":
	SBLOCCHI = Unlocks
	OGGETTI = {Items.Power: 1000000000}
elif CLASSIFICA == "sunflowers":
	SBLOCCHI = Unlocks
	OGGETTI = {Items.Carrot: 1000000000}
else:
	SBLOCCHI = []
	for u in Unlocks:
		if u != Unlocks.Expand and u != Unlocks.Megafarm:
			SBLOCCHI.append(u)
	SBLOCCHI.append((Unlocks.Expand, 5))
	OGGETTI = {Items.Carrot: 1000000000}

sa = 0
sb = 0
sd = 0
sd2 = 0
for seme in range(1, SEMI + 1):
	ta = simulate(A, SBLOCCHI, OGGETTI, {}, seme, SPEEDUP)
	tb = simulate(B, SBLOCCHI, OGGETTI, {}, seme, SPEEDUP)
	d = tb - ta
	sa += ta
	sb += tb
	sd += d
	sd2 += d * d
	quick_print("seme", seme, "A", ta, "B", tb, "B-A", d)

ma = sa / SEMI
mb = sb / SEMI
md = sd / SEMI
var = (sd2 - SEMI * md * md) / (SEMI - 1)
if var < 0:
	var = 0
err = (var / SEMI) ** 0.5
quick_print("media A", ma, "media B", mb)
quick_print("B - A", md, "errore standard", err)
if md < -2 * err:
	quick_print("B e' piu' veloce")
elif md > 2 * err:
	quick_print("B e' piu' lento")
else:
	quick_print("differenza non distinguibile dal caso: servono piu' semi")
