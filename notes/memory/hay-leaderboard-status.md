---
name: hay-leaderboard-status
description: "Stato della classifica Hay di The Farmer Was Replaced: miglior tempo, script e simulatore tarato"
metadata:
  node_type: memory
  type: project
  originSessionId: 3f951fe5-8b41-41f9-8c4c-d7e931188633
  modified: 2026-11-05T11:17:06.997Z
---

Al 5 nov 2026 il miglior tempo dell'utente sulla classifica Hay è 1:48.943 rank #26 (con W = 0.68 nella fase iniziale; prima 1:48.978; serie successive: 1:49.038, 1:49.072, 1:48.978, 1:49.056, media 1:49.04), prima 1:48.984 rank #26 (5 nov 2026; serie precedenti: 1:49.129, 1:49.057, 1:49.024, 1:49.149; il 1:48.984 è con erba sulla seconda riga del blocco e serpentine da 30 mosse), ottenuto con `rng_predictor/lb_hay_micro.py`. Prima era 1:50.159.

Il simulatore `rng_predictor/haysim/` riproduce il gioco: per quello script stimava 109,14 s. Le varianti si confrontano con `batch.py`, che usa sequenze di companion per cella uguali tra le varianti.

**Why:** l'utente vuole limare anche i millesimi. Lo schema a 2 celle d'erba per drone ha un minimo teorico di circa 1:47-1:48. Dal 4 nov 2026 l'RNG della classifica è crittografico, quindi prevederlo non è più possibile. I tempi da 0:50 in classifica erano fatti con la previsione.

**How to apply:** misura ogni nuova idea su `haysim` prima di proporla. Usa i costi dell'interprete corretti in `rng_predictor/FINDINGS_cactus_dino_maze.md`: il test del `while` costa 1 solo alla prima valutazione, `x in dict` costa la Size di `x`, un indice costa 1. Vedi anche [[wood-leaderboard-status]].

**6 nov 2026:** il record pulito in classifica è 1:46.960. I tempi sopra (0:50–1:27, 1:46.678, 1:47.035) sono stati dichiarati exploit. Nuova idea: disposizione densa delle coppie (reticolo (6,0),(3,2), 436 cespugli invece di 960) in `rng_predictor/lb_hay_dense.py`, generata da `rng_predictor/dense/`. Il simulatore stimava circa 108,3 s; in gioco 1:48.361, rank #12 (6 nov 2026).
Poi 1:48.174, rank #12, con la seconda disposizione densa (421 cespugli; simulatore 108,19 s, quindi tarato bene). La classifica ripulita dagli exploit ha in testa const arch 1:46.212 e ThePhilosopher 1:46.960. La seconda disposizione densa ha 421 cespugli e viaggio 278, stimata circa -0,1 s; è in `lb_hay_dense.py`, generata con PLAN=plan_opt.json.

**6 nov 2026 (sera):** `lb_hay_dense2.py` (piano `dense/plan_split3_16.json`, visita anticipata, dict letterali) e' un ottimo locale: sweep dsim a 48 seed su WR/K/EARLY/W0/W/THR/WN1/ret_water/R0/R1 e su tutti i piani plan_split* da' al massimo -0,02 s (WR 0,71-0,72, che in gioco rischia raccolti acerbi). Scomposizione del tempo per drone (dsim, 108,0 s): azioni di regime 103,7 s (fisse: 72/23 harvest + 1 move per raccolto valido, p = 1/3 x 23/24 letto in Growable.ChooseCompanion), overhead interprete dei reroll 1,7 s (4 tick per `get_companion() not in dict`, irriducibile), percorso di piantagione 1,24 s (1203 azioni totali di cui ~256 mosse di viaggio dall'origine), attese/spin acqua in warmup 0,54 s, acqua 0,42 s, spawn 0,17 s. CORRETTO 7 nov: il pavimento e' 105,44 s (regime 103,75 + interprete 1,70); il record 1:46,21 sta solo 0,8 s sopra, noi 2,7 s: il margine da recuperare (~1,9 s) e' tutto in semina (1,24 s), attese/acqua del warmup (0,96 s), spawn e finale. Nota: in dsim la riga `t += ACT # spawn_drone` di spawn_ready e' ricalcolata per ogni drone, il suo conteggio nei tally non e' tempo reale. Idea stimata: controllare get_companion() su ogni cella attraversata durante la semina e raccogliere se punta a un cespuglio gia' piantato: 45 raccolti validi in tutto, al massimo -0,15 s (erba iniziale matura). Le 539 celle mai piantate valgono solo 18 raccolti. Spawnare i figli nella regione (il figlio nasce nella cella del padre) NON aiuta: conta la somma dei tempi di partenza di tutti i droni (fieno condiviso) e un tratto di viaggio condiviso viene pagato in attesa da ogni discendente, quindi la somma e' invariante; l'albero binario all'origine e' gia' ottimo. Il tempo in classifica e' la media di ~120 run e la run finisce quando termina il programma del drone 0 (clear).

**7 nov 2026:** implementati i raccolti gratuiti in `rng_predictor/lb_hay_dense3.py` (generato da `dense/gen3.py` con `PLAN=plan_chk_500.json`, lanciato dalla cartella dense; piano da `dense/addchecks.py MARGIN=500`; verificato con `dense/verify3.py`). dsim ha la nuova azione "check"; confronti con `haysim/sweep_chk.py`. Risultato dsim: -0,164 s su 192 run (circa 46 raccolti gratuiti per run, 0,8 a vuoto). Margini: 0 tick -0,175, 500 -0,165, negativi peggiorano (troppi raccolti a vuoto). Non ancora provato in gioco: lo script ha 4247 righe. Prossimo margine da attaccare: warmup (0,96 s) e semina (1,24 s).

**7 nov 2026 (pomeriggio), idee provate e scartate** (simulatore `haysim/dsim4.py` = dsim + opzioni FERT e Q4; confronti `SIM=dsim4 PROCS=4 nice -n 19 python3 sweep_chk.py`):
- Fertilizzante nelle attese del riscaldamento: +0,03 s (Growable.GetYield dimezza la resa di una pianta weird; solo ~3 usi a run).
- Riscaldamento con 4 erbe in quadrato 2x2 (piani `dense/plan_q4c_*.json` da `dense/add4.py`): peggiora di circa 0,16 s per ogni secondo che dura (+0,34 s se finisce a 5 s), perche' il companion valido scende a 21/24.
- Tetto dell'avvio a secco: con serbatoio infinito -0,43 s, con erba gia' bagnata da t=0 -0,78 s; col serbatoio vero se ne recupera poco.
- Mosse della semina: 742 contro un minimo di 623 con la stessa disposizione (al massimo -0,12 s); le celle sono gia' le piu' vicine all'origine (distanza media 10,7 contro 10,4).
- Costo delle mosse: solo DinosaurHat lo cambia (parte da 400, un solo drone): inutile.
Conclusione: `lb_hay_dense3.py` (~107,9 s simulati) e' vicino al limite pratico del modello; restano al massimo ~0,3 s teorici. Le voci fisse sopra il pavimento 105,44 (piantare 0,43 + spawn 0,17 + viaggio minimo 0,17 = 0,77 s) spiegano gia' tutto il distacco del record (0,8 s), quindi il record implica avvio a secco quasi perfetto o qualcosa fuori dal modello.
