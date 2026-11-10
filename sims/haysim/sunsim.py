"""Simulatore della classifica Sunflowers (100.000 power, 32 droni, campo 32x32).

NOTA 7 nov 2026: modello AGGREGATO, non allineato agli script a blocchi (v5+): mosse da formula,
flag e massimo del campo non simulati, niente consumo di power ne' fine run. Per v5/v7 usare
sunsim2.py (simulatore a eventi drone per drone) + sunprog.py (trascrizione degli script).

Regole lette da decompiled_full/Core/{Sunflower,Growable,Farm,Execution,GridManager}.cs:

  petali = Next(7,16)  -> valore uniforme 7..15 a OGNI plant, letto da measure() (1 tick).
  resa   = dropAmount(1) * YieldFactor; YieldFactor x8 se il girasole ha il valore MASSIMO
           fra TUTTI i girasoli in campo (semi compresi) e ce ne sono >= 10.
  flag globale hadIncorrectSunflowerHarvest: ogni harvest (anche di un seme, resa 0)
           calcola getBoost = (number==max && count>=10); il flag diventa !getBoost; se il
           flag PRIMA era True (ultimo harvest non massimo) questo harvest perde il bonus.
           => un reroll (harvest di un seme non-massimo + plant) sporca il flag e toglie il
              bonus al raccolto successivo di CHIUNQUE: costa ~7 power (8 -> 1) + 403 tick.
  crescita = meanGrowTime(5s) * randomFactor / (1 + 4*acqua),  randomFactor ~ U[0.8,1.2].
  acqua cella: use_item(Water,n) = +0.25*n  (cella clampata a [0,1]); decadimento medio ~1%/s.
             use_item fallisce (1 tick) se il serbatoio ha < n unita' d'acqua.
  serbatoio condiviso: +1 ogni 20/512 s = 25.6/s, parte da 0 (HarvestFactor=1).
  velocita': power==0 -> 3037.5 tick/s (meta'); power>0 -> 6075 tick/s.
  consumo:  UsedPort += ops/200/30 per step -> ~32 ops/s * ... = ~32 power/s totali (1/drone).
  costi (tick): azione 200 (move/plant/harvest/till/use_item), azione fallita 1;
                measure/get_*/num_items/can_harvest 1; confronto/if/indice/operatore 1;
                for 1/iterazione; while 1 alla prima valutazione; chiamata propria 1; get_time 0.

Calibrazione (logs/sunflowers_v4_log.txt, sunflowers_v5_run1.txt):
  v4 (colonne): round ~12.3 s, ~7500 power/round (32 droni), P_W~4.6, PH_W~1.35.
  v5 (blocchi 4x8): round ~10.4 s, fasi ~0.95-1.0 s (con PH_W=1.0 sforavano -> ~6500 power/round).

Il simulatore e' deterministico-per-seed: estrae i petali e la deviazione di crescita da un
RNG per avere medie realistiche; una run media si ottiene con mean_over_seeds().
"""
import random

TPS_FULL = 6075.0
TPS_HALF = 3037.5
ACT = 200          # tick di un'azione riuscita
FAIL = 1           # tick di un'azione fallita
GOAL = 100000
NDRONE = 32
NCELL = 32         # celle per drone (blocco 4x8)
BW, BH = 4, 8
TANK_RATE = 25.6   # unita' d'acqua al secondo nel serbatoio condiviso
GROW_MEAN = 5.0
DEV = 0.2
CONS = 32.0        # power/s consumati (totale, ~1 per drone)
PETAL_LO, PETAL_HI = 7, 15   # inclusivi

# ---------------------------------------------------------------------------
# Modello del tempo: converte un carico di tick in secondi tenendo conto della
# velocita' dimezzata finche' il power totale e' 0.
# ---------------------------------------------------------------------------

class Clock:
    def __init__(self):
        self.t = 0.0                 # secondi simulati
        self.power = 0.0             # inventario power reale (32 droni, netto consumo)
        self.harvested = 0.0         # power lordo raccolto (somma su tutti i droni)
        self.first_harvest_done = False

    def speed(self):
        # power>0 -> piena; power==0 -> meta'. Il power parte da 0 e resta 0 finche'
        # il primo harvest non lo porta sopra 0.
        return TPS_FULL if self.power > 0.0 else TPS_HALF

    def spend(self, ticks):
        # avanza il tempo di `ticks` (di UN drone; i 32 girano in parallelo sincronizzati)
        dt = ticks / self.speed()
        self.advance(dt)

    def advance(self, dt):
        if dt <= 0:
            return
        self.t += dt
        self.power = max(0.0, self.harvested - CONS * self.t)

    def add_power(self, gross):
        # gross = power raccolto da UN drone in questo istante -> *NDRONE perche' tutti uguali
        self.harvested += gross
        self.power = max(0.0, self.harvested - CONS * self.t)
        if gross > 0:
            self.first_harvest_done = True


# ---------------------------------------------------------------------------
# Modello acqua: serbatoio condiviso + acqua di cella con decadimento.
# ---------------------------------------------------------------------------

class Water:
    def __init__(self):
        self.used = 0.0              # unita' d'acqua gia' consumate (tutti i droni)

    def tank(self, t):
        return TANK_RATE * t - self.used

    def take(self, t, n):
        # un drone prova a usare n unita'; vero se il serbatoio (condiviso) le ha
        if self.tank(t) >= n:
            self.used += n
            return True
        return False


def grow_seconds(rng, water):
    rf = rng.uniform(1.0 - DEV, 1.0 + DEV)
    return GROW_MEAN * rf / (1.0 + 4.0 * water)


# ---------------------------------------------------------------------------
# Economia del bonus.  Modelliamo l'aggregato come indicato dalle note:
#   - ogni harvest di un girasole cresciuto col valore giusto = +8 power;
#   - il PRIMO harvest di ogni fase puo' perdere il bonus (flag sporco dal round/fase prec.):
#     lo contiamo una volta per round (perdita ~7 power, globale);
#   - ogni reroll durante una fase di raccolta sporca il flag -> -7 power (globale),
#     oltre a 403 tick (harvest 200 + plant 200 + measure 1 + op) sul drone che rerolla;
#   - un girasole non cresciuto in tempo non viene raccolto quel round (resa 0 quel round).
# Lordo per girasole raccolto col bonus = 8; senza bonus = 1.
# ---------------------------------------------------------------------------
BOOST = 8.0
NOBOOST = 1.0


# ===========================================================================
# STRATEGIA A FINESTRA (baseline v4/v5)
# ===========================================================================

def sim_windowed(seeds, minv=11, cap=9, phase_margin=0.42, grow_wait=1.2,
                 water_on=True, verbose=False):
    """Un drone, molti round, finche' GOAL.  Ritorna (tempo_s, round_log)."""
    rng = random.Random(seeds)
    clk = Clock()
    wat = Water()
    log = []
    r = 0
    nvals = 16 - minv          # fasi: 15..minv
    while clk.power < GOAL:
        t_round0 = clk.t
        # -------- finestra di piantagione --------
        # ogni cella: plant(200)+measure(1); reroll finche' valore in [minv,15] e cap non pieno.
        cnt = [0] * nvals
        cells = []             # (valore, grow_finish_time)
        # muoviti sulle 32 celle (serpentina 4x8): 31 mosse
        moves = (NCELL - 1)
        clk.spend(moves * ACT + moves)   # mosse + for-overhead
        rerolls_window = 0
        for c in range(NCELL):
            # plant iniziale
            clk.spend(ACT + 1 + 2)       # plant + measure + op
            v = rng.randint(PETAL_LO, PETAL_HI)
            # reroll (nella finestra: non sporca bonus perche' nessuno raccoglie)
            while v < minv or cnt[v - minv] >= cap:
                clk.spend(ACT + ACT + 1 + 3)  # harvest + plant + measure + op
                v = rng.randint(PETAL_LO, PETAL_HI)
                rerolls_window += 1
            cnt[v - minv] += 1
            # acqua: dosata per crescere entro la fase di questo valore
            w = 0.0
            if water_on:
                # tempo che manca alla fase di v (fasi scendono da 15)
                phases_ahead = (15 - v)
                left = grow_wait + phases_ahead * phase_margin + 0.3
                need = (GROW_MEAN / left - 1.0) / 4.0   # 1+4w >= 5/left
                if need > 0:
                    nunits = int(need / 0.25) + 1
                    if nunits > 4:
                        nunits = 4
                    if wat.take(clk.t, nunits):
                        clk.spend(ACT)
                        w = min(1.0, 0.25 * nunits)
                    else:
                        clk.spend(FAIL)
            gf = clk.t + grow_seconds(rng, w)
            cells.append([v, gf])
        t_plant_end = clk.t
        # -------- attesa crescita --------
        clk.advance(grow_wait)
        # -------- fasi di raccolta 15..minv (sincronizzate) --------
        first_phase_loss_charged = False
        for v in range(15, minv - 1, -1):
            # il lavoro della fase: scan 32 celle (todo) + giro greedy + harvest
            todo = [i for i in range(NCELL) if cells[i][0] == v]
            clk.spend(NCELL + NCELL)     # scan + confronti
            nmoves = greedy_moves(len(todo))
            clk.spend(nmoves * ACT)
            boosted_this = 0
            for i in todo:
                grown = cells[i][1] <= clk.t
                clk.spend(ACT + 2)       # harvest + op
                if grown:
                    boosted_this += 1
                cells[i][0] = 0
            # il primo harvest del round puo' perdere il bonus (flag)
            gross = boosted_this * BOOST
            if not first_phase_loss_charged and boosted_this > 0:
                gross -= (BOOST - NOBOOST)   # una perdita per round
                first_phase_loss_charged = True
            clk.add_power(gross * NDRONE)
            # margine di sincronizzazione (il drone piu' lento + overshoot del wait_until)
            clk.advance(phase_margin)
            if clk.power >= GOAL:
                break
        if verbose:
            log.append((r, round(t_plant_end, 2), round(clk.t, 2),
                        round(clk.power, 1), rerolls_window))
        r += 1
        if r > 400:
            break
    return clk.t, log


def greedy_moves(n):
    """mosse medie per raccogliere n celle sparse in un blocco 4x8 con giro greedy."""
    if n <= 0:
        return 0
    # il blocco ha diametro Manhattan 10; con n celle sparse le mosse ~ perimetro/densita'.
    # calibrato: ~ (n celle) coprono in media 1.6*(n+2) mosse, saturando verso ~24.
    m = int(1.6 * (n + 1))
    if m > 24:
        m = 24
    return m


# ===========================================================================
# STRATEGIA A PIPELINE (v6): niente finestra dedicata.  Durante la fase v il drone
# raccoglie i v e RIPIANTA subito; il nuovo valore u:
#   - se u e' nella banda utile per questo round (cresce entro la sua fase e non
#     inquina le fasi rimaste) -> tenuto, verra' raccolto nella fase u di QUESTO round;
#   - altrimenti reroll (costa 403 tick + 7 power).
# Alle fasi basse (<= low_stop) non si ripianta (resterebbe un seme che inquina o
# inutile): la cella resta vuota e si riempie in una mini-finestra a fine round.
# ===========================================================================

def sim_pipeline(seeds, minv=11, cap=9, phase_margin=0.42,
                 cascade_gap=2, low_stop=12, water_on=True, verbose=False):
    """cascade_gap: tiene il replant solo se u <= v-cascade_gap (ha tempo di crescere e
    non inquina).  low_stop: sotto questa fase non si ripianta (mini-finestra)."""
    rng = random.Random(seeds)
    clk = Clock()
    wat = Water()
    log = []
    r = 0
    # stato campo: lista di celle con (valore, grow_finish). Inizialmente vuoto -> primo
    # round fa una finestra piena (come windowed) per innescare la pipeline.
    # Modelliamo lo steady-state della pipeline: ogni round parte con il campo gia'
    # pieno di semi piantati nel round precedente (nelle fasi).
    cells = seed_full_field(rng, clk, wat, minv, cap, water_on)
    while clk.power < GOAL:
        t_round0 = clk.t
        first_phase_loss_charged = False
        rerolls_round = 0
        for v in range(15, minv - 1, -1):
            todo = [i for i in range(NCELL) if cells[i][0] == v]
            clk.spend(NCELL + NCELL)
            nmoves = greedy_moves(len(todo))
            clk.spend(nmoves * ACT)
            boosted_this = 0
            # ripianta solo se v e' alta abbastanza da avere una banda utile non vuota
            replant = (v > low_stop) and (v - cascade_gap >= minv)
            for i in todo:
                grown = cells[i][1] <= clk.t
                clk.spend(ACT + 2)            # harvest del girasole v
                if grown:
                    boosted_this += 1
                if replant:
                    # ripianta e valuta u.  Regola del flag:
                    #   u <= v-cascade_gap  -> tenuto: cresce entro la sua fase u e viene
                    #       ri-raccolto in QUESTO round (cascata), oppure u<minv = cella morta
                    #       ma innocua (sotto tutte le fasi, non ruba il bonus a nessuno);
                    #   u >= v-cascade_gap+1 .. v -> inquinerebbe le fasi rimaste -> reroll
                    #       (harvest del seme non-massimo sporca il flag: -7 power, +403 tick).
                    clk.spend(ACT + 1 + 2)   # plant + measure + op
                    u = rng.randint(PETAL_LO, PETAL_HI)
                    hi = v - cascade_gap     # massimo valore tenibile senza inquinare
                    while u > hi:
                        clk.spend(ACT + ACT + 1 + 3)
                        u = rng.randint(PETAL_LO, PETAL_HI)
                        rerolls_round += 1
                    if u < minv:
                        cells[i] = [0, 0.0]  # cella morta: andra' nella mini-finestra
                    else:
                        w = 0.0
                        if water_on:
                            left = (v - u) * phase_margin + 0.15
                            need = (GROW_MEAN / left - 1.0) / 4.0
                            if need > 0:
                                nu = int(need / 0.25) + 1
                                if nu > 4:
                                    nu = 4
                                if wat.take(clk.t, nu):
                                    clk.spend(ACT)
                                    w = min(1.0, 0.25 * nu)
                                else:
                                    clk.spend(FAIL)
                        cells[i] = [u, clk.t + grow_seconds(rng, w)]
                else:
                    cells[i] = [0, 0.0]      # vuota -> mini-finestra
            gross = boosted_this * BOOST
            if not first_phase_loss_charged and boosted_this > 0:
                gross -= (BOOST - NOBOOST)
                first_phase_loss_charged = True
            # penalita' bonus dei reroll di QUESTA fase (ognuno toglie 7 power, globale)
            gross -= rerolls_round * (BOOST - NOBOOST)
            rerolls_round = 0
            clk.add_power(gross * NDRONE)
            clk.advance(phase_margin)
            if clk.power >= GOAL:
                break
        # mini-finestra: riempi le celle vuote (fasi <= low_stop) per il round successivo
        empties = [i for i in range(NCELL) if cells[i][0] == 0]
        if empties:
            moves = greedy_moves(len(empties))
            clk.spend(moves * ACT + len(empties))
            for i in empties:
                clk.spend(ACT + 1 + 2)
                v = rng.randint(PETAL_LO, PETAL_HI)
                # qui nessuno raccoglie (mini-finestra) MA i droni non sono perfettamente
                # sincronizzati: assumiamo la finestra sia flag-safe (reroll liberi).
                while v < minv:
                    clk.spend(ACT + ACT + 1 + 3)
                    v = rng.randint(PETAL_LO, PETAL_HI)
                w = 0.0
                if water_on:
                    if wat.take(clk.t, 4):
                        clk.spend(ACT)
                        w = 1.0
                    else:
                        clk.spend(FAIL)
                cells[i] = [v, clk.t + grow_seconds(rng, w)]
        if verbose:
            log.append((r, round(clk.t, 2), round(clk.power, 1)))
        r += 1
        if r > 400:
            break
    return clk.t, log


def seed_full_field(rng, clk, wat, minv, cap, water_on):
    """Primo round: finestra piena a meta' velocita' per innescare la pipeline."""
    cnt = [0] * (16 - minv)
    cells = []
    clk.spend((NCELL - 1) * ACT + (NCELL - 1))
    for c in range(NCELL):
        clk.spend(ACT + 1 + 2)
        v = rng.randint(PETAL_LO, PETAL_HI)
        while v < minv or cnt[v - minv] >= cap:
            clk.spend(ACT + ACT + 1 + 3)
            v = rng.randint(PETAL_LO, PETAL_HI)
        cnt[v - minv] += 1
        w = 0.0
        if water_on and wat.take(clk.t, 4):
            clk.spend(ACT)
            w = 1.0
        cells.append([v, clk.t + grow_seconds(rng, w)])
    clk.advance(1.2)
    return cells


# ===========================================================================
# Utility
# ===========================================================================

def fmt(t):
    m = int(t // 60)
    s = t - 60 * m
    return "%d:%06.3f" % (m, s)


def mean_over_seeds(fn, nseeds=40, **kw):
    tot = 0.0
    for s in range(nseeds):
        t, _ = fn(s, **kw)
        tot += t
    return tot / nseeds


if __name__ == "__main__":
    import sys
    print("# Calibrazione baseline a finestra (v4/v5)")
    for pm, gw, tag in [(0.55, 1.35, "v4-like colonne"), (0.42, 1.2, "v5-like blocchi")]:
        t, log = sim_windowed(0, phase_margin=pm, grow_wait=gw, verbose=True)
        # round steady: delta power fra due round
        if len(log) >= 3:
            dp = log[2][3] - log[1][3]
            dt = log[2][2] - log[1][2]
        else:
            dp = dt = 0
        print("  %-18s tempo=%s  round~%.2fs  dPow/round~%.0f" %
              (tag, fmt(t), dt, dp))
    print()
    print("# Media su 40 seed")
    tw = mean_over_seeds(sim_windowed, phase_margin=0.42, grow_wait=1.2)
    print("  windowed (v5)          : %s" % fmt(tw))
    for cg in (2, 3):
        for ls in (11, 12, 13):
            tp = mean_over_seeds(sim_pipeline, cascade_gap=cg, low_stop=ls)
            print("  pipeline cg=%d low=%d     : %s" % (cg, ls, fmt(tp)))
