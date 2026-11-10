---
name: sunflowers-multi-v11
description: "Sunflowers multi (32 droni): v11 scritta il 10 nov 2026, sim 2:29.2 contro v10 2:39.7; analisi del perche' 2:09.7 (#1) non si raggiunge con lo schema a fasi, strumenti in haysim/sun2 e schemi scartati"
metadata:
  node_type: memory
  type: project
  originSessionId: 7dc7421d-7942-4a44-b96c-582a275d4110
  modified: 2026-11-10T11:36:10.393Z
---

Al 10 nov 2026. `rng_predictor/lb_sunflowers_v11.py` (provata in gioco: 2:28.5): stesso impianto della v10 (blocco 4x8, serpentina, fasi a finestre get_time 15..9) con: tetto di lavoro per fase WB 3800 tick (mosse in ordine di semina*200 + 215 a cella) oltre a CAP 8, finestra di fase PH_W 0.72 (era 0.85); attesa di crescita GW che cala coi round (1.75 -> 0.4); rilancio dei semi che non farebbero in tempo (LM 3.0 -> 1.4 s); semina a ritmo (rilanci solo se il resto sta in tp - rimaste*0.083). Simulatore, 16 semi, obiettivo 90-110k riscalato: v10 2:39.7, v11 2:29.2 (-10.5 +- 0.7). Peso di ogni modifica: WB 5.5 s, GW 3.4, LM 0.7, ritmo 0.3. Atteso in gioco ~2:26-2:30 (v10 2:37.964). IN GIOCO (10 nov 2026): media 2:28.476 dopo 26 run su ~48 (serie in corso), in linea col simulatore (2:29.2).

Strumenti nuovi in `rng_predictor/haysim/sun2/`: `sim3.py` (copia di sunsim2 con richieste gwait/align e jitter parametrico), `prog11.py` (schema v11 con flag), `prog12.py` (discesa con ripianto e battito di tick), `tune.py` (discesa per coordinate), `gen_sun11.py best9.json out.py` (genera lo script di gioco), `harness.py script.py seed` (esegue lo SCRIPT VERO a thread sul mondo simulato: v10 da' 158.2 s = 2:38 in gioco, v11 145.0). Vale per qualunque script girasoli: usarlo prima di dare uno script all'utente.

Dove va il tempo della v10 (per drone, 158 s): mosse 35%, attese 29%, semine 13%, raccolti 13% (di cui 6729 rilanci), codice 4%, acqua 2%. A regime 1000 raccolti x8 per round da 10.6 s (94/s); round 0 dura 21.6 s e i round 1-4 perdono 720 raccolti per celle non cresciute: l'avvio costa ~17 s. Serbatoio 25.6 unita'/s, vuoto fra 25 e 45 s.

Limiti misurati: con crescita istantanea lo schema a fasi tarato fa 128 s (limite del tempo-drone); con la crescita vera 149.5, e tutte le varianti finiscono li' (MINV 7, 8, 9; CAP 5-8; finestre piu' corte = celle perse). Il #1 (2:09.7 = 1930 tick per raccolto per drone, noi 2340 -> 2200) e' sotto il limite di questa famiglia anche a crescita infinita: usa un meccanismo che non ho trovato.

Scartati col simulatore (10 nov): 15 raccolti nell'attesa di crescita (+5 s), attesa sulla cella non cresciuta, pre-posizionamento nel tempo morto (0), sincronia a tick con get_tick_count (-0.2 s), 8 o 9 livelli (uguale), dosi d'acqua diverse nei primi round (uguale), ripianto dopo i 15 (uguale o peggio), ripianto in tutte le fasi con azioni allineate a un battito di 240 tick per rendere innocui i semi sopra il livello (+14 s: l'allineamento dei raccolti costa piu' di quanto rendono i semi in piu', che con poca acqua non crescono in tempo).

Regole verificate nel decompilato del 6 nov (Core): `Sunflower.Harvest` bonus se petali == max di tutti i girasoli e conteggio >= 10, flag globale come gia' noto; `till()` toglie il girasole SENZA toccare il flag (ma lascia prato: 600 tick per rilanciare contro 400); `measure(direzione)` legge la cella accanto per 1 tick; `get_tick_count()` e' gratis e per drone (tick dal suo avvio); a `spawn_drone` tutto e' copiato tranne i `PyDroneHandle` (has_finished/wait_for funzionano da qualunque drone che ha l'handle, wait_for restituisce il valore di ritorno): unico canale fra droni oltre a tempo, oggetti e num_drones. Asset girasole: niente overplant, companion, swap; canBeWeird si'. Loam raddoppia la resa ma serve dig (vietato, dlc 0). Fertilizzante 0.8/s, 2 s di crescita l'uno, resa dimezzata: irrilevante.

**Why:** l'utente e' #2 con 2:38.127 e voleva uno schema nuovo per avvicinare 2:09.7.

**How to apply:** far provare la v11; se il tempo in gioco non segue il simulatore, guardare le stampe del drone principale (round/fase) e ritarare con tune.py. Per andare oltre serve un'idea fuori dallo schema semina+discesa a finestre: non rifare le prove elencate sopra. Vedi [[sunflowers-todo]], [[leaderboard-overview]], [[sunflowers-single]].
