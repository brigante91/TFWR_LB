# Verifica RE evidence-backed (REA + ILSpy) — stream RNG per leaderboard

Analisi statica in sola lettura di `Core.dll` (`sha256:3e49fa9e…2125ce5`) e `Utils.dll`.
Metadata via REA `rea-dotnet-static`; C# via ILSpy 8.2. Sorgenti in `decompiled/`.
Il gioco non è stato avviato. Scopo: solo offline, nessun invio alla classifica online.

## Seeding (conferma di `tfwr_rng.py`, nessuna correzione)

`Simulation::.ctor`: master `new Random(seed>=0 ? seed : OS-entropy)`, poi 9 stream
seminati **in quest'ordine** con `Helper::JustSha256It(master)`:
`various, maze, snake, cactus, sunflower, pumpkin, poly, random`.

`JustSha256It(rnd)` = `SHA256(rnd.NextBytes(16))[0..4] little-endian & 0x7FFFFFFF`
→ **16 sample consumati sul master per stream**. (Utils `Helper.cs:123`.)

## Mappa stream → consumatori (evidenza field-access REA)

| Stream | Metodi che lo leggono |
|---|---|
| various | FarmObject/Growable.OnRestart (gooIndex, randomFactor), Growable.ToggleWeird, GridManager.WaterDecay |
| maze | BushPlant.GenerateHedgeMaze, Treasure.ChooseNextPosition/CompleteRepositioning |
| snake | Apple.ChooseTarget |
| cactus | Cactus.OnRestart |
| sunflower | Sunflower.OnRestart |
| pumpkin | Pumpkin.OnRestart, Pumpkin.OnFullyGrown |
| poly | Growable.ChooseCompanion |
| random | Execution.AddProgramState (per-drone `random()`) |
| (tutti) | MainSim.LeaderboardExecutionFinished (1 Next() ciascuno per il seed successivo) |

## Per leaderboard

### hay / carrots / wood → `poly`
Companion via `Growable::ChooseCompanion`. Modello `tfwr_rng.py` verificato esatto:
ordine `Vector2Int(x,y)`, condizioni di break dei due loop di rigetto, mapping
`Next(4)`→{0 grass,1 bush,2 carrot,_ tree}, `Wrap`, `WorldSize`, `WorldSizeScale`.

### cactus → `cactus`
`Cactus.OnRestart`: `cactusNumbers[cell] = randomCactus.Next(10)` **una volta per cella**
(cache; replant non ri-estrae). `Measure()`→number. Board predicibile dal sotto-seed
conoscendo l'ordine di primo restart. `lb_cactus.py` è un sort adattivo (non predittivo):
leva record = pre-calcolare gli swap ed eliminare i `measure()`.

### sunflowers → `sunflower`
`Sunflower.OnRestart`: `number = randomSunflower.Next(7,16)` (7..15) **non cache-ato**.
Boost 8× se `number == max(sunflower sul campo) && count>=10`.
⚠️ Il flag `hadIncorrectSunflowerHarvest` applica una penalità in `Harvest()`, **ma**
`GetYield()` ricalcola `getBoost` senza penalità appena prima della resa → la penalità
sembra **solo cosmetica (VFX stars)**. Da confermare in gioco.

### pumpkins → `pumpkin`
`Pumpkin.OnRestart`: `mysteriousNumber = JustSha256It(randomPumpkin)` (= **16 sample**);
`Measure()`→mysteriousNumber (non usato da questa leaderboard).
`OnFullyGrown`: `randomPumpkin.NextDouble() <= 0.2` → **20% morte** (dead_pumpkin), 1 sample.
Resa (`GetDrops`): `size.x² × min(size.x,6) × YieldFactor`; 32×32 → `1024×6×YieldFactor`.
`lb_pumpkins.py` gestisce i DEAD adattivamente: corretto.

### maze → `maze`
`BushPlant.GenerateHedgeMaze`: `Next(num²)` (start) + DFS `GridDirection[].OrderBy(k=>Next())`
**4 draw/passo** (OrderBy stabile, chiave valutata 1×/elemento in ordine enum, anche con break)
+ `Next(list2.Count-1)` (tesoro; ⚠️ off-by-one: esclude l'ultimo vicolo cieco)
+ `ChooseNextPosition` (≥2).
`Treasure.CompleteRepositioning` (riuso): `ChooseNextPosition` (≥2) + loop celle `(i+j)%2==0`
× 4 direzioni con `NextDouble()` ogni volta (0,2% apre muro) ≈ **2·mazeSize²/riposizionamento**.
`Treasure.Measure()` = `(pos.x, pos.y)` → navigazione di `lb_maze.py` corretta.

### dinosaur → `snake`
`Apple.ChooseTarget`: `(randomSnake.Next(Wx), randomSnake.Next(0,Wy))`, re-roll finché la
cella è occupata da Dinosaur/Apple (2 draw/iterazione). `Apple.Measure()` = prossima
posizione mela (o None). `lb_dinosaur.py`: ciclo Hamiltoniano + scorciatoia verso la mela
misurata, adattivo e corretto. Leva record = sequenza mele pre-calcolata (richiede
co-simulare l'occupazione per i re-roll).

## Nota trasversale sulla predizione offline

Per cactus/sunflower/maze/snake il **numero di estrazioni** dipende dallo stato della board
(occupazione, loop di rigetto). Un predittore puro deve quindi **co-simulare la griglia**,
esattamente come l'approccio osserva→recupera-seed→predici di `session.py`/`sessfind.c`.
Il seed master (-1) resta entropia OS non osservabile: la predizione parte dal recupero del
sotto-seed a 31 bit dagli output osservati in partita.
