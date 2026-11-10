# Audit in sola lettura del codice di gioco (The Farmer Was Replaced) — bug e anomalie rilevanti per le classifiche

**Avvertenza sulle versioni.** `Core.dll` e `Utils.dll` installati sono stati aggiornati il **6 nov 2026 alle 11:57** (Core.dll 588 288 byte). I sorgenti esaminati qui sono la decompilazione ILSpy della **build del 4 nov 2026** (`decompiled_full/Core`, `decompiled_full/Utils`, Core.dll 579 KB). Tutti i riferimenti `file:riga` si riferiscono a quei sorgenti; ogni punto va riverificato sulla build del 6 nov prima di considerarlo attuale.

Metodo: lettura statica dei sorgenti, nessuna esecuzione del gioco, nessuna modifica ai salvataggi. La documentazione di riferimento è il `__builtins__.py` generato dal gioco in `Saves/Save1/` (solo letto). Le note precedenti (`FINDINGS*.md`, `REA_VERIFICA.md`, `PIANO_LB.md`) sono state usate come punto di partenza e verificate.

Categorie:
- **(A) bug veri**: il codice fa una cosa diversa da quella che il resto del codice o la documentazione fanno aspettare.
- **(B) comportamenti non documentati sfruttabili in classifica**: non sono errori, ma non stanno nella documentazione e danno un vantaggio a chi li conosce.
- **(C) curiosità innocue**: codice morto, incoerenze cosmetiche, discrepanze di documentazione senza effetto pratico.

Gravità: **Alta** (può decidere l'esito o il tempo di una run), **Media** (effetto misurabile ma limitato), **Bassa** (effetto trascurabile o solo fuori classifica).

Glossario dei costi (Simulation.cs:119-125: `actionOps = 200`, `operationOps = 1`; Simulation.cs:222-226: `OpDuration = ceil(2 500 000 / fattoreVelocità) ns`; con speed 5 e power > 0 il fattore è 15,1875 → 164 610 ns per tick, 6075 tick ≈ 1 s simulato).

---

## Riepilogo

| # | Cat. | Titolo | Gravità | Classifiche toccate |
|---|---|---|---|---|
| A1 | A | Zucche: raggruppamento greedy e immutabile → cella bloccata a gruppo 1x1 ("512 per sempre") | Alta | Pumpkins |
| A2 | A | Zucche: liberare una zucca cresciuta (till, dinamite…) distrugge tutto il gruppo senza resa | Media | Pumpkins |
| A3 | A | Girasoli: il flag `hadIncorrectSunflowerHarvest` cambia anche raccogliendo un seme | Media | Sunflowers |
| A4 | A | Girasoli: l'anteprima `GetYield()` ignora la penalità e ha un effetto collaterale | Bassa | Sunflowers (solo UI) |
| A5 | A | Labirinto: il tesoro non può mai finire nell'ultimo vicolo cieco (`Next(Count-1)`) | Bassa | Maze |
| A6 | A | `use_item(Weird_Substance, n)` su cespuglio con n troppo piccolo: effetto applicato, ritorna False, 1 tick, nessun consumo | Bassa | Maze |
| A7 | A | Azioni senza effetto che costano 200 tick (reuse durante trasloco, till non arabile, swap vuoto-vuoto, harvest su coda/mela) | Bassa | tutte |
| A8 | A | Errore runtime in classifica: la run resta sospesa invece di chiudersi come fallita | Bassa | tutte |
| A9 | A | `change_hat` con cappello `preventHover` mentre si è in hover: fallisce in silenzio | Bassa | nessuna |
| A10 | A | `Treasure.SetValues`: `nextY` scritto in `nextPos.x` (salvataggio) | Bassa | nessuna |
| B1 | B | `clear()` come interruttore di fine run (termina tutti i droni in 200 tick) | Media | tutte le multi-drone |
| B2 | B | `measure()` su zucca restituisce un numero condiviso da tutto il gruppo: oracolo di fusione in 4 tick | Media | Pumpkins |
| B3 | B | Girasoli: la penalità vale per "serie" di errori, non per errore; un seme con petali massimi la azzera gratis | Media | Sunflowers |
| B4 | B | Il power viene consumato dalle azioni anche in classifica (1/30 per azione da 200 tick); velocità dimezzata finché power = 0 | Media | Sunflowers (obiettivo in power) |
| B5 | B | Labirinto: ogni riuso apre muri con p = 0,002 per adiacenza; dopo 300 riusi resta il 55 % dei muri | Media | Maze |
| B6 | B | Labirinto: `use_item` funziona anche su cespuglio non cresciuto; 300 riusi per labirinto indipendentemente dalla taglia → più labirinti piccoli in parallelo | Media | Maze |
| B7 | B | Cactus: la taglia è legata alla cella finché un cactus non cresce lì; `swap` scambia anche il numero | Bassa | Cactus |
| C1-C14 | C | Codice morto (`send/receive/get_drone_id`), discrepanze doc (5x vs 8x, "al cubo" vs tetto 6, "lato" vs lato²), arrotondamenti, interprete, ecc. | — | — |

---

## (A) Bug veri

### A1 — Zucche: raggruppamento greedy e immutabile, una cella può restare per sempre un gruppo 1x1

**File e righe.** `PumpkinController.cs:123-169` (`MergeWithOthers`), `:186-201` (`LargestSquare`), `:203-216` (`HasOverlaps`), `:81-100` (`RemovePumpkin`); `Pumpkin.cs:22-32` (`OnFullyGrown` → `AddPumpkin`), `:44-52` (`Harvest`), `:56-65` (`GetDrops`).

**Cosa fa il codice.** Quando una zucca finisce di crescere, `AddPumpkin` → `MergeWithOthers` calcola con programmazione dinamica il quadrato più grande di zucche cresciute che contiene la nuova posizione e, in `LargestSquare`, lo accetta solo se `!HasOverlaps(rect)`, cioè se nessun gruppo già formato sporge fuori dal rettangolo candidato. I gruppi esistenti non vengono mai ridisegnati: una volta formato, un gruppo cambia solo quando viene raccolto per intero (`RemovePumpkin`) o inglobato in un quadrato che lo contiene tutto. Se nessun quadrato di lato ≥ 2 passa il test, la zucca diventa un gruppo 1x1 (`:200`). `Pumpkin.Harvest` rimuove solo le celle del gruppo della zucca raccolta e rende `lato² × min(lato, 6) × YieldFactor` (`:58-60`).

**Cosa ci si aspetterebbe.** Che le zucche adiacenti e cresciute vengano riaccorpate quando la configurazione cambia, o almeno che una cella raccolta e ripiantata possa rientrare nel quadrato più grande disponibile. Invece, se i gruppi vicini "a cavallo" dei candidati non vengono mai raccolti, la cella ripiantata ricade sempre nello stesso 1x1: ogni raccolto rende 1 × 1 × 1 × 512 = 512 zucche (livello 10) e ricrea la stessa situazione. È quanto osservato in gioco ("raccolto da 512 per sempre").

**Riproduzione (mondo 3x3, due droni, gioco normale o `simulate`).**
```
set_world_size(3)
clear()
# gruppo 2x2 fisso nelle celle (0,1),(1,1),(0,2),(1,2): si forma quando cresce l'ultima
for (x, y) in [(0,1),(1,1),(0,2),(1,2),(1,0),(2,1),(2,2)]:
    # spostarsi su (x,y), till(), plant(Entities.Pumpkin)
    ...
# attendere che tutte siano cresciute (eventuali morte: ripiantare)
# (1,0),(2,1),(2,2) restano gruppi 1x1 perché il 2x2 sporge da ogni candidato 2x2 che le contiene

def worker(x, y, ritardo):
    # vai su (x,y)
    while True:
        for i in range(ritardo): pass
        till(); till()               # soil
        plant(Entities.Pumpkin)
        while not can_harvest(): pass
        harvest()                    # rende sempre 1 zucca × YieldFactor
spawn_drone(worker, 2, 0, 3000)
worker(0, 0, 0)
```
Con lo sfasamento, quando una delle due zucche cresce l'altra è seme o vuota: il candidato 3x3 non è disponibile (`dp` richiede tutte le 9 celle cresciute), i candidati 2x2 che contengono (0,0) o (2,0) contengono una cella del 2x2 fisso che sporge → `HasOverlaps` → 1x1. Le due celle rendono 1 zucca per raccolto all'infinito. Nella classifica con 32 worker che raccolgono appena `can_harvest()` è vero, lo stesso schema si presenta ogni volta che una zucca morta è stata sostituita mentre il resto del campo era già raggruppato in modo "sbagliato".

**Impatto.** Alto per Pumpkins: la fusione 32x32 (3 145 728 zucche) avviene solo se, nell'istante in cui cresce l'ultima zucca, tutte le altre 1023 sono cresciute e presenti. Uno script che raccoglie prima della fusione completa o che gestisce le morte in modo asincrono può restare bloccato con rese da 512. Vedi B2 per un modo di accorgersene.

**Gravità.** Alta.

### A2 — Zucche: liberare una zucca cresciuta per vie diverse dal raccolto distrugge tutto il gruppo senza resa

**File e righe.** `Pumpkin.cs:82-86` (`OnFree` → `pumpkinController.RemovePumpkin(this, out _)`), `PumpkinController.cs:81-100` (`RemovePumpkin` itera `IterPositions(groups[p])` e chiama `gm.RemoveEntity(item)` su ogni cella del gruppo), `GridManager.cs:793-803` (`Free`), `Drone.cs:544-558` (`ChangeGround` → `RemoveEntity(pos, regrowGrass: false)`).

**Cosa fa il codice.** `RemovePumpkin` è usato sia dal raccolto (che raccoglie la resa restituita) sia da `OnFree`, che scarta il valore di ritorno. `Free` viene chiamato da `till()`, `set_world_size`, `clear()`, dinamite, `plant()` su entità sovrapiantabile, ecc. Quindi `till()` sotto una qualsiasi zucca di un gruppo 32x32 rimuove tutte le 1024 zucche a resa zero.

**Cosa ci si aspetterebbe.** Che `till()` rimuova la sola pianta sotto il drone (come per ogni altra entità), o che la rimozione forzata lasci intatte le altre zucche del gruppo (al più spezzando il gruppo).

**Riproduzione.** Campo di zucche cresciute e fuse; un drone esegue `till()` su una di esse: tutto il gruppo scompare, `num_items(Items.Pumpkin)` non cambia.

**Impatto.** Medio per Pumpkins: un `till()` errato (per esempio un worker che prepara il terreno su una cella già occupata) azzera un ciclo intero. Non è sfruttabile, è una trappola.

**Gravità.** Media.

### A3 — Girasoli: `hadIncorrectSunflowerHarvest` viene aggiornato anche raccogliendo un seme

**File e righe.** `Sunflower.cs:37-58` (`Harvest`), `Growable.cs:184-191` (`Growable.Harvest`: resa solo se `Harvestable`, rimozione sempre), `Drone.cs:506-526` (`Drone.Harvest` chiama `entity.Harvest()` per qualunque entità presente).

**Cosa fa il codice.** `Sunflower.Harvest` ricalcola `getBoost = (petali == massimo del campo) && (girasoli ≥ 10)` (`:43`), salva il vecchio flag, scrive il nuovo (`:45`, `= !getBoost`) e solo dopo annulla il bonus se il vecchio flag era sporco (`:46-49`). Tutto questo avviene prima di `base.Harvest`, cioè anche quando il girasole non è cresciuto e la resa sarà vuota. Nota: il massimo e il conteggio includono anche i semi (`cells … where f is Sunflower`).

**Cosa ci si aspetterebbe.** Che un raccolto a resa zero (seme) non modifichi lo stato della penalità, o perlomeno che la documentazione lo dica. Due conseguenze: (1) raccogliere un seme con petali diversi dal massimo "sporca" il flag e il prossimo girasole raccolto da chiunque perde il ×8; (2) raccogliere un seme con petali uguali al massimo "pulisce" il flag a costo zero di resa (vedi B3).

**Riproduzione.**
```
# campo con >= 10 girasoli cresciuti, tutti con petali < 15, più un seme da 15 appena piantato
harvest()   # sul seme da 15: resa 0, flag = pulito (era il massimo)
harvest()   # su un girasole da 14 cresciuto: resa 1 (14 != 15, flag = sporco)
harvest()   # su un girasole da 14 dopo aver tolto il 15: 14 è il massimo ma flag sporco → resa 1, flag pulito
```
Variante: `harvest()` su un seme da 9 quando il massimo è 15 → il successivo raccolto di un 15 cresciuto rende 1 invece di 8.

**Impatto.** Medio per Sunflowers (il reroll `harvest(); plant()` dei semi è la strategia naturale e interagisce con il flag globale condiviso da tutti i droni).

**Gravità.** Media.

### A4 — Girasoli: `GetYield()` (anteprima nel tooltip) ignora la penalità e ha un effetto collaterale

**File e righe.** `Sunflower.cs:61-69` (`GetYield` ricalcola `getBoost` senza guardare il flag e lo scrive nel campo), `:71-74` (`GetHarvestYield` → `base.GetYield()`, cioè `Growable.GetYield`, che usa il `getBoost` deciso in `Harvest`), `MainSim.cs:990-999` (il tooltip chiama `entity.GetYield()`).

**Cosa fa il codice.** Il raccolto applica la penalità correttamente (il flusso è `Harvest` → `base.Harvest` → `GetHarvestYield` → `Growable.GetYield`, che legge `getBoost` già corretto). L'anteprima invece mostra ×8 anche quando il raccolto renderà ×1. Inoltre passare il mouse su un girasole scrive `getBoost`; è innocuo perché `Harvest` lo ricalcola.

**Cosa ci si aspetterebbe.** Anteprima uguale alla resa.

**Riproduzione.** Rendere il flag sporco (A3), poi passare il mouse sul girasole con più petali: il tooltip mostra la resa ×8; `harvest()` rende ×1.

**Impatto.** Solo interfaccia.

**Gravità.** Bassa.

### A5 — Labirinto: il tesoro non viene mai posto nell'ultimo vicolo cieco trovato

**File e righe.** `BushPlant.cs:94-131` (DFS; `list2` raccoglie le celle in cui la ricerca torna indietro, cioè i vicoli ciechi, nell'ordine di scoperta), `:133` `int num12 = list2[sim.randomMaze.Next(list2.Count - 1)];`.

**Cosa fa il codice.** `Random.Next(n)` restituisce 0..n-1, quindi `Next(Count - 1)` esclude l'ultimo elemento. L'ultimo vicolo cieco aggiunto è l'ultimo ramo esplorato prima di esaurire lo stack, in genere vicino alla cella di partenza del DFS.

**Cosa ci si aspetterebbe.** `Next(list2.Count)`. Con `Count == 1` il codice funziona per caso (`Next(0)` → 0).

**Riproduzione.** Non osservabile direttamente senza il seme; statisticamente, su molti labirinti il vicolo cieco scoperto per ultimo non ospita mai il primo tesoro.

**Impatto.** Lieve distorsione della distribuzione della posizione iniziale del tesoro; nessun vantaggio pratico (con RNG crittografico il labirinto non è prevedibile).

**Gravità.** Bassa.

### A6 — `use_item(Items.Weird_Substance, n)` su cespuglio con `n < 2^(mazes-1)`: effetto applicato, ritorna `False`, costa 1 tick, non consuma nulla

**File e righe.** `Execution.cs:386-405` (ramo `weird_substance`, `entity2 is BushPlant`): `num4 = num2 / num3; if (num4 < 1) { bushPlant.ToggleWeird(); break; }` lascia `flag4 = false` e `useActionTicks = false`; a `:432-437` si ha `ReturnValue = False`, nessun `RemoveItem`, `ops = operationOps`. `Growable.cs:207-226` (`ToggleWeird` inverte `weird` del cespuglio e dei 4 vicini, consuma estrazioni di `randomVarious`).

**Cosa ci si aspetterebbe.** O l'azione fallisce senza effetti, o riesce consumando l'oggetto e costando 200 tick. La documentazione di `use_item` dice: "returns True if an item was used, False if … / takes 200 ticks if it succeeded, 1 otherwise".

**Riproduzione.** Con `mazes` al livello 6 (serve n multiplo di 32): su un cespuglio, `use_item(Items.Weird_Substance, 1)` → ritorna `False`, costo 1 tick, il cespuglio e i vicini diventano/tornano "weird", l'inventario non cambia.

**Impatto.** Nullo per la classifica Maze (sostanza strana illimitata, la stranezza non serve); fuori classifica permette di rendere strani i cespugli senza spendere.

**Gravità.** Bassa.

### A7 — Azioni senza effetto che costano 200 tick (o esito incoerente con la documentazione)

Tutte in `Execution.cs:236-1005` (`ApplySideEffect`) e nei metodi di `Drone`/`GridManager` chiamati:

1. **Riuso del tesoro durante il trasloco**: `Treasure.cs:53-57` (`if (repositioning) { useActionTicks = true; return false; }`) → `Execution.cs:406-413, 437`: ritorna `False` ma costa 200. Documentazione di `use_item`: "1 tick otherwise". Il primo riuso costa 200 e il trasloco dura `OpDuration × 200` (`Treasure.cs:66`); un secondo `use_item` entro 200 tick costa altri 200 per nulla.
2. **`till()` su terreno non arabile**: `Drone.cs:544-555` esce subito se `!isTillable`; `Execution.cs:288-292` addebita comunque `actionOps`. Atteso: 1 tick come le altre azioni fallite (il valore di ritorno è `None`, quindi lo script non può accorgersene).
3. **`swap()` fra due celle vuote**: `GridManager.cs:344-398` ritorna `true` quando entrambe le entità sono `null` (`:359` passa, `:371-396` non fa nulla) → 200 tick, `True`.
4. **`harvest()` su `Dinosaur` o `Apple`**: `Entity.cs:118-122` (`Harvest` base restituisce `null` e non rimuove), `Apple.cs:10-16` (`Harvestable = false`, resa vuota, nessuna rimozione), `Dinosaur.cs` non ridefinisce `Harvest`; `Drone.cs:506-513` ritorna `true` → 200 tick, nessun effetto. La documentazione di `harvest` dice "If you harvest an entity that can't be harvested, it will be destroyed": vale per semi, zucche morte, siepi, non per coda e mela.
5. **`set_world_size(n)` con `n` uguale alla taglia corrente**: `Execution.cs:617-628`, 200 tick senza effetto (coerente con la doc, che però dice "only if the size has actually changed" riferendosi al reset).

**Impatto.** Basso: sono tick persi solo da script errati; il punto 1 riguarda chi fa polling del tesoro con `use_item` invece di `can_harvest()`.

**Gravità.** Bassa.

### A8 — Errore runtime durante una run di classifica: la run resta sospesa invece di chiudersi come fallita

**File e righe.** `Execution.cs:741-755` (`SideEffect.Error` → `sim.Error()`), `Simulation.cs:203-207` (`Error`: `hasError = true; Paused = true`), `Simulation.cs:233-241` (`RunNextStep`: con `Paused` esce subito, quindi il ramo `if (IsExecuting() && hasError) StopProgramExecution()` a `:243-246` non viene mai raggiunto), `MainSim.cs:262-265` (`LeaderboardExecutionFinished` è chiamato solo quando `!sim.IsExecuting()`), `:550-566` (`StopMainExecution` imposta `leaderboardCancelled`).

**Cosa fa il codice.** Un'eccezione in qualsiasi drone mette in pausa la simulazione con l'overlay di classifica attivo; la run non viene né chiusa né conteggiata finché l'utente non preme stop, e allora viene registrata come annullata (fallita).

**Cosa ci si aspetterebbe.** Chiusura automatica della run come fallita (o come riuscita se l'obiettivo è già raggiunto: oggi non è possibile, perché il controllo `Items.Contains(goalItems)` a `MainSim.cs:469` avviene solo alla fine naturale).

**Riproduzione.** `leaderboard_run(Leaderboards.Hay, "f", 1000)` con `f` = `x = 1 / 0`.

**Impatto.** Nessun vantaggio; esito corretto (fallimento) ma raggiunto solo con intervento manuale.

**Gravità.** Bassa.

### A9 — `change_hat` verso un cappello con `preventHover` mentre il drone è in hover: fallisce in silenzio

**File e righe.** `Execution.cs:475-494`: se `hatSO.preventHover` e il drone non è già a quota 1 con cappello `preventHover`, chiama `drone.Hover(1, out ops)` e cambia cappello solo se riesce; `Drone.cs:237-248` (`Hover` fallisce, 1 tick, se il cappello attuale ha `preventHover` o se c'è un bambù più alto). In caso di fallimento `ReturnValue = None`, nessun avviso, cappello invariato.

**Impatto.** Nessuno in classifica (hover non serve); fuori classifica può confondere.

**Gravità.** Bassa.

### A10 — `Treasure.SetValues`: il valore `nextY` viene scritto in `nextPos.x`

**File e righe.** `Treasure.cs:170-173`: `if (values.ContainsKey("nextY") …) nextPos.x = result3;`.

**Impatto.** Solo caricamento dei salvataggi: la destinazione del prossimo trasloco perde la coordinata y. Nessun effetto in classifica (le run partono da zero).

**Gravità.** Bassa.

---

## (B) Comportamenti non documentati sfruttabili in classifica

### B1 — `clear()` come interruttore di fine run

**File e righe.** `Execution.cs:519-535` (`SideEffect.Clear`: `RemoveSpawnedDrones`, `ClearGrid`, `States.RemoveAll(s != MainState)`, `MainState = States[droneId]`, `DroneId = 0`, costo 200 al chiamante), `Execution.cs:708-739` (`Terminated`: la run finisce quando tutti gli stati sono `null`), `MainSim.cs:455-485` (tempo registrato = `sim.CurrentTime` quando l'esecuzione si è fermata; successo = `Items.Contains(goalItems)` valutato in quel momento; `clear()` non tocca l'inventario).

**Comportamento.** Il tempo della run è l'istante in cui termina l'ultimo drone. Senza `clear()` ogni worker deve accorgersi da solo del raggiungimento dell'obiettivo (polling di `num_items`, 1 tick a chiamata più il resto del ciclo) e finire l'iterazione in corso (per uno schema plant/harvest/move sono alcune centinaia o migliaia di tick, cioè 0,05-0,3 s). Con `clear()` il drone che rileva l'obiettivo termina tutti gli altri all'istante e la run si chiude al suo `OpCount + 200`. La documentazione di `clear` descrive la distruzione dei droni ma non nel contesto delle classifiche. Dettaglio ulteriore: `clear()` può essere chiamato da un drone generato; in quel caso il programma principale viene ucciso e il chiamante diventa il drone 0 (`MainState = States[droneId]`).

**Riproduzione.** Nel ciclo del main: `if num_items(Items.Hay) >= 2000000000: clear()` e poi `return`.

**Impatto.** Medio: su run da ~108 s (Hay) un guadagno fino a ~0,3 s è dello stesso ordine della distanza fra le prime posizioni.

### B2 — `measure()` su una zucca restituisce il "numero misterioso", identico per tutte le zucche dello stesso gruppo

**File e righe.** `Pumpkin.cs:88-91` (`Measure` → `mysteriousNumber`), `:79` (assegnato in `OnRestart`), `PumpkinController.cs:163-169` (`MergeWithOthers` copia il numero della prima cella del quadrato su tutte le celle del gruppo).

**Comportamento.** La documentazione di `measure` dice che per le entità non elencate ritorna `None`; per le zucche ritorna invece un numero, e dopo la fusione tutte le zucche di un gruppo condividono lo stesso valore. Quattro `measure()` sugli angoli (4 tick) bastano a stabilire se il gruppo 32x32 si è formato (quattro angoli nello stesso gruppo quadrato ⇒ il quadrato è l'intero campo). È anche l'unico modo di rilevare lo stallo descritto in A1 (una zucca il cui numero non coincide con quello dei vicini cresciuti).

**Riproduzione.**
```
a = measure()                 # su (0,0)
# spostarsi su (31,31)
b = measure()
if a == b: harvest()          # il gruppo contiene entrambi gli angoli
```

**Impatto.** Medio per Pumpkins.

### B3 — Girasoli: la penalità si paga una volta per serie di errori, non per errore; un seme "massimo" la azzera gratis

**File e righe.** `Sunflower.cs:43-49`.

**Comportamento.** Il flag è un singolo booleano globale (`GridManager.cs:74`): N raccolti sbagliati consecutivi costano un solo bonus (il primo raccolto corretto successivo rende ×1 e ripulisce il flag). Combinato con A3: raccogliere un seme con petali uguali al massimo del campo (resa zero in ogni caso) ripulisce il flag senza perdere alcun bonus su un girasole cresciuto. Lo schema "reroll di molti semi, poi un raccolto su un seme massimo, poi raccolti ×8" neutralizza la penalità per 200 tick e un seme.

**Impatto.** Medio per Sunflowers.

### B4 — Il power viene consumato dalle azioni anche in classifica; velocità dimezzata finché il power è zero

**File e righe.** `Execution.cs:165-212` (`UsedPower += opsConsumati / 200 / 30`), `Farm.cs:421-436` (`UsePower` ogni 0,2 s: toglie `UsedPower`, se non basta azzera il power, e se `SpeedFactor > MaxSpeedFactor()` rallenta), `Farm.cs:406-414` (`MaxSpeedFactor` = 1,5^speed × 2 se power > 0), `Farm.cs:130-145` (`CollectItems`: quando il power passa da 0 a > 0 e la velocità è al massimo, raddoppia).

**Comportamento.** Ogni azione da 200 tick costa 1/30 di power; a 6075 tick/s un drone consuma ≈ 1 power/s, 32 droni ≈ 32 power/s. Per le classifiche con 1e9 power iniziale è irrilevante. Per **Sunflowers** (obiettivo 100 000 power, power iniziale 0): (1) la simulazione gira a metà velocità finché non si raccoglie il primo girasole; (2) su una run di ~180 s si bruciano ≈ 6 000 power, cioè ≈ 6 % dell'obiettivo, da compensare con ≈ 750 raccolti ×8 in più; (3) se il consumo supera l'incasso il power torna a 0 e la velocità si dimezza (oscillazione possibile nei primi round). Il debito non viene mai riportato in negativo (`SetNumber(0)`). Nulla di questo è in `__builtins__.py`.

**Impatto.** Medio per Sunflowers (va messo nel conto dei raccolti necessari e del numero di droni attivi).

### B5 — Labirinto: ogni riuso del tesoro apre muri; dopo 300 riusi sopravvive il 55 % dei muri

**File e righe.** `Treasure.cs:105-128` (`CompleteRepositioning`: per ogni cella con `(i + j) % 2 == 0` e per ognuna delle 4 direzioni, `randomMaze.NextDouble() <= 0,002` apre il muro da entrambi i lati), `:47-68` (`RepositionTreasure`: resa incassata subito, trasloco completato dopo 200 tick), `:49` (massimo 300 riusi: `treasureFactor >= 301`).

**Comportamento.** Ogni adiacenza interna viene esaminata esattamente una volta per riuso (ha un solo estremo "pari"), quindi ogni muro superstite si apre con p = 0,002 a ogni riuso: 0,998^300 ≈ 0,548. In un 32x32 (961 muri interni dopo la generazione dell'albero) ne restano ≈ 527 dopo 300 riusi; il labirinto finale è quasi un campo aperto e i riusi finali costano pochissime mosse. Non documentato in `__builtins__.py` (né il tetto di 300 riusi).

**Impatto.** Medio per Maze (strategia: percorsi lunghi all'inizio, riusi rapidi alla fine; con più droni sparsi conviene memorizzare i muri aperti via `can_move`).

### B6 — Labirinto: generazione su cespuglio non cresciuto; 300 riusi per labirinto indipendentemente dalla taglia

**File e righe.** `Execution.cs:386-405` (nessun controllo `Harvestable` sul cespuglio), `BushPlant.cs:8` (`GenerateHedgeMaze` non controlla la crescita), `Treasure.cs:40-45,61` (resa = `dropAmount × lato² × YieldFactor`), `:49` (300 riusi per tesoro).

**Comportamento.** (1) Si può trasformare il cespuglio in labirinto subito dopo `plant()`, senza attendere i 4 s di crescita. (2) La resa per riuso è ∝ lato², ma il numero di riusi (300) e il costo per riuso (`lato × 2^(mazes-1)` sostanza strana) sono per labirinto: 16 labirinti 8x8 danno 16 × 301 × 64 × 32 = 9 863 168 oro, esattamente l'obiettivo, con percorsi ≈ 4 volte più corti e 2 droni per labirinto; la generazione sovrascrive le siepi di altri labirinti (`SetEntity` → `HedgePlant.OnFree` → `RemoveMaze`), quindi i quadrati non devono sovrapporsi. Nessuno dei due punti è documentato.

**Impatto.** Medio per Maze.

### B7 — Cactus: la taglia è memorizzata nella cella finché un cactus non vi cresce; `swap` sposta anche il numero; `till` non lo azzera

**File e righe.** `Cactus.cs:230-234` (`OnRestart`: estrae solo se `cactusNumber == -1`), `:35-39` (`OnFullyGrown` lo rimette a -1), `GridManager.cs:368-370` (`Swap` scambia `cactusNumber`), `Drone.cs:556-558` (`till` rimuove l'entità senza toccare la cella), `GridManager.cs:335-338` (`GenerateWorld` copia il numero e poi lo azzera subito: la copia è codice morto).

**Comportamento.** Raccogliere o estirpare un seme e ripiantare dà la stessa taglia; il "reroll" è possibile solo dopo la crescita completa (1 s senz'acqua). È plausibilmente voluto, ma non è documentato ("Cacti come in 10 different sizes").

**Impatto.** Basso (noto dalle note precedenti; decide la struttura degli script di ordinamento).

---

## (C) Curiosità innocue e discrepanze di documentazione

**C1 — `send`, `receive`, `get_drone_id` esistono ma non sono richiamabili.** `BuiltinFunctions.cs:807-861` definisce `Send` e `Receive`, `:786-791` `GetDroneId`; `Execution.cs:29` ha `MessageChannel`, `:669-672` il caso `SideEffect.GetDroneId`; `ProgramState.cs:83-86` ha `AllMessagesQueue` e `MessageQueues[36]`. Nessuno dei tre è in `functionList` (`:10-72`), che è l'unica fonte dei nomi registrati nello scope (`Execution.cs:65-68`), quindi chiamarli dà "name not defined". Inoltre non esiste alcun codice che travasi i messaggi da `MessageChannel` alle `MessageQueues` del destinatario: anche registrandoli, `receive` restituirebbe sempre `None`. Le stringhe `"send"`, `"receive"`, `"get_drone_id"` in `resetUnlocks` (`:87-94`) sono sblocchi senza effetto. Funzionalità incompleta, nessun impatto.

**C2 — Discrepanze fra `__builtins__.py` e codice.**
- Girasoli: doc "5x bonus power", codice `8.0 * base.YieldFactor` (`Sunflower.cs:26`).
- Zucche: doc "number of pumpkins in the mega pumpkin cubed", codice `lato² × min(lato, 6) × YieldFactor` (`Pumpkin.cs:58-60`): il cubo vale solo fino al lato 6; per il 32x32 la resa è 1024 × 6 × 512, non 32³ × 512.
- Tesoro: doc "gold equal to the side length of the maze", codice `lato²` (`Treasure.cs:40-45, 61`).
- `measure`: doc "all other entities … None", le zucche restituiscono un numero (B2).
- `harvest`: doc "will be destroyed", coda del dinosauro e mela non vengono distrutte (A7.4).
- `use_item`: doc "1 tick otherwise", il riuso del tesoro fallito durante il trasloco costa 200 (A7.1).
- `spawn_drone`: la doc dice che gli argomenti sono copiati; non dice che anche l'intero scope globale (variabili e funzioni) viene copiato in profondità al momento dello spawn (`Scope.cs:69-82`, `PyFunction.cs:48-59`, `Execution.cs:643-656`): dizionari o liste globali non sono condivisi fra droni.
- `wait_for`: doc "1 + remaining task ticks"; in realtà il drone in attesa viene escluso dallo scheduler (`Execution.cs:121, 129, 159`) e alla fine riparte con `OpCount = GlobalOpCount` (`:712-716`): nessun tick accumulato, ma nessuna perdita.
- Cappello del dinosauro: le note precedenti riportano "~100" mosse; il costo parte da 400 e scende di `floor(ops × 0,03)` per mela fino a 33 dopo 99 mele (`DinosaurHat.cs:18, 125`).

**C3 — Durata del tick arrotondata per eccesso.** `Simulation.cs:224`: `ceil(2 500 000 / 15,1875) = 164 610 ns` invece di 164 609,05: 6075 tick valgono 1,0000057 s simulati; su una run di 2 minuti ≈ 0,7 ms. Il punteggio inviato è `(int) media.TotalMilliseconds` (`LeaderboardManager.cs:92`).

**C4 — Seme e RNG.** Dal 4 nov, per `leaderboardType ∈ {reset, farm_resources}` tutti i flussi casuali sono `BufferedCryptoRandom` (`Simulation.cs:141-162`), che usa `RandomNumberGenerator.Fill` e tratta il seme solo come sale (`BufferedCryptoRandom.cs:18-32`): il seme calcolato per le run successive (`MainSim.cs:488`, somma dei `Next()` con overflow e `Mathf.Abs`) non ha alcun effetto sulle estrazioni. La predizione dell'RNG in classifica non è più possibile. `Mathf.Abs(int.MinValue)` resta negativo e porta a `new Random()`: innocuo.

**C5 — Tempo di esecuzione in classifica: cosa conta e cosa no.** `MainSim.cs:455-493`: successo = `Items.Contains(goalItems)` alla fine; le run si ripetono finché il tempo simulato cumulato raggiunge 7200 s (`:479`) e si invia la **media** (`:481`); una sola run fallita o annullata chiude l'invio come fallito; il `speedup` di `leaderboard_run` è solo `TimeFactor` (`:154-175`, limitato a 1e6) e non tocca la simulazione. `set_execution_speed`, `set_world_size`, `clear()` sono permessi in classifica (`Execution.cs:519, 601, 617`) ma nessuno dei primi due dà vantaggi (la velocità può solo scendere; mondi più piccoli riducono la resa per ciclo in tutte le classifiche esaminate).

**C6 — Interprete (Utils).** Indici: `IPyIndexable.cs:16-37, 78-86`: l'indice è un double troncato con `(int)`; `l[0.5]` → `l[0]`, `l[-0.5]` → `l[len-1]` (via `len + (-0,5)` poi troncamento). `pop(l, 1.7)` usa `floor`. Aritmetica: `/` è divisione reale, `//` = `Math.Floor(a / b)`, `%` con segno di Python (`PyNumber.cs:17-26`), `**` = `Math.Pow`, divisione per zero → errore (`BinaryExprNode.cs:101`); i confronti fra numeri usano `==` sui double (`0.1 + 0.2 != 0.3` come in Python). `(int)(double)` su valori fuori dall'intervallo int (es. `use_item(Items.Water, 1e10)`, `hover(1e10)`, `set_world_size(1e10)`) dà `int.MinValue` su Mono/x64: `use_item` lancia l'errore "negativo" (`BuiltinFunctions.cs:314-317`), `hover` fallisce, `set_world_size` non cambia nulla ma costa 200 e riposiziona i droni.

**C7 — `use_item(Items.Water, n)` consuma `n` anche se l'acqua viene limitata a 1.** `Drone.cs:660-674` ritorna sempre `true`, `GridManager.cs:245` `Math.Clamp(volume, 0, 1)`, `Execution.cs:433-436` rimuove `n`. Coerente con la doc ("use the item n times") ma senza rimborso. Analogamente `use_item(Items.Weird_Substance, 1e9)` su un cespuglio in un mondo 32x32 consuma 1e9 sostanza e genera un 32x32 (`Execution.cs:391-403`: la divisione intera e l'avviso "not divisible" non impediscono il consumo totale).

**C8 — `Growable.Fertilize` con `n` enorme.** `Growable.cs:202`: `2 * number` è una moltiplicazione `int`; per `n > 1 073 741 823` va in overflow negativo e `grownPercent` diventa negativo (crescita più lunga). Serve avere più di 1e9 fertilizzante: irraggiungibile in classifica (nessuna partenza con fertilizzante). Nota: il fertilizzante rende sempre la pianta "weird" (`:195`, resa dimezzata), anche su pianta già cresciuta.

**C9 — Cactus: anteprima diversa dal raccolto.** `Cactus.cs:84-86` (`GetYield` → `CountSorted`, flood fill che richiede `IsSorted()` di ogni cactus visitato e del cactus di partenza) contro `:14-32, 103-129` (`Harvest` → `Pop`: il cactus di partenza non viene controllato, si propaga ai 4 vicini solo se tutti i vicini sono ordinati, poi ricorsivamente). Un cactus non ordinato mostra 0 nel tooltip ma rende 1² × YieldFactor. Un vicino non cresciuto conta come non ordinato (`:171-186`) e blocca la propagazione.

**C10 — Scheduler.** `Execution.cs:96-234`: tutti i droni al minimo `OpCount` agiscono nello stesso passaggio in ordine di indice crescente; `spawn_drone` costa 200 al chiamante e il nuovo drone parte da `GlobalOpCount + 200` (`:655`); se tutti i droni sono in `wait_for` reciproco, `Min` su insieme vuoto → `GlobalOpCount = num` (`:129-134, 220-225`) e il tempo simulato avanza all'infinito senza errore. `print`, `do_a_flip`, `pet_the_piggy` costano `floor(1 s / OpDuration)` tick (6075) ma non consumano power (`:756-777`, `flag = false` → `AddAndConsumeOps`).

**C11 — Cappello del dinosauro fuori dalla sua classifica.** Lo sblocco `dinosaurs` al massimo rende disponibile `Hats.Dinosaur_Hat` in tutte le classifiche `everythingUnlocked` (`BuiltinFunctions.cs:620-685`, `Farm.cs:324-344`); ma le mele costano cactus (`DinosaurHat.cs:22-26`), quindi senza cactus in inventario il costo per mossa resta 400 (`:18`) e ogni mossa con coda converte la cella lasciata in `soil` (`Dinosaur.cs:50-58`). Nessun vantaggio. Un solo cappello alla volta (`:34-37`). `till()` sotto un segmento di coda da parte di un altro drone equivale a `change_hat` del dinosauro (`Dinosaur.cs:60-67` → `OnUnequip` → incasso delle ossa `:56-81`).

**C12 — Power: debito perdonato.** `Farm.cs:425-428`: se il power non basta per coprire `UsedPower` viene azzerato, mai negativo; fra un `UsePower` e l'altro (0,2 s) si corre a velocità doppia anche con saldo di fatto negativo.

**C13 — `clear()` e `set_world_size` non azzerano `hadIncorrectSunflowerHarvest`** (è un campo di `GridManager`, `GridManager.cs:74`, e la griglia non viene ricreata). Una nuova run di classifica crea una nuova `Simulation`, quindi parte pulita.

**C14 — Fine naturale di una funzione.** `FunctionNode.cs:93` imposta `ReturnValue = None` quando una funzione termina senza `return`: `wait_for` su un drone la cui funzione finisce senza `return` restituisce correttamente `None` (verifica negativa).

---

## Verifiche con esito negativo (comportamenti controllati e risultati coerenti)

- `use_item` con `n < 1` o `n` frazionario: `n` troncato a int, errore se < 1 (`BuiltinFunctions.cs:296-323`); `Items.Contains(id, n)` e `RemoveItem` ricevono lo stesso `n` (eccetto la dinamite, forzata a 1 dopo il controllo: `Execution.cs:422-430`).
- `plant()` su cella occupata: fallisce con 1 tick salvo `canBeOverplanted` (erba, zucca morta), nel qual caso l'entità precedente viene liberata senza resa (`Drone.cs:577-600`, `GridManager.cs:586-595`).
- `harvest()` su seme di cactus/girasole/zucca: 200 tick, resa 0, entità rimossa (`Cactus.cs:14-23`, `Growable.cs:184-191`, `Pumpkin.cs:44-52` via `RemovePumpkin` fuori gruppo).
- `harvest()` sul tesoro in trasloco: 200 tick, resa vuota, tesoro non rimosso (`Treasure.cs:16-23`).
- Crescita con acqua che cambia: `StopGrowing` accumula la frazione già cresciuta e `TryScheduleGrow` riprogramma il residuo con il nuovo tempo (`Growable.cs:106-159`); `grownPercent` non può superare 1 né (salvo C8) scendere sotto 0.
- Decadimento acqua: ogni 0,1 s, per cella, con p = 0,1, `× 0,99` (`GridManager.cs:260-272`).
- `spawn_drone` oltre il massimo: `None`, 1 tick (`Execution.cs:633-642`). `wait_for` su un handle già finito: copia profonda del valore, 1 tick (`:681-696`).
- `swap` di piante in crescita: la crescita continua (`GridManager.cs:371-396`, `UpdateFarmObject`); il companion delle piante non è coinvolto perché solo i cactus sono `canBeSwapped` (dato da asset, non verificato qui).
- `HasCompanion` guarda solo il **tipo** presente nella cella companion al momento del raccolto, anche se seme (`Growable.cs:233-244`): già noto.
- Resa/ossa/oro degli obiettivi: 32x32 ordinato → 1024² × 32 = 33 554 432 cactus; 1023 segmenti → 1023² × 32 = 33 488 928 ossa (`DinosaurHat.cs:83-88`); 301 × 32² × 32 = 9 863 168 oro; tutti uguali agli obiettivi delle classifiche.
- `ItemBlock` usa `double` (`ItemBlock.cs`): nessun overflow intero; `Contains` è `>=`; `Remove` fallisce invece di andare in negativo.
- La condizione di successo del tipo `reset` è `IsUnlocked("leaderboard")` per `fastest_reset` e `IsUnlocked("underground_leaderboard")` altrimenti (`MainSim.cs:468`).
