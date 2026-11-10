# The Farmer Was Replaced: risultati dell'analisi RNG / classifica Hay

Analisi statica, in sola lettura, di `TheFarmerWasReplaced_Data/Managed/{Core,Utils,mscorlib}.dll`
e dei dati serializzati in `resources.assets`. Il gioco non è stato avviato.

I numeri di riga si riferiscono al disassemblato ottenuto con
`monodis Core.dll > Core.il` (idem `Utils.il`, `mscorlib.il`); gli offset `IL_xxxx` sono
quelli del metodo e non dipendono dallo strumento.

Legenda affidabilità: **[IL]** letto direttamente nel codice, **[asset]** letto dai dati
serializzati, **[gioco]** confermato in partita, **[non tracciato]** non verificato.

## Valori utili per la classifica Hay

| Grandezza | Valore | Fonte |
|---|---|---|
| Obiettivo `hay` (multi-drone, Steam `hay_multi`) | 2 000 000 000 fieno | [asset] |
| Obiettivo `hay_single` | 100 000 000 fieno | [asset] |
| Oggetti iniziali | power 1 000 000 000 | [asset] |
| Sblocchi | tutti al massimo (`everythingUnlocked`) | [asset] |
| Mondo | 32×32 (multi), 8×8 (single) | [IL] |
| Droni massimi | 32 = `1 << megafarm(5)` (multi) | [IL] |
| Resa erba senza companion | 512 | [IL]+[asset] |
| Resa erba con companion | 81 920 (= 512 × 160) | [IL]+[asset] |
| Raccolti con companion per l'obiettivo multi | 24 415 | calcolo |
| Fattore di velocità | 15,1875 = 1,5⁵ × 2 | [IL]+[asset] |
| Durata di un tick | 164 610 ns, cioè 6075 tick al secondo simulato | [IL] |
| Azione da 200 tick | 0,0329 s simulati | calcolo |
| Crescita erba asciutta | 0,5 s = 3037,5 tick | [IL]+[asset] |
| Crescita erba con acqua 1,0 | 0,1 s = 607,5 tick | [IL] |

## 1. Seed quando viene passato -1

Nessun `TickCount`, nessun orologio: entropia del sistema operativo.

- `Simulation::.ctor` (Core.il 21961-22076): a `IL_0060` controlla `seed >= 0`; se sì
  `new Random(seed)` (`IL_0068`), altrimenti `new Random()` (`IL_0075`).
- `System.Random::.ctor()` (mscorlib.il, fino a riga 156781): `call GenerateSeed()` poi
  `.ctor(int32)`.
- `Random::GenerateSeed` (fino a riga 157091): legge il campo `[ThreadStatic] t_threadRandom`
  (riga 156765). Se è nullo lo crea con seed `s_globalRandom.Next()` sotto lock
  (`IL_0009`-`IL_0038`). Restituisce `t_threadRandom.Next()` (`IL_003e`).
- `Random::.cctor` (fino a riga 157330): `s_globalRandom = new Random(GenerateGlobalSeed())`.
- `Random::GenerateGlobalSeed` (fino a riga 157108): `Interop.GetRandomBytes(&int, 4)`.
- `Interop::GetRandomBytes` (mscorlib.il 251-276): `BCryptGenRandom(IntPtr.Zero, buf, len, 2)`,
  P/Invoke su `BCrypt.dll` (riga 1705).

Conseguenze:

- Il seed master di una run con -1 è un valore a 31 bit non prevedibile a priori.
  Sotto Proton `BCryptGenRandom` è servito da Wine, che attinge al generatore casuale
  dell'host [non tracciato: non ho letto il codice di Wine].
- `t_threadRandom` vive per tutto il processo: ogni `new Random()` sullo stesso thread è
  l'uscita successiva dello stesso generatore di Knuth. In teoria 55 seed master consecutivi
  permetterebbero di prevedere i successivi, ma un seed master non è osservabile dal codice
  di gioco.

## 2. Classifica Hay: numero di run, tempo inviato, seed

`MainSim::LeaderboardExecutionFinished` (Core.il 19245-19468), chiamato da
`MainSim::Update` (riga 18541). Per le leaderboard di tipo `farm_resources` (3):

1. Successo della run = `farm.Items.Contains(leaderboard.goalItems)` (`IL_006f`-`IL_0099`).
2. `totalLeaderboardTime += sim.CurrentTime` (`IL_00a0`-`IL_00b7`), `numLeaderboardRuns++`
   (`IL_00bc`-`IL_00c5`).
3. Se `totalLeaderboardTime >= 0x68c61714000 ns` (7200 s simulati) **oppure** la run è
   fallita o annullata (`IL_00db`-`IL_00f7`): invia e si ferma.
4. Tempo inviato = `totalLeaderboardTime / numLeaderboardRuns`, cioè la **media**
   (`IL_0117`-`IL_012d`, `StopLeaderboardRun(success, nome, nomeSteam, media)`).
5. Altrimenti parte un'altra run (`IL_0147`-`IL_0207`).

Quindi le run non sono un numero fisso: si ripetono finché il tempo simulato cumulato
arriva a 2 ore. Con run da circa 1 minuto sono circa 120 run per invio, e conta la media.
Una sola run fallita chiude l'invio come fallito.

Seed delle run successive (`IL_015f`-`IL_01fb`), sempre concatenato:

```
seed = Abs( various.Next() + sunflower.Next() + snake.Next() + random.Next()
          + pumpkin.Next() + poly.Next() + maze.Next() + cactus.Next() )   // somma int32 con overflow
```

Dipende dallo stato finale di ogni flusso, quindi da quante estrazioni ha consumato la run.
La prima run usa -1: `BuiltinFunctions::LeaderboardRun`, `ldc.i4.m1` a `IL_00b0` (riga 24889).
In `tfwr_rng.py` è `SimulationRng.next_leaderboard_seed()`.

Definizioni lette dagli asset (`LeaderboardSO`, campi a Core.il 11317): tutte le leaderboard
sono tipo 3, `everythingUnlocked = 1`. `hay`: `singleDrone = 0`, obiettivo hay 2e9.
`hay_single`: `singleDrone = 1`, obiettivo hay 1e8.

Sblocchi con `everythingUnlocked` (`BuiltinFunctions::GetUnlockStrings`, Core.il 24908-25176):
per ogni sblocco aggiunge prima `"nome"` e poi `"nome_livelloMassimo"` (`IL_0136`, `IL_01a0`).
In single-drone salta `megafarm` e forza `expand_5` (`IL_014f`-`IL_017d`).

Livelli massimi [asset]: grass 10, polyculture 5, speed 5, expand 9, megafarm 5,
watering 9, trees 10, carrots 10, fertilizer 4.

### Estrazioni di `poly` consumate all'avvio

`Farm::.ctor` (Core.il 13974-14196) crea la griglia a `IL_0052`, **prima** di applicare
gli sblocchi (`IL_007b` e seguenti). `Farm::Unlock` (14834-14930) rigenera il mondo a ogni
cambio di livello di `expand` (`IL_0078`, `GenerateWorld` → `ClearGrid(true)`).

Con la doppia stringa `expand` + `expand_9` la sequenza è 1×1 → 1×3 → 32×32.
**[gioco]** Confermato con `simulate(seed=12345)`: 5506 estrazioni di `poly` prima del
primo companion osservato, unica sequenza compatibile su 512 provate.
Per `hay_single` la sequenza attesa è 1×1 → 1×3 → 8×8 [IL, non provata in gioco].

## 3. Scheduler dei droni

`Execution::Execute` (Core.il 27969-28602). Gli stati dei droni stanno in
`Execution.States`, lista indicizzata per id del drone.

Ciclo (etichetta `IL_007d`):

1. Orizzonte = `floor(GlobalOpCount + min(199, tempoDisponibile / OpDuration))`
   (`IL_0008`-`IL_0032`).
2. **Fase codice** (`IL_00a2`-`IL_012b`): per indice crescente, ogni drone che non ha
   un'azione pendente, non è in attesa e ha `OpCount <= orizzonte` esegue
   `PerformExecutionStep`, cioè interpreta codice finché incontra un'azione o supera l'orizzonte.
3. `GlobalOpCount` = minimo di `OpCount` tra i droni non in attesa (`IL_0133`-`IL_0180`,
   predicato `b__35_0` a riga 30485).
4. **Fase azioni** (`IL_0363`-`IL_04f9`): per indice crescente, il drone con un'azione
   pendente e `OpCount <= GlobalOpCount` (`IL_041b`-`IL_0432`) esegue `ApplySideEffect`.
   `GlobalOpCount` non viene ricalcolato dentro questo ciclo.
5. Ricalcolo del minimo e avanzamento del tempo simulato (`IL_052e`-`IL_05d0`), poi da capo.

Risposte:

- **Ordine**: per contatore di tick del drone nel momento in cui chiama l'azione. A parità
  di tick, tutti i droni pari al minimo agiscono nello stesso passaggio in ordine di
  **indice crescente** (id più basso per primo), e in quell'ordine ricevono le estrazioni
  di `poly`.
- **Momento dell'effetto**: l'effetto avviene all'inizio dell'azione; il costo (200) viene
  aggiunto a `OpCount` subito dopo (`ApplySideEffect`, `IL_1485`-`IL_14a3`, riga finale del
  metodo 28605-30388). Il companion della ricrescita è quindi estratto al tick in cui
  `harvest()` viene chiamato, non 200 tick dopo.
- **Indice dei droni**: `Farm::AddDrone` (15344-15431) riusa il primo slot libero
  (`IL_000e`-`IL_004a`), altrimenti accoda. Un drone nuovo nasce nella posizione di chi lo
  genera e parte con `OpCount = GlobalOpCount + 200` (`IL_0dee`-`IL_0dfd`, riga 29832).
- **Costi**: sono decisi in `ApplySideEffect` per le azioni e dal valore di ritorno dei
  builtin per le funzioni pure.

| Chiamata | Tick | Riga Core.il |
|---|---|---|
| `harvest()` con un'entità sotto il drone (anche non matura) | 200 | 28605+, `IL_010f` |
| `harvest()` su cella senza entità | 1 | `IL_0104` |
| `plant()` riuscito / fallito | 200 / 1 | `IL_01f9` / `IL_01ee` |
| `till()` | 200 | `IL_02b3` |
| `swap()`, `use_item()` riusciti / falliti | 200 / 1 | `IL_0198`, `IL_0669` |
| `clear()`, `set_world_size()` | 200 | `IL_08bf`, `IL_0c9e` |
| `spawn_drone()` riuscito / limite raggiunto | 200 / 1 | `IL_0e77` / `IL_0d39` |
| `can_harvest()`, `get_companion()`, `wait_for()`, `has_finished()` | 1 | `IL_0144`, `IL_099e`, `IL_0f98`, `IL_0fce` |
| `random()`, `len()`, `abs()`, `range()`, `send()`, `receive()` | 1 | builtin, `ldc.r8 1.` |

Il costo delle singole espressioni e istruzioni dell'interprete (somme, confronti,
assegnazioni) non l'ho tracciato nodo per nodo [non tracciato].

## 4. Condivisione di dati tra droni

Caso `SPAWN_DRONE` di `ApplySideEffect` (Core.il 29739-29888):

- La funzione passata viene **copiata in profondità** (`PyFunction::DeepCopy`, `IL_0d67`),
  e così ogni argomento (`IL_0dbe`). Il nuovo drone riceve un `ProgramState` nuovo e uno
  scope costruito sul `parentScope` della funzione copiata (`IL_0e14`-`IL_0e25`).
  Le variabili globali sono quindi una copia al momento dello spawn, non condivise.
  Non ho letto `PyFunction::DeepCopy` per confermare che copi anche lo scope padre
  [non tracciato], ma è coerente con l'uso del dizionario di memoizzazione.
- Ogni drone nuovo prende un generatore `random()` proprio, seminato da
  `Simulation.randomRandom.Next()` (`ProgramState::.ctor`, Core.il 53449-53542, `IL_00d8`).
- `wait_for(handle)`: restituisce una copia profonda del valore di ritorno del drone
  (`IL_0f5a`-`IL_0f77`); se non ha finito mette chi chiama in attesa (`IL_0f8e`-`IL_0f93`).
  Chi è in attesa accumula 1 tick per passo (`PerformExecutionStep`, 53575-53754, `IL_001d`-`IL_0051`).
- `has_finished(handle)`: booleano, 1 tick.
- Esistono nel codice anche `send(valore, idDrone)` e `receive([idDrone])`
  (`BuiltinFunctions::Send` 25613-25699, `Receive` 25702-25832): una coda di messaggi
  ordinata per `OpCount` del mittente, `receive` restituisce `None` se la coda è vuota.
  Sono registrati tra i builtin (riga 27470), ma non ho verificato se sono disponibili al
  giocatore né quando i messaggi vengono consegnati [non tracciato].

A parte questi canali, i droni condividono solo lo stato del mondo (griglia, inventario).

## 5. Crescita dell'erba

- `Growable::OnRestart` (Core.il 5302-5369): `randomFactor = (float)various.NextDouble() * dev * 2 + 1 - dev`
  con `dev = growTimeDeviationPercent`.
- `Growable::GetGrowTime` (4736-4759): `growTime = GrowTimeFactor × meanGrowTime × randomFactor` secondi.
- `Growable::get_GrowTimeFactor` (4540-4582): `1 / (1 + 4 × acqua)` con acqua in [0, 1].
- Erba [asset]: `meanGrowTime = 0,5`, `dev = 0`. Quindi `randomFactor = 1` esatto e

```
tempo di crescita erba = 0,5 / (1 + 4 × acqua) secondi simulati
```

Il flusso `various` viene comunque consumato a ogni erba creata (rotazione casuale, indice
della mesh, `NextDouble`), ma non influenza la durata. Per le altre piante sì:
bush 4 s ± 20 %, carrot 6 s ± 20 %, tree 7 s ± 20 % [asset].

Conversione in tick: `Simulation::ChangeExecutionSpeed` (22251-22269) imposta
`OpDuration = ceil(2 500 000 / fattore) ns`. `Farm::MaxSpeedFactor` (15164-15191):
`1,5^speed`, raddoppiato se `power > 0`. Con speed 5 e power disponibile: 164 610 ns per tick.
Più la simulazione è veloce, più tick dura la crescita: 3037,5 tick asciutta, 607,5 con acqua 1.

Acqua:

- `Drone::Water` (13417-13520): `acqua += 0,25 × numero`, limitata a [0, 1] da
  `GridManager::SetWaterVolume` (16724-16779). Come `numero` dipende dal livello di
  `watering` non l'ho tracciato [non tracciato].
- `GridManager::WaterDecay` (16782-16855): ogni 0,1 s simulati, per ogni cella, con
  probabilità 0,1 (estrazione da `various`) `acqua *= 0,99`.
- Quando l'acqua di una cella cambia, la pianta ricalcola il timer di crescita
  (`Growable::UpdateFarmObject` 4624-4641 → `TryScheduleGrow` 4644-4733).

Gli upgrade della leaderboard non accorciano la crescita dell'erba: `grass` aumenta solo
la resa.

## 6. Tutti i consumatori del flusso `poly`

Il campo `Simulation::randomPoly` è letto in due soli metodi:

1. `Growable::ChooseCompanion` (Core.il 5159-5285), righe 5174, 5183, 5244.
2. `MainSim::LeaderboardExecutionFinished`, riga 19412: un `Next()` a fine run per il seed
   successivo.

`ChooseCompanion` è chiamato solo da `Growable::OnRestart` (riga 5328), solo se
`canHaveCompanion`. `OnRestart` è chiamato solo da `GridManager::SetFarmObject` (riga 17918),
cioè alla creazione di un'entità. Piante con companion [asset]: grass, bush, carrot, tree.

Percorsi che creano una di queste piante:

| Percorso | Metodo, riga | Companion estratti |
|---|---|---|
| `plant()` riuscito | `Drone::Plant` 13325 | 1 |
| `harvest()` su grassland (ricrescita erba) | `Growable::Harvest` 4918 → `RemoveEntity` 17464 | 1 |
| `till()` che riporta a grassland | `Drone::ChangeGround` 13179 | 1 |
| `clear()` | `ClearGrid(true)` 16912, da riga 29355 | uno per cella |
| `set_world_size(n)` con n diverso | `set_SizeLimit` → `GenerateWorld` 17168 | uno per cella |
| Avvio della simulazione | `GridManager::.ctor` 16638, `Farm::Unlock` 14892 | vedi sezione 2 |
| Rimozione di cactus, zucche, labirinto, coda del dinosauro su grassland | `RemoveEntity` (chiamanti a 1900, 7342, 5885, 10354) | 1 per cella |

Non consumano `poly`: movimento, `get_companion()`, `can_harvest()`, azioni fallite,
crescita (timer), decadimento dell'acqua, `spawn_drone()`. Nessun timer in background lo tocca:
tra un'azione nostra e l'altra il flusso è fermo.

## 7. Moltiplicatore polyculture

- `FarmObject::get_YieldFactor` (Core.il 3701-3727):
  `max(1 << (NumUnlocked(yieldUpgradeName) - 1), 1) × harvestFactor`.
  `harvestFactor` vale 1 (`MainSim::.ctor` riga 21045); lo porta a 10 solo
  `CheatConsole::ToggleFastMode` (riga 1248).
- `Growable::get_YieldFactor` (4809-4836): moltiplica per `5 << NumUnlocked("polyculture")`
  se `HasCompanion()`, altrimenti per 1.
- `Growable::GetYield` (4839-4889): `dropAmount × YieldFactor`.

Erba: `dropAmount = 1`, grass 10 → 512; polyculture 5 → ×160. **Confermati 512 e ×160.**

`Growable::HasCompanion` (5072-5115) è vero se nella cella `companionPos` esiste un'entità
e il suo `objectName` è uguale a quello di `companionType`. Dipende solo dal **tipo**
presente in quella cella al momento del raccolto: non conta se il companion è cresciuto,
né chi lo ha piantato, né il suo stato.

Due dettagli:

- `Growable::Harvest` (4892-4924) calcola la resa solo se la pianta è matura (`IL_0008`),
  ma rimuove e fa ricrescere l'erba in ogni caso: un raccolto prematuro costa 200 tick,
  rende zero ed estrae comunque un nuovo companion.
- La resa è calcolata prima della rimozione, quindi con il companion della pianta vecchia.

## Stato di `tfwr_rng.py`

Nessuna correzione necessaria alla derivazione dei seed: validata bit per bit contro
`System.Random` di mono e confermata in gioco sul flusso `poly`.
