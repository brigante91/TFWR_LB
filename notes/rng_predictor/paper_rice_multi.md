# Raccolta e discesa intrecciate: uno schema per la classifica Rice di *The Farmer Was Replaced*

*10 novembre 2026*

## Sommario

La classifica Rice chiede di produrre 2 000 000 di riso con 32 droni su un campo 32×32 scavando strati successivi di argilla. Lo schema di riferimento (una colonna per drone, tre passate per strato) si era fermato a 1:50.588 dopo diciotto versioni, a 0,65 s dal primo posto (1:49.943). Mostriamo che il tempo residuo non sta nel lavoro dei droni ma nelle attese di crescita dei primi due strati, dove l'acqua manca, e che queste attese si possono riempire anticipando la discesa allo strato successivo. Il vincolo è il crollo: scavare una cella distrugge il riso non raccolto fino a 10 righe di distanza. Lo schema proposto (v19) raccoglie le prime 18 righe, scende e pianta sulle prime 6, raccoglie le altre 14 e completa la discesa. Nel simulatore il tempo medio passa da 110,49 a 109,27 s su 20 seed; in gioco la media di classifica è 1:49.327, primo posto globale.

## 1. Introduzione

Nelle classifiche del gioco ogni azione del drone costa un numero fisso di tick e il punteggio è il tempo medio di più run consecutive che coprono almeno due ore simulate. La varianza fra run è quindi mediata e contano solo i miglioramenti sistematici.

Il lavoro precedente (versioni v1-v18) aveva esaurito le leve ovvie: interprete (cicli srotolati, acqua in linea), politica dell'acqua, albero di avvio dei droni, forma delle zone, fertilizzante, ultimo strato. Tutte le versioni dalla v2 alla v18 stavano fra 1:50.5 e 1:51.1. Questo lavoro parte da una domanda diversa: dove finisce il tempo che non è lavoro?

## 2. Regole rilevanti

**Sottosuolo.** Il terreno è diviso in strati di 16 blocchi. In ogni strato, sotto 0-7 blocchi di terra (la quota varia con un rumore liscio), ci sono 2 blocchi di argilla e poi roccia fino alla fine dello strato. Il primo strato non ha argilla.

**Riso.** Si pianta solo sull'argilla. Una pianta matura rende 128 riso e trasforma il blocco in terrazza secca, che va scavata per piantare sul blocco sotto. Ogni cella dà quindi 2 raccolti per strato; l'obiettivo richiede 15 625 raccolti, cioè 7 strati completi più una parte dell'ottavo.

**Crescita e acqua.** La crescita dura 6 s ± 20% e accelera linearmente con l'acqua del terreno, da 1× a livello 0 a 5× a livello 1. Una tanica alza il livello di 0,25; il terreno perde circa l'1% al secondo. Le taniche arrivano a ritmo fisso (25,6 al secondo nel modello), mentre il campo ne chiederebbe circa 160 al secondo: l'acqua è scarsa per tutta la run.

**Costi.** Un'azione (mossa, raccolta, semina, uso di un oggetto) costa 200 tick, circa 0,033 s. Uno scavo su argilla, roccia o terrazza costa circa 475 tick, 0,078 s.

**Crolli.** Scavando una cella, i quattro vicini con roccia o terra in cima vengono trascinati un livello sopra la nuova quota. Argilla e terrazze resistono al trascinamento ma crollano se un vicino è 4 o più livelli più profondo (stabilità 3), fermandosi a 3 livelli dal vicino. Il crollo distrugge la pianta e si propaga di cella in cella. Non c'è continuità fra i bordi del campo.

## 3. Schema di riferimento (v18)

Ogni drone possiede una colonna e la percorre verso nord, rientrando dal bordo. Per ogni strato fa tre passate:

- **A2**: scende fino all'argilla e pianta sul primo blocco (circa 0,15 s a cella);
- **B**: raccoglie, scava la terrazza secca e pianta sul secondo blocco (circa 0,18 s a cella);
- **A1**: raccoglie il secondo blocco (circa 0,07 s a cella). La terrazza rimasta viene tolta dal crollo nella A2 successiva.

Tre visite per cella a strato sono il minimo: la discesa di una cella distrugge il riso dei vicini, quindi raccolta del secondo blocco e discesa non possono avvenire nella stessa visita.

## 4. Metodo

Il simulatore `haysim/rice` riproduce a eventi i 32 droni, la generazione del terreno, i crolli, la crescita, l'evaporazione e il magazzino dell'acqua, con le regole ricavate dal codice del gioco. È tarato sui tempi per strato misurati in gioco e stima la v18 a 110,5 s contro 110,6 s reali. Ogni configurazione è valutata su 4-20 seed; con 20 seed l'errore standard della media è circa 0,12 s.

## 5. Dove va il tempo

Con acqua infinita lo schema di riferimento chiuderebbe in circa 98 s: le attese valgono 12-13 s. Il simulatore le localizza così (media per drone):

| Strato | Attesa nella B (s) | Attesa nella A1 (s) | Durata dello strato in gioco (s) |
|---|---|---|---|
| 1 | 2,95 | 4,27 | 20,3 |
| 2 | 2,22 | 3,60 | 17,3 |
| 3 | 0,30 | 1,37 | 13,7 |
| 4-7 | 0,1-0,5 | 0,6-1,2 | 12,75 |

Nei primi due strati l'acqua in magazzino è nulla e il campo è limitato dalla crescita, non dal lavoro. La causa dell'attesa nella A1 è strutturale: la B pianta a 0,18 s a cella e la A1 raccoglie a 0,07 s a cella, quindi il drone raggiunge le piante giovani in coda alla colonna e deve aspettarle. L'ultima cella piantata ha bisogno di circa 6 s, la A1 ne offre 2,2.

## 6. Schema intrecciato (v19)

L'idea è spendere quell'attesa nella discesa dello strato successivo. Il vincolo è il cono del crollo: una discesa di 15-22 livelli, a 3 livelli per cella, distrugge il riso non raccolto fino a 10 righe più avanti nella colonna, e altrettanto nelle colonne vicine. Lo scavo deve quindi restare almeno 11 righe dietro al fronte di raccolta.

Nei primi due strati, dopo la B, ogni drone esegue:

1. raccolta delle righe 0-17;
2. ritorno alla riga 0 (14 mosse verso nord attraverso il bordo), discesa e semina sulle righe 0-5;
3. avanzamento alla riga 18 (12 mosse), raccolta delle righe 18-31;
4. avanzamento alla riga 6 (6 mosse), discesa e semina sulle righe 6-31.

Le 32 mosse in più (circa 1 s) cadono dentro le attese. La discesa spezzata non costa scavi aggiuntivi: quando il drone lascia la riga 5, la riga 6 è già stata trascinata a un livello dall'argilla. Le righe 0-5 arrivano alla B successiva già mature e la seconda parte della discesa è più corta.

Tutti i droni seguono lo stesso percorso fisso, scritto in linea nel codice. Dal terzo strato lo schema torna a quello di riferimento, perché lì le attese non coprono più le mosse aggiuntive.

## 7. Risultati

| Configurazione | Simulatore (s) | Celle perse a run | Gioco |
|---|---|---|---|
| v18, riferimento | 110,49 | 0 | 1:50.588 |
| v19, taglio a riga 18, distanza 12, 2 strati | 109,27 | 2 | **1:49.327** |

Il guadagno previsto è 1,22 s, quello misurato in classifica 1,26 s. L'attesa media per drone scende da 19,5 a 16,1 s. Il primo posto precedente era 1:49.943.

**Sensibilità ai parametri** (simulatore, 8 seed, riferimento 110,61 s):

| Variante | Tempo (s) | Celle perse a run |
|---|---|---|
| Solo il primo strato intrecciato | 110,26 | 0 |
| Due strati, taglio 18 | 109,28 | 2 |
| Due strati, taglio 20 | 109,35 | 3 |
| Due strati, taglio 22 | 109,38 | 7 |
| Tre strati, taglio 20 | 109,36 | 4 |
| Due strati, tre tagli (16, 24, 32) | 110,18 | 3 |
| Due strati, taglio 13 | 110,10 | 39 |
| Distanza 14 invece di 12 | 109,40 | 4 |

L'ottimo è piatto fra i tagli 18 e 20. Tagli troppo vicini all'inizio fanno partire lo scavo quando i vicini non hanno ancora finito di raccogliere; più tagli aggiungono mosse più in fretta di quanto tolgano attese. Tagli e distanze diversi per strato non danno differenze oltre il rumore (20 seed, fra 109,07 e 109,47 s).

**Robustezza allo sfasamento.** Con un ritardo casuale per drone all'avvio, lo schema intrecciato conserva il vantaggio:

| Ritardo massimo (s) | Riferimento (s) | Intrecciato (s) | Celle perse a run |
|---|---|---|---|
| 0,5 | 110,61 | 109,06 | 4 |
| 1,0 | 110,60 | 109,21 | 5 |
| 2,0 | 110,75 | 109,64 | 23 |

**Barriere di sincronizzazione.** Far aspettare ai droni che tutti (soglia sul riso totale) o i due vicini (lettura della cella a est e a ovest) abbiano finito la raccolta azzera le celle perse ma costa circa 1,2 s: tutti si allineano al drone più lento. Senza barriera la perdita è di 2-3 celle su 15 625 raccolti.

## 8. Risultati negativi precedenti

Tentativi fatti sullo schema di riferimento che non hanno retto in gioco o nel simulatore:

- **Pre-scavo a scatto (v9).** Durante la prima attesa lunga nella A1 il drone tornava a scavare la riga 0. Nel simulatore guadagnava 0,9 s, in gioco ha dato 1:53.9 con righe vuote: lo scatto dipendeva dal singolo drone e divideva i droni in due gruppi sfasati. La v19 differisce proprio in questo: percorso identico per tutti e distanza di sicurezza esplicita.
- **Acqua concentrata in coda alla colonna.** Meglio nel primo simulatore, peggio in gioco (1:51.1-1:52.1) e nel simulatore con evaporazione.
- **Zone a blocchi invece di colonne.** 133-168 s, con riso perso ai confini.
- **Fertilizzante nelle attese.** Nessun guadagno: l'attesa si sposta alla cella successiva.
- **Soglie dell'acqua, cache del magazzino, albero di avvio.** Tutto entro il rumore o peggio.
- **Acqua a livello 1 nell'ultimo strato.** Nessun effetto.

## 9. Limiti

- Il simulatore è stato tarato sui tempi per strato, non sullo sfasamento fra droni, che in gioco non è stato misurato. La previsione ha retto per la v19 e non per la v9.
- Il guadagno dipende dalle attese dei primi strati. Su Rice_Single, dove l'acqua basta da subito e le attese sono nulle, lo schema non si applica.
- Restano circa 6 s di attesa nei primi due strati (soprattutto all'inizio della B) e circa 1 s a strato dopo. Una divisione dei droni in squadre che lavorano per righe potrebbe anticipare più discesa, ma non è stata simulata.

## 10. Conclusioni

Lo schema a tre passate era al limite del lavoro per cella, ma non del tempo: nei primi due strati un terzo della durata era attesa di crescita. Intrecciare la raccolta del secondo blocco con la discesa successiva, tenendo lo scavo 12 righe dietro al riso non raccolto, recupera 1,2 s senza scavi aggiuntivi e con una perdita di 2-3 celle a run. Il risultato in gioco, 1:49.327, coincide con la previsione del simulatore entro 0,05 s.

## Appendice: file

- `lb_rice_multi.py`: script di gioco v19, generato.
- `gen_rice.py`: generatore; parametri `SPL = 2`, `CUT = 18`, `LAG = 12`.
- `haysim/rice/v4.py`, `world.py`: simulatore; parametri `SPL`, `CUTS`, `LAG`, `BAR`, `LB`, `JIT`.
- `lb_rice_multi_v18.py`: schema di riferimento.
