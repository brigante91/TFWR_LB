# Piano classifiche (6 nov 2026) — analisi degli script `lb_*` (escluso hay)

Fonti: script in `rng_predictor/`, copie in gioco in `Saves/Save1/`, sorgenti decompilate del
4 nov in `decompiled_full/Core/`, asset (`resources.assets` via UnityPy), classifiche Steam
(`steamcommunity.com/stats/2060160/leaderboards/<id>/?xml=1`). Il gioco NON e' stato avviato.
Attenzione: `Core.dll` e `Utils.dll` sono stati aggiornati oggi alle 11:57 (588 KB contro 579 KB
del 4 nov); `ilspycmd` non parte (manca il runtime .NET 6), quindi le regole qui sotto vengono
dalla build del 4 nov e vanno riverificate se qualcosa in gioco non torna.

## Stato classifiche (SteamID 76561198129401400)

| Classifica | #1 | #10 | #25 | #57 | Tu | Stima script v2 |
|---|---|---|---|---|---|---|
| Cactus (2337 iscritti) | 0:18.9 | 0:27.7 | 0:32.9 | 0:34.5 | 0:48.174 (#393) | ~0:42 |
| Carrots (639) | 3:10.7 | 3:45.9 | 4:08.4 | 4:34.7 | — | ~3:50 |
| Dinosaur (1780) | 5:14.9 | 10:23.9 | 11:56.2 | 12:52.4 | — | da simulare |
| Maze (1822) | 0:42.8 | 1:27.0 | 1:39.5 | 1:54.2 | — | da provare |
| Pumpkins (1449) | 5:43.3 | 5:59.7 | 6:14.1 | 6:48.5 | — | ~5:00-5:20 |
| Sunflowers (12) | 3:13.5 | 9:07.6 | — | — | — | ~3:00-3:10 |
| Wood (901) | 3:44.3 | 4:16.2 | 4:27.8 | 4:56.3 | — | sim 4:47 (lb_wood_best) |
| Hay (1642) | 1:46.2 | 1:48.1 | 1:49.4 | 1:51.4 | 1:48.943 (#21) | — |

I tempi dal 2024 in su sotto i 20-30 s (cactus) e i 5 min (dinosauro) sono quasi certamente
fatti con la previsione dell'RNG, che dal 4 nov non e' piu' possibile.

## Dati dagli asset (livelli massimi con `everythingUnlocked`)

grass 10, carrots 10, pumpkins 10, trees 10, cactus 6, dinosaurs 6, mazes 6, sunflowers 1,
polyculture 5, watering 9, fertilizer 4, speed 5, expand 9, megafarm 5.
Oggetti iniziali: carrots = power/hay/wood 1e9; pumpkins = carrot+power 1e9; cactus = pumpkin+power;
dinosaur = cactus+power; maze = weird_substance+power 1e9; sunflowers = SOLO carrot 1e9 (power 0!).
Crescita (s): grass 0.5, cactus 1, pumpkin 2, bush 4, sunflower 5, carrot 6, tree 7; tutte /(1+4*acqua),
bush/carrot/tree +-20%. Acqua +1 ogni 20/512 s (25.6/s), fertilizzante +1 ogni 1.25 s.
Fertilizzante = +2 s di crescita ma rende la pianta "weird" (resa /2 + weird substance): mai usarlo.

## Costi dell'interprete (vedi FINDINGS_cactus_dino_maze.md)

Azioni 200 tick (move/plant/harvest/till/swap/use_item/spawn/clear/change_hat), fallite 1.
measure/can_harvest/get_*/num_items 1, get_time/get_tick_count 0. Operatore 1, confronto 1,
if 1, for 1 per iterazione, while 1 solo alla prima valutazione, indice 1, chiamata propria 1.
6075 tick = 1 s simulato con power > 0 (3037 senza power: conta per Sunflowers).

## Per script

### lb_cactus.py (in gioco: 0:48.174) -> `lb_cactus_v2.py`
- Shaker sort colonne poi righe. Simulato offline (`haysim/cactus_sort_sim.py`): colonne 589 azioni
  medie (19 s), righe 425 (14 s); il percorso critico e' il max su 32 linee: ~49.7 s. Torna col 48.
- Il numero e' legato alla CELLA finche' il cactus non cresce: `lb_cactus_fast.py` (reroll con
  harvest del seme) va in loop infinito. Marcato NON USARE.
- `lb_cactus_hybrid.py`: idea giusta (reroll a bande prima del sort) ma banda per colonna e reroll
  con harvest: l'harvest di un cactus cresciuto fa pop dei vicini se ordinati (~1 volta ogni 3 run
  nel simulatore) e lascia buchi -> measure() = None -> crash del sort.
- v2: banda DIAGONALE t=(x+y)*10//63 +-1 (abbassa le inversioni anche delle righe), reroll con
  till+till+plant (600 tick, niente pop), K=8 giri verso nord con wrap (rivisita dopo >6075 tick,
  quindi sempre cresciuti), barriere via calo dell'acqua in inventario (niente respawn), harvest
  dal punto in cui sta il main. Simulatore `haysim/cactus_hybrid2.py`: ~42.6 s (-7 s).
- Limite del metodo: ~2 azioni per inversione sono inevitabili con un drone per linea; sotto i
  ~38 s servirebbe un'idea diversa (es. 2 droni per linea nella fase colonne).

### lb_sunflowers.py (mai inviata) -> `lb_sunflowers_v2.py`
- BUG grave: `Sunflower.Harvest` aggiorna il flag `hadIncorrectSunflowerHarvest` anche quando si
  raccoglie un SEME. Il reroll `harvest(); plant()` dei 31 droni lascia il flag quasi sempre
  "sporco" e il raccolto successivo (di chiunque) perde il bonus x8. Inoltre la copia in gioco
  ha MAXP = 10, che non e' mai il massimo del campo se esiste un 15.
- Livello sunflowers = 1: 1 power per girasole, 8 col bonus -> ~12.500 raccolti. Power iniziale 0:
  la simulazione va a meta' velocita' finche' non si raccoglie il primo girasole.
- v2: round sincronizzati con `get_time()`: finestra di piantagione (reroll fino a petali >= 11,
  flag sporco pagato una volta per round), crescita, poi fasi di raccolta 15,14,13,12,11: in
  ogni fase si raccolgono solo i girasoli con quel valore, che e' il massimo del campo. Primo
  round senza reroll (9 fasi) e finestre doppie perche' lento. Stima ~13 round da ~13.8 s + 28 s
  del primo = ~3:00-3:10 contro 3:13 del #1. Parametri da tarare in gioco: P_W, PH_W, MINV.
  Rischio: un drone che sfora la fase (colonna con >14 celle dello stesso valore) fa perdere
  qualche bonus agli altri; con PH_W = 1.5 e' raro e costa poco.

### lb_carrots.py (mai inviata) -> `lb_carrots_v2.py`
- 2 carote per drone + bush intorno: la crescita (6 s, 1.76 s con acqua 0.6) limita a ~1 raccolto
  ogni 0.9 s per drone -> ~11 minuti. Il companion delle carote e' grass/bush/tree con la stessa
  probabilita', e il prato (grass) e' gratis: i bush non servono.
- v2: 32 blocchi 2x3 a passo 5, un drone gira sul perimetro (1 mossa per raccolto), tutto il resto
  prato. `haysim/layout_eval.py`: ~1820 tick per raccolto (anelli su coppie di righe come
  lb_wood_best: ~2000; vecchio schema ~4400). 24.415 raccolti / 32 droni -> ~3:50.
- Il #1 fa ~1515 tick/raccolto: non so come. Idee non ancora valutate: piantare il tipo richiesto
  nella cella companion quando e' adiacente invece di rerollare; 4 celle 2x2 con meno mosse
  (ma attende la crescita).

### lb_pumpkins.py (mai inviata) -> `lb_pumpkins_v2.py`
- Resa 32x32 = 1024*6*512 = 3.145.728 -> 64 raccolti. Il vecchio script rispawna 31 droni a ogni
  ciclo (catena spawn 6200 tick + goto colonna fino a 3200): ~1.5 s x 64 = ~100 s buttati.
- v2: worker persistenti per colonna; sincronizzazione naturale: il worker aspetta che la cella
  sotto torni vuota dopo il raccolto del main. Il main raccoglie MARGIN=0.8 s dopo aver finito la
  sua colonna: se una colonna e' in ritardo il quadrato e' 31 (resa -6%, le celle restano).
  Gestione morti (20%) con lista pending e attesa sul posto quando restano <= 2 celle. Acqua
  prioritaria alle ripiantate. Stima ciclo ~4.5-5 s -> ~5:00-5:20 (il #1 fa 5:43).
- Da fare: simulatore delle zucche per tarare MARGIN e la politica dell'acqua.

### lb_wood.py / lb_wood_best.py (in gioco c'e' lb_wood_best; sim 287 s = 4:47, ~#35)
- Struttura buona (anelli da 6 su coppie di righe, acqua 0.9). Costi: harvest+plant 400,
  reroll ~920, mosse 533, acqua/attese ~400. Idee per il prossimo giro (da misurare su woodsim):
  `use_item(Water, 4)` in un colpo invece di 4 azioni; durante i primi ~30 s (serbatoio vuoto,
  crescita 7 s) piantare alberi extra nelle righe libere per non stare fermi; W piu' bassa;
  controllo dell'obiettivo solo vicino alla fine come in lb_hay_micro.

### lb_dinosaur.py (mai inviata; #1 5:14, #10 10:24)
- Logica corretta (ciclo hamiltoniano + scorciatoie verso la mela, posizione della prossima mela
  da measure()). Due problemi: (1) il costo del codice per passo (~60-100 tick: ciclo sui vicini,
  dizionari, `in occ`) supera il costo del move quando il cappello scende a 33 tick; (2) seguendo
  il ciclo nella parte finale il percorso medio per mela e' ~(celle libere)/2: la somma e' ~M^2/4
  = 262k mosse, mentre il #1 ne fa ~58k. Serve una strategia che tenga la zona libera compatta
  (distanze ~sqrt(libere)) e un simulatore Python per confrontarle. Il piu' lungo da fare.

### lb_maze.py (mai inviata; #1 0:43, #10 1:27)
- 300 riusi + 1 harvest = 301 x 32768 = 9.863.168 esatto. Ogni riposizionamento apre muri con
  prob. 0.2% per cella/direzione (~4 per riuso): dopo 300 riusi il labirinto e' quasi aperto,
  quindi i riusi finali costano pochissimo con 32 droni sparsi. Il DFS greedy per drone senza
  memoria del labirinto e' il punto debole; il `for i in range(3000)` iniziale e' una sincronia a
  tempo fragile (i droni potrebbero trovarsi su una siepe). Da provare in gioco prima di toccarlo.

## Ordine proposto per i test in gioco
1. `lb_sunflowers_v2` (12 iscritti, #1 alla portata, bug grave nel vecchio).
2. `lb_pumpkins_v2` (deterministico, #1 alla portata).
3. `lb_carrots_v2` (3x piu' veloce del vecchio).
4. `lb_cactus_v2` (-6 s stimati, poi micro-ottimizzazioni).
5. wood (woodsim), poi dinosauro (serve il simulatore), poi labirinto.
Per copiare in gioco: `Saves/Save1/<nome>.py` (il gioco ha il file watcher); lancio
`leaderboard_run(Leaderboards.X, "nome_file", 1000000)` come nei commenti degli script.
