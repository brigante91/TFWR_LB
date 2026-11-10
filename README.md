# TFWR_LB — The Farmer Was Replaced: leaderboard work

Raccolta di script, simulatori e note per le classifiche di *The Farmer Was Replaced*.
Stato dei record al 9-10 nov 2026, dalle note di lavoro. Nomi ed esiti sono quelli riportati nelle note, non ricontrollati in gioco.

## Record principali

| Classifica | Miglior tempo | Posizione | Script |
|---|---|---|---|
| Hay (dense) | 1:48.174 | #12 | `scripts/lb_hay_dense.py` |
| Hay (micro) | 1:48.943 | #26 | `scripts/lb_hay_micro.py` |
| Hay Single | 2:51.329 | #67 | `scripts/lb_hay_single_v2.py` |
| Cactus | 0:48.174 | #393 | `scripts/lb_cactus_v2.py` |
| Sunflowers (multi) | 2:28.5 (v11) | — | `scripts/lb_sunflowers_v11.py` |
| Sunflowers Single | 4:23.733 (v10) | — | `scripts/lb_sunflowers_single_v10.py` |
| Rice | 1:49.327 | #1 (v19) | `sims/haysim/rice/v4.py` (sim) + `scripts/lb_rice_multi_v18.py` (ultimo script presente; la v19 non è nella raccolta) |
| Rice Single | 2:26 | — | `scripts/lb_rice_single.py` |
| Bamboo Single | 3:17 (v2) | — | `scripts/lb_bamboo_single.py` (v1 presente in `lb_bamboo_single_v1.py`) |
| Treasure Map | 25.0 s (v4) | #1 reale 19.4 s | `scripts/lb_treasure_v4.py` |
| Pumpkins | 7:01 (v4) | — | `scripts/lb_pumpkins_v4.py` |

Nota: alcune versioni citate nelle note (es. rice v19, bamboo v2) non sono nella raccolta come file separato; per quelle la nota resta il riferimento.

## Struttura

- `scripts/` — tutti gli script di classifica (`lb_*.py`), i generatori (`gen_rice.py`), gli script di supporto (`tfwr_rng.py`, `session.py`, `banco.py`, `lancia.py`, `match_*.py`, `dynsim.py`, `test_ingame.py`…) e `ScriptAttuali/` (script in uso in gioco).
- `sims/` — simulatori e strumenti per classifica:
  - `haysim/` — simulatore fieno/girasoli/cactus/riso/bamboo/tesoro (es. `sunsim2.py`, il simulatore valido per i girasoli, `haysim.py`, `pumpsim.py`)
  - `dense/` — generatore e ottimizzatore di layout fieno
  - `hay_pred/` — test di predizione RNG per il fieno
  - `haysingle/` — simulazioni e percorsi per Hay Single
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
