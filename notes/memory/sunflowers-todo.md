---
name: sunflowers-todo
description: "Girasoli: direzioni fisse nella semina della v9 MISURATE (7 nov): -0.55 s, P_W ridotto non aiuta; scritto in lb_sunflowers_v10.py"
metadata:
  node_type: memory
  type: project
  originSessionId: 0c438b02-e1ae-4df9-99f8-12e4c450bb5c
  modified: 2026-11-07T16:13:43.516Z
---

TODO aperto il 7 nov 2026, ancora da misurare: in `rng_predictor/lb_sunflowers_v9.py`, `plant_sweep` sposta il drone con `go_to_k` a ogni cella della serpentina, circa 15 tick tra calcoli e cicli contro circa 3 di una lista di direzioni fisse (una per ciascuno dei due ordini, partenza da 0 o da 31). Stima: circa 0,06 s risparmiati per round sulla semina, fino a circa mezzo secondo su ~15 round, ma solo se il tempo liberato si usa: piu' reroll nella finestra oppure P_W piu' corto. Da misurare con il simulatore tarato `haysim/sunsim2.py` + `haysim/sunprog.py` prima di scriverlo.

MISURATO il 7 nov 2026 (flag FIXDIR in haysim/sunprog.py, sim tarato, 160 seed, errore della differenza appaiata): direzioni fisse con P_W 3.8: -0.554 +- 0.133 s (obiettivo casuale), -0.393 +- 0.067 s (obiettivo fisso). Con P_W 3.7: -0.53 / -0.41 (uguale); con P_W 3.6: -0.29 / +1.84 (peggio). Quindi: direzioni fisse SI', P_W resta 3.8. Il tempo liberato serve a far finire la semina prima della scadenza, non ad accorciarla. Scritto in `rng_predictor/lb_sunflowers_v10.py` (7 nov). In gioco 2:37.964 contro ~2:38.124 della v9 (-0.16 s, entro il rumore, direzione giusta).

**Why:** l'utente l'ha chiesto come TODO mentre la sessione girasoli fa altre valutazioni. Dalla stessa analisi sono stati scartati senza bisogno di misure: la tabella POS al posto di % e // (ogni operazione costa 1 tick, nessun guadagno) e togliere i quick_print (costano 0 tick).

**How to apply:** quando si riprende la v9, provare la serpentina fissa da sola e poi insieme a P_W ridotto (3,8 -> 3,7 / 3,6). Vedi [[leaderboard-overview]].
