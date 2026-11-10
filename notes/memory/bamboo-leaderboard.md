---
name: bamboo-leaderboard
description: "Classifiche Bamboo (5e8, 32 droni) e Bamboo Single (2.5e7, 8x8): regole estratte, simulatore haysim/bamboo, script v1 lb_bamboo.py / lb_bamboo_single.py (8 nov 2026, non provati)"
metadata:
  node_type: memory
  type: project
  originSessionId: 23bc7904-bbab-4111-a6f8-45453a33121c
  modified: 2026-11-08T12:41:22.951Z
---

8 nov 2026: scritti `rng_predictor/lb_bamboo.py` (multi) e `lb_bamboo_single.py`, non ancora provati in gioco. Simulatore `rng_predictor/haysim/bamboo/` (sim.py + prog.py, `python3 prog.py mode=1|2 N=.. PARAM=..`): stima single ~201 s (R=6, T1=5, D=4, acqua 1.0 sotto 0.5), multi ~211 s (W_TOP 0.8, W_RISE 0.1). Classifica Steam (lbid bamboo 21488263, bamboo_single 21444624): multi #1 2:49.9, #6 3:11.0, #7 5:25; single #1 2:33.3, #8 3:08.4.

Regole (Bamboo.cs, Drone.cs, asset grezzi): avvio power 1e9 + riso 1e9; resa 128 (livello 8) * pezzi^2; semina costa 128 riso; solo su soil/dirt/perlite (perlite x2 ma dig vietato: niente sottosuolo). Crescita 1 blocco ogni 1/(1+4*acqua) s, deviazione 0 (deterministica). Fiori f1 = 1+a+r, f2 = f1+max(3,b+r), F = f2+max(3,c+r), a,b,c in {2,3,4}, r in {0,1} fisso per cella (rumore); nuovi fiori solo con una nuova semina. move() in una cella a quota h taglia la pianta a h (resa (h_vecchia-h)^2); a quota fiore-1 toglie il fiore; il taglio completa il blocco in corso e all'uscita del drone la pianta sale subito di 1. hover(h) costa un'azione e non puo' scendere sotto l'altezza del bambu' su cui si sta. measure() = prossimo fiore - 1. harvest() rende h^2 solo se ferma (isGrown), rimette quota 1. Acqua 25.6/s, fertilizzante 0.8/s (inutile), evaporazione 1%/s.

Schema v1: ciclo chiuso con una cella vuota "ascensore" dove si cambia quota; piante ritirate finche' f1 == 5 e f2-f1 == 4; poi 3 passate di sole move() (quota 4, quota 8, quota 1). Single drone-limitato (azioni); multi limitato dall'acqua (attese ~87 s nel sim).

**Why:** nuove classifiche DLC da scalare come le altre ([[leaderboard-overview]], [[rice-leaderboard]]).
**How to apply:** provare in gioco e confrontare col sim. Il #1 single (~4650 azioni) sembra fare ~3 move per ciclo senza ritiri: la perdita principale della v1 sono ritiri e semina (~1600 azioni). Idee: quote diverse per tratti del percorso in ordine crescente (r=1 con f1=6), meno ritiri, selezione di F.

**8 nov 2026 (sera):** single v1 in gioco 3:24.236 (run 195-223 s, ~31 cicli, 70-160 ritiri): il sim (201 s) e' tarato. Ricerca del #1 (2:33): schema a passate uniformi (5,9) ha pavimento ~170 s anche con selezione GRATIS (sim con fiori forzati); sovraccarico reale ~1400 azioni (semina 380, ritiri 550, acqua 140, attese 10 s). Scartati: campo piu' piccolo (attese/acqua, 198-216), selezione di F (peggio), giro solo su celle r=1 con fiori (6,11) (`haysim/bamboo/prog3.py`, percorso goloso da 4 vicoli ciechi, efficienza 0.75: 194 s), swap (bambu' canBeSwapped 0), jump/dig vietati in classifica, cappelli/fertilizzante inutili. Guida Steam "Bamboo 15M per minute" = corridoi, piu' lenta. v2 = ritiro rinviato alla passata di taglio (sim -4 s), v1 salvata in lb_bamboo_single_v1.py. Manca ancora il meccanismo del #1.

**8 nov (notte), scavo sul #1:** oracoli nel sim (selezione gratuita): (5,9) 170 s; giro solo r=1 (6,11) 166 s; (5,9) senza acqua/attese ~155 s = il #1. Accettare d diversi (DLO/DHI in prog2) peggiora (212-247). Verificati e chiusi: OnRestart solo da semina, set_world_size rigenera il campo (ResetPos taglia (0,0) ma si perde tutto), BufferedCryptoRandom non distorto, rumore r solo 0/1. Ipotesi: i tempi del #1/#2 (153-154) sono dell'epoca con RNG prevedibile (selezione gratis), non verificabile (XML senza date).

**v2 single in gioco: 3:17** (run 182-210 s, media ~197; sim 198). v1 3:24.2.
