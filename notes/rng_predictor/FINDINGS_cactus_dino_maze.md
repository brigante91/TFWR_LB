# Verifica dei commenti negli script cactus / dinosauro / labirinto (build del 4 nov 2026)

Core.dll è cambiato rispetto a ottobre (348 KB -> 579 KB: livelli/profondità, bambù, riso,
dinamite). Righe = `monodis Core.dll` di questa build. Tutto letto dall'IL, non provato in gioco.

## Costi (Execution::ApplySideEffect, Simulation::.ctor: actionOps=200, operationOps=1)
harvest 200 se c'è un'entità sotto (anche seedling/tesoro in movimento: effetto nullo), 1 se vuoto |
plant 200 ok / 1 fallito | swap 200 ok / 1 fallito | till 200 sempre | move = costo del cappello
(dinosauro: 400→33) altrimenti 200, 1 se fallito | use_item 200 ok / 1 fallito (reuse tesoro fallito
perché sta già traslocando: 200!) | change_hat 200 | measure 1 | can_harvest 1 | get_* 1 | get_time,
get_tick_count, quick_print 0.

## Interprete (Node::CheckIncrementOpCount, riga 87180) — corretto il 5 nov 2026
Il costo di un'operazione e' spesso la "dimensione" del valore (IPyObject::Size): numero, entita',
booleano = 1; tupla = somma degli elementi, quindi `(x, y)` = 2 e `(tipo, (x, y))` = 3.
- operatore binario 1 (BinaryExprNode, IL_10b3, operationOps x V_4).
- confronto (ComparisonNode, IL_063a): somma delle Size degli operandi di sinistra; `a < b` = 1,
  `t == (1, 2)` = 2.
- `x in dict` / `x not in dict` = Size(x) (BinaryExprNode IL_0f20 / IL_0fe1); `x in set` idem;
  `x in lista` = fino a len.
- indice `a[i]` = 1 su lista/tupla (IPyIndexable::At, Utils 45659); `d[k]` = max(1, Size(k))
  (PyDict::At, Utils 43706).
- `if` 1. `while`: il test costa 1 solo alla prima valutazione; le iterazioni successive non
  pagano il test (BranchNode, firstLoop, IL_0142 / back-edge IL_0336 -> IL_0059). Si paga
  solo il costo dell'espressione della condizione. `while True:` costa 1 una volta.
- `for` 1 per iterazione | `=` 0, `+=` ecc. 1 | `not` 0 | tupla letterale 1 |
  lista letterale max(len,1) | chiamata a funzione propria 1, builtin = suo costo |
  return/break/continue 0 | len/abs/append/pop 1.
- `use_item(Items.Water, n)`: +0.25 x n acqua in un'unica azione da 200 tick (Drone::Water 36481).

## Cactus
- Dimensione decisa al plant (Cactus::OnRestart 3721: cell.cactusNumber == -1 → randomCactus.Next(10)),
  measure() la legge subito (3688). Azzerata solo a crescita completa (OnFullyGrown 3053) → tagliare
  un seedling e ripiantare dà la stessa dimensione; swap scambia anche il numero della cella
  (GridManager::Swap 46201-46209). VERO.
- till su grassland rimuove l'entità senza ricrescita (ChangeGround 36027, RemoveEntity(pos,false)). VERO.
- Propagazione (Cactus::Pop 3318, predicato 3787, IsSorted 3520, AreSorted 3630): un cactus si
  propaga a TUTTI e 4 i vicini solo se OGNI vicino cactus è "sorted": maturo e con N>=sé, E>=sé,
  S<=sé, W<=sé (uguaglianza ammessa; vicino vuoto o ad altra profondità = ok). Un vicino NON MATURO
  conta come non ordinato (AreSorted 3657-3665). Il cactus di partenza non viene controllato. VERO,
  con l'avvertenza sui seedling: il controllo can_harvest a (0,0) non copre gli altri.
- Resa (GetDrops 3269): cactus = k² × 2^(cactus-1) (×32 al livello 6) → 1024²×32 = 33554432. VERO.
- Harvest di un seedling: costa 200, rende nulla, rimuove (Cactus::Harvest 2988-3003). Il reroll con
  can_harvest() è corretto.

## Dinosauro
- Mela: a change_hat una mela sotto il drone con nextPos già estratta (OnEquip 19339-19396).
  Mangiata quando il drone LASCIA la cella (OnMove 19720-19731 confronta con oldPos). La nuova mela
  nasce a nextPos e si estrae la successiva (19837-19846): uniforme fra le celle senza coda/mela
  alla stessa profondità (FindFreeCells 20089, TryChooseTarget 20267-20272 randomSnake), riestratta
  se uguale alla posizione attuale (20292-20293 / 20056-20082). measure() sulla mela = nextPos
  (Apple::Measure 2121; a campo quasi pieno restituisce l'unica cella libera). VERO.
- Costo move: ops parte da 400 (ctor 20310), a ogni mela ops -= floor(ops×0.03) (19849-19858),
  nessun clamp: si ferma a 33 dopo 99 mele. VERO ("~100").
- Ossa (BoneCount 19551): (celle con entità Dinosaur)² × 2^(dinosaurs-1) → 1023²×32 = 33488928. VERO.
- Coda invalicabile (Dinosaur::CanDroneMoveToFrom 4295, canMoveTo true solo sull'ultimo segmento
  quando non restano celle libere 20005).
- Commento sui tick: "indice 1" VERO su liste/tuple; "assegnazioni 0" vero solo per `=` (`+=` costa 1);
  "loop 0" FALSO per `for` (1 per iterazione), quasi vero per `while` (1 solo alla prima
  valutazione); "funzioni proprie 0" FALSO (1).

## Labirinto
- Oro per reuse e per harvest = dropAmount × mazeSize² × 2^(mazes-1) (Treasure::GetYield 15435,
  RepositionTreasure 15532-15561, Harvest 15412-15430) = 32768. 9863168 = 301 × 32768. VERO.
- Reuse ammesso finché treasureFactor < 301 (15510-15518), contatore parte da 1 (OnRestart 15993),
  +1 a ogni trasloco (CompleteRepositioning 15728-15731) → 300 reuse. VERO.
- Quantità: count / 2^(mazes-1) deve essere >= mazeSize per il reuse (ApplySideEffect 70266-70282),
  divisibile e = lato per generare (70208-70246). n×2^(mazes-1) VERO.
- Trasloco: timer di 200 tick (15622-15626); durante il trasloco il tesoro non è raccoglibile
  (get_Harvestable 15354), harvest restituisce vuoto ma costa 200, un secondo use_item fallisce e
  costa 200 (15520-15527). La logica di collect() è corretta.
- Harvest del tesoro finito (o di qualsiasi siepe) rimuove tutto il labirinto con ricrescita erba
  (HedgePlant::RemoveMaze 8433, Harvest 8512). VERO.
