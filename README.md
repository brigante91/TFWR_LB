# TFWR_LB — The Farmer Was Replaced: leaderboard work

Raccolta di script, simulatori e note per le classifiche di *The Farmer Was Replaced*.
Stato dei record al 9-10 nov 2026, dalle note di lavoro. Nomi ed esiti sono quelli riportati nelle note, non ricontrollati in gioco.

## Record principali

Rank dal profilo (SteamID 76561198129401400), dati XML ufficiali al 10 nov 2026. Elenco completo di tutte le 30 classifiche: [`leaderboards/RANKS.md`](leaderboards/RANKS.md).

| Classifica | Rank | Script |
|---|---|---|
| Rice (multi) | #1 | `scripts/lb_rice_multi_v18.py` (ultimo presente; v19 solo nelle note) |
| Rice Single | #4 | `scripts/lb_rice_single.py` |
| Sunflowers (multi) | #2 | `scripts/lb_sunflowers_v11.py` |
| Sunflowers Single | #8 | `scripts/lb_sunflowers_single_v10.py` |
| Hay (multi) | #8 (1:47.99) | `scripts/lb_hay_dense.py` |
| Hay Single | #62 | `scripts/lb_hay_single_v2.py` |
| Treasure Map | #6 | `scripts/lb_treasure_v4.py` |
| Bamboo Single | #9 | `scripts/lb_bamboo_single.py` |
| Pumpkins (multi) | #81 | `scripts/lb_pumpkins_v4.py` |
| Cactus (multi) | #115 | `scripts/lb_cactus_v2.py` |
| Fastest Reset | #2282 | — |

Non in classifica (19): Bamboo multi, Cactus single, Carrots (multi/single), Dinosaur, Dynamite (multi/single), Fastest Underground Reset, Maze (multi/single), Mushrooms (multi/single), Ores (multi/single), Pumpkins Single, Pyramids (multi/single), Wood (multi/single).

Nota: alcune versioni citate nelle note (es. rice v19, bamboo v2) non sono nella raccolta come file separato; per quelle la nota resta il riferimento.

## Struttura

- `scripts/` — tutti gli script di classifica (`lb_*.py`), i generatori (`gen_rice.py`), gli script di supporto (`tfwr_rng.py`, `session.py`, `banco.py`, `lancia.py`, `match_*.py`, `dynsim.py`, `test_ingame.py`…) e `ScriptAttuali/` (script in uso in gioco).
- `sims/` — simulatori e strumenti per classifica:
  - `haysim/` — simulatore fieno/girasoli/cactus/riso/bamboo/tesoro (es. `sunsim2.py`, il simulatore valido per i girasoli, `haysim.py`, `pumpsim.py`)
  - `dense/` — generatore e ottimizzatore di layout fieno
  - `hay_pred/` — test di predizione RNG per il fieno
  - `haysingle/` — simulazioni e percorsi per Hay Single
- `leaderboards/` — XML ufficiali Steam delle 30 classifiche (`xml/`) e riepilogo rank (`RANKS.md`).
- `logs/` — log di run in gioco (pumpkins, girasoli).
- `notes/memory/` — note di progetto per classifica (stato, regole, lezioni).
- `notes/rng_predictor/` — findings, audit, piani e verifiche (`FINDINGS.md`, `AUDIT_BUG.md`, `PIANO_LB.md`, `EXPLOIT_REPORT.md`, …).

## Regole e lezioni chiave

- Punteggio: per tutte le classifiche le run si ripetono finché il tempo simulato totale è ≥ 2 h e si invia la media. Una run fallita o annullata scarta la serie. Steam tiene il record migliore.
- Girasoli: ogni raccolta (anche di seme) aggiorna il flag che toglie il bonus al raccolto successivo; l'acqua è la risorsa scarsa; la crescita media è 7 s.
- Zucche: la resa è 3072 per quadrato di lato ≥ 6; raccogliere presto un 32×32 incompleto frammenta il campo.
- Cactus: il numero è legato alla cella finché non cresce.
- Livelli massimi: pumpkins 10, sunflowers 1, cactus/dinosaurs/mazes 6.
- Classifiche Dinosaur e Maze: nessun invio riuscito nelle note.

## Esclusioni

Non incluse: le cartelle `decompiled*` (codice decompilato del gioco, non sviluppato qui), `__pycache__`, `script_achievement/` (script achievement, non classifiche) e la cartella `Saves` del gioco.

## Fonti

Classifiche leggibili da `https://steamcommunity.com/stats/2060160/leaderboards/<id>/?xml=1`.
