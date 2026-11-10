---
name: hay-single
description: "Classifica Hay_Single (1 drone, 8x8, 1e8 fieno): lb_hay_single_v1.py scritto l'8 nov 2026, stima 2:53, generatore e simulatori in rng_predictor/haysingle/"
metadata:
  node_type: memory
  type: project
  originSessionId: 0c438b02-e1ae-4df9-99f8-12e4c450bb5c
  modified: 2026-11-08T09:56:06.815Z
---

Hay_Single: 1 drone, campo 8x8, obiettivo 100.000.000 di fieno (FINDINGS.md; descrizione del gioco "Farm 100_000_000 hay with a single drone on an 8x8 farm"). Raccolto con companion 81.920, quindi servono 1.221 raccolti validi.

8 nov 2026: scritto `rng_predictor/lb_hay_single_v1.py`, non ancora provato in gioco. Generato da `rng_predictor/haysingle/gen.py` con il percorso di `route.py`. A = (0,0), dove il drone parte, e C = (1,0), con 30 cespugli sul resto dei due rombi. Semina con 35 mosse in un giro unico, con controlli dei raccolti gratuiti (circa 3,6 attesi). Acqua: 4 unita' se sotto 0.9, controllo ogni 8 cicli. `can_harvest` solo dopo un reroll al primo colpo sull'altra cella (flag `fast`). Controllo del fieno a ogni raccolto solo negli ultimi 3 milioni.
- Stima `regime_sim.py`: 173,5 s, circa 2:53. Soglie 0.95/0.85/0.8/0.7 peggiori; controllare can_harvest sempre costa +0,2 s.
- Il percorso chiuso perfetto sulle 32 celle non esiste per la parita' del toro: 35 mosse contro un minimo di 33.
- `emulate.py` esegue lo script generato su un campo finto: 10 semi, sempre 1.221 validi, zero raccolti su cespugli, zero erba acerba dopo una mossa. Varianza fra semi circa +-4 s (numero di reroll).

**Why:** l'utente ha chiesto "il miglior script possibile per hay single". Lo schema a 2 erbe e' il limite gia' dimostrato per l'hay a 32 droni; vedi [[hay-leaderboard-status]].

**How to apply:** dopo il test in gioco confronta il tempo con 2:53. Se c'e' scarto, tara `regime_sim.py` sul log. Per confronti fra varianti usa `banco.py` con CLASSIFICA da aggiungere per Hay_Single: Unlocks senza Megafarm, Expand 5, power 1e9.

**8 nov 2026, in gioco:** v1 2:52.783, rank #84; stima 2:53.5, quindi simulatore tarato. #1 const arch 2:45.245, #2 2:46.338, #3 2:46.396, #4-#15 2:47.5-2:49.2. Le sole azioni di questo schema valgono 2:46.0 (1.221 x (3.13 raccolti + 1 mossa) x 200 tick): i primi tre stanno sotto, quindi usano un meccanismo diverso, non trovato. Esclusi nel codice: swap (non cambia companion, che resta sulla cella assoluta), moltiplicatore del terreno (1 per prato e terra), DinosaurHat (mele non disponibili), 3 erbe, set_world_size.

**v2** (`lb_hay_single_v2.py`, `ROUTE=route2.json OUT=lb_hay_single_v2.py VER=2 python3 gen.py`), non ancora provata in gioco. Effetti delle azioni applicati all'inizio dell'azione (Execution): fra due raccolti della stessa erba passano almeno ~810 tick, quindi con acqua >= 0.69 can_harvest non serve mai. Niente flag fast; acqua solo nel ramo "valido al primo colpo" se < 0.8; percorso di 34 mosse (A (5,7), C (6,7); limite di parita' 15/15 cespugli, quindi 30-31 teoriche). `regime_sim2.py`, 80 semi appaiati: -0.7 s (T 0.75 -0.8, 0.9 -0.19). `emulate.py` (SCRIPT=...) su 16 semi: zero acerbi, zero cespugli raccolti.

**v2 in gioco (8 nov 2026):** 2:52.057 e PB 2:51.329, rank #67; stima 2:52.1 confermata. Fra un invio e l'altro circa +-0.7 s.
