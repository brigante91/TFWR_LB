---
name: no-touch-saves
description: "Mai modificare, creare o copiare file nella cartella Saves del gioco (Saves/Save1 ecc.)"
metadata:
  type: feedback
---

Non scrivere mai nulla sotto `.../AppData/LocalLow/TheFarmerWasReplaced/TheFarmerWasReplaced/Saves/` (niente copie di script, niente modifiche a lb_launcher.py o altri file).

**Why:** l'utente l'ha chiesto esplicitamente l'8 nov 2026, dopo che avevo copiato lb_treasure.py e cambiato SCELTA in lb_launcher.py.
**How to apply:** gli script restano in `rng_predictor/`; e' l'utente a copiarli nel gioco e a modificare il launcher. Indicargli solo cosa copiare/cambiare.
