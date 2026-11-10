---
name: treasure-leaderboard
description: "Classifica Treasure Map (115000 oro, 1 drone 8x8): regole estratte, scorciatoia sul percorso, script lb_treasure.py v1 (8 nov 2026, non provato)"
metadata:
  type: project
---

8 nov 2026. Steam lbid 21469574 (26 iscritti): #1 19.434 s, #5 24.4 s, #10 45.8 s.
LeaderboardSO (byte grezzi, id 1757): power 1e9, everythingUnlocked, singleDrone 1, obiettivo oro 115000, fullyGenerateUnderground, solo TreasureMapFeature (pretended chunk 2, depth 32). jump() vietato in classifica.

Regole (TreasureMapController/TreasureMapFeature/UndergroundTreasure): ogni strato da 16 ha un blocco alto 11 con basalto a tutto campo, mappa sotto in x,y in [2,6), percorso di 9 livelli sotto la mappa. measure() (1 tick) sul basalto da' (x,y) della mappa; sulla mappa genera il percorso (stringa NESWD, ~790 lettere in media su 8x8). Oro = 16 x lunghezza (treasure_map liv 5 -> profondita' 9, resa 2^4): ~12700 a tesoro, ~9 tesori. Il percorso non attraversa mai i bordi. Durezze: basalto/mappa/percorso 2 (il percorso tiene la durezza della terra originale), terra 1-3; dig = ceil(h/OP/1.5^8) tick, move 200.

SCORCIATOIA: CheckDronePosition usa FindLastIndex: basta stare su una cella qualsiasi del percorso; si cammina fra celle del percorso dello stesso livello e si scava da qualunque cella che ha percorso anche sotto. Simulato (haysim/treasure/pathgen.py, greedy.py): seguendo il percorso ~780 mosse, ottimo 3D 11.6, avido (scava se puoi, altrimenti BFS alla cella piu' vicina con percorso sotto) 13.6.

v1 `rng_predictor/lb_treasure.py`: pozzo verticale fino al basalto, measure, vai alla mappa, scava fino alla mappa, lettura q += DL[c] (~4 tick/lettera), discesa avida. Stima ~22 s. Stampa per tesoro i tempi di discesa/lettura/percorso.

v1 in gioco (8 nov): 27.936 s. Per tesoro (~10): discesa ~1.15 s (pozzo ~5.5 scavi, colonna della mappa ~7 scavi: doppio scavo), lettura ~0.4 s (3 tick/lettera misurati), percorso ~1.35 s (9 scavi da ~0.08 s, ~13.6 mosse, BFS ~0.2 s). Distanza pozzo-basalto bimodale: 4-5 oppure 10-11.
dig(direzione) e' VIETATO (BuiltinFunctions.Dig chiama NoParams: errore in gioco), anche se Execution lo gestirebbe. Ogni dig() abbassa le 4 colonne vicine (terra/roccia) fino a un blocco sopra la nuova quota (confermato: mappa vicina al pozzo = 2 scavi). v2 (`lb_treasure.py`, v1 in `lb_treasure_v1.py`): dal basalto move + dig per casella fino alla mappa (D+1 scavi invece di ~D+3..9) + BFS srotolata; stima ~26 s, da provare. Conto del minimo: 9 scavi di percorso + pozzo + basalto + lettura + ~12 mosse ~ 2.0 s a tesoro, cioe' il ritmo del #1: lo scarto rimasto e' il tunnel (~4 scavi laterali a tesoro).

v2 in gioco ~27 s (mappa sempre 2 scavi, ma ~5 mosse senza wrap: guadagno piccolo); salvata in lb_treasure_v2.py.
RNG PREVEDIBILE: il seme dello strato k e' seme0+k (chunkSeed = groundSeed + chunk + 100, +1000*(m+1)) e System.Random (Knuth) e' lineare nel seme: ogni estrazione avanza di un passo costante a ogni strato (raw: 1121899819, 630111683, 1501065279, 458365203, 969558243 mod 2^31-1 per le estrazioni 1-5). Estrazioni: 1-2 spostamento x,y (Next(0,1)), 3 quota (Next(0,6)), 4-5 mappa x,y (Next(2,6)). Spiega la distanza pozzo-basalto 4/5 o 10/11. Predittore a intervalli (haysim/treasure/mappred.py): giusta 69% dal 2o strato, 95% dal 7o. v3 (`lb_treasure.py`): pozzo nella colonna piu' economica tra tesoro, mappa prevista e vicini (stima con il livello piu' profondo del percorso precedente), primo pozzo in (3,3); stampa mappa/previsione per verificare. Da provare.

v3 in gioco (8 nov): previsione quasi sempre giusta, discesa ~0.85 s (da 1.05), run 22.6-29.2 s, media ~25.2 s (~2.58 s a tesoro). Bilancio a tesoro coerente col modello: ~17 scavi da ~0.08 s (9 percorso + pozzo d1 medio ~6.3 + 1-2), lettura 0.41 s, ~14 mosse 0.46 s, BFS ~0.15 s. Scartati nel sim: lookahead a parita' di distanza (13.03 vs 13.26 mosse; ottimo 3D 11.4 ma costa troppi tick), mondo piu' piccolo (set_world_size: percorsi molto piu' corti, 4x4 = 23 tesori). Il #1 (2.0 s a tesoro) non si spiega con questo schema: servirebbero meno scavi o scavi piu' economici; misurato (v3m, 25.9 s ufficiali; v3 26.0): durezza quasi sempre 2 ovunque (pozzo, mappa, percorso; raro 3-4), quindi scegliere colonne tenere non serve. Tick della discesa lungo il percorso 4600-12200 (media ~7700: 8 scavi 3800 + ~13 mosse 2600 + BFS ~1300).

Limite di schema: per scendere di 16 blocchi a strato servono >= 16 scavi (le cadute gratis non scendono mai sotto la quota del vicino piu' profondo), cioe' 7600 tick; + lettura 3 tick/lettera (~2400) + ottimo 11.4 mosse: ~2.2 s a tesoro, 21.5 s. Il #1 (2.0 s) deve leggere a ~2 tick/lettera o meno. Idea non provata: nodi-dizionario (node = node[c], 1 lettura) ma costruire 640 nodi costa ~1.3 s. Catena dei successori (scrittura gratuita durante la lettura): 22.8 mosse, peggio. Ottimo all'indietro: troppi tick. v4 (`lb_treasure.py`, v3 in lb_treasure_v3.py): codice q = livello*100 + y*10 + x, BFS con vicini q+-1, q+-10 senza tabelle (verificata in haysim/treasure/check_v4.py: 0 errori, 14.3 mosse); in gioco 25.0 s ufficiali (v3 26.0). Siamo sul pavimento dello schema (~2.4-2.6 s a tesoro).

v5 (`lb_treasure.py`, v4 in lb_treasure_v4.py): cicli srotolati (scelta del pozzo con 5 candidati scritti a mano + colcost con if in fila + tabella WD, primo anello della BFS senza dizionario, tolti contatori/tempi di debug); verificata identica alla v4 nel sim (0 differenze, 14.34 mosse). Guadagno stimato ~0.2-0.5 s. Dinamite non ottenibile (semina disattivata, niente strati di dinamite). La lettura (3 tick/lettera) non si srotola: for+indice+somma sono il minimo.

**Why:** nuova classifica da scalare ([[leaderboard-overview]]).
**How to apply:** leggere le stampe della prima run: se la discesa fra tesori (pozzo + colonna della mappa) pesa molto, e' li' la leva; la lettura costa ~0.5 s a tesoro e non si puo' evitare.
