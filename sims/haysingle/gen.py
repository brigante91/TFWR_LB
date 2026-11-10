"""Genera lo script di Hay_Single. uso: ROUTE=route2.json OUT=lb_hay_single_v2.py VER=2 python3 gen.py
(VER=1: v1 con flag fast e controllo can_harvest; VER=2: senza controlli, acqua nel ramo al primo colpo)"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
VER = int(os.environ.get("VER", "1"))
R = json.load(open(os.path.join(HERE, os.environ.get("ROUTE", "route.json"))))
S = 8
A = tuple(R["A"]); C = tuple(R["C"]); path = [tuple(p) for p in R["path"]]; end = tuple(R["end"])
D3 = [(dx, dy) for dx in range(-3, 4) for dy in range(-3, 4) if (dx or dy) and abs(dx) + abs(dy) <= 3]
D3.sort(key=lambda o: (o[1], o[0]))


def w(p):
    return (p[0] % S, p[1] % S)


def diamond(g):
    return [w((g[0] + dx, g[1] + dy)) for dx, dy in D3]


bush = (set(diamond(A)) | set(diamond(C))) - {A, C}


def step_dir(a, b):
    for name, (dx, dy) in (("East", (1, 0)), ("West", (-1, 0)), ("North", (0, 1)), ("South", (0, -1))):
        if w((a[0] + dx, a[1] + dy)) == b:
            return name
    raise ValueError((a, b))


# ---- percorso di semina con i controlli dei raccolti gratuiti
lines = ["def semina():"]
planted = []; seen = {path[0]}; nchk = 0
if path[0] in bush:
    lines.append("\tplant(BUSH)")
    planted.append(path[0])
for a, b in zip(path, path[1:]):
    lines.append("\tmove(%s)" % step_dir(a, b))
    if b in seen:
        continue
    seen.add(b)
    cand = [d for d in diamond(b) if d in planted]
    if cand:
        nchk += 1
        lit = "{" + ", ".join("(%d, %d): True" % d for d in cand) + "}"
        lines += ["\tc = get_companion()", "\tif c[0] == BUSH:", "\t\tif c[1] in %s:" % lit,
                  "\t\t\tif can_harvest():", "\t\t\t\tharvest()"]
    if b in bush:
        lines.append("\tplant(BUSH)")
        planted.append(b)
assert set(planted) == bush and path[-1] == end
semina = "\n".join(lines)

X0 = end; X1 = A if end == C else C
d01 = step_dir(X0, X1); d10 = step_dir(X1, X0)


def ok_lit(g, other):
    return "{" + ", ".join("(BUSH, (%d, %d)): True" % d for d in diamond(g) if d != other) + "}"


def visit2(ok, d, final=False, first=False):
    out = []
    if first:
        out += ["\tuse_item(WATER, 4)", "\twhile not can_harvest():", "\t\tpass"]
    out += ["\tharvest()"]
    if final:
        out += ["\tif num_items(HAY) >= GOAL:", "\t\treturn"]
    out += ["\tif get_companion() in %s:" % ok, "\t\tif get_water() < WT:", "\t\t\tuse_item(WATER, 4)",
            "\telse:", "\t\tharvest()", "\t\twhile get_companion() not in %s:" % ok, "\t\t\tharvest()",
            "\tmove(%s)" % d]
    return out


def visit(ok, d, water=False, final=False, first=False):
    out = []
    if first:
        out += ["\tuse_item(WATER, 4)", "\twhile not can_harvest():", "\t\tpass", "\tharvest()"]
    else:
        out += ["\tif fast:", "\t\twhile not can_harvest():", "\t\t\tpass", "\tharvest()"]
        if water:
            out += ["\tif get_water() < WT:", "\t\tuse_item(WATER, 4)"]
    if final:
        out += ["\tif num_items(HAY) >= GOAL:", "\t\treturn"]
    out += ["\tif get_companion() in %s:" % ok, "\t\tfast = True", "\telse:", "\t\tfast = False",
            "\t\tharvest()", "\t\twhile get_companion() not in %s:" % ok, "\t\t\tharvest()", "\tmove(%s)" % d]
    return out


def indent(ls):
    return ["\t" + l for l in ls]


if VER == 2:
    farm = ["def farm():", "\tok0 = %s" % ok_lit(X0, X1), "\tok1 = %s" % ok_lit(X1, X0)]
    farm += visit2("ok0", d01, first=True) + visit2("ok1", d10, first=True)
    farm += ["\twhile num_items(HAY) < NEAR:"]
    body = []
    for k in range(8):
        body += visit2("ok0", d01) + visit2("ok1", d10)
    farm += indent(body)
    farm += ["\twhile True:"]
    farm += indent(visit2("ok0", d01, final=True) + visit2("ok1", d10, final=True))
    farm = "\n".join(farm)
else:
  farm = ["def farm():", "\tok0 = %s" % ok_lit(X0, X1), "\tok1 = %s" % ok_lit(X1, X0), "\tfast = False"]
  farm += visit("ok0", d01, first=True) + visit("ok1", d10, first=True)
  farm += ["\twhile num_items(HAY) < NEAR:"]
  body = []
  for k in range(8):
      body += visit("ok0", d01, water=(k == 0)) + visit("ok1", d10, water=(k == 0))
  farm += indent(body)
  farm += ["\twhile True:"]
  farm += indent(visit("ok0", d01, final=True) + visit("ok1", d10, final=True))
  farm = "\n".join(farm)

head = """# Classifica Hay_Single: 100.000.000 di fieno, 1 drone, campo 8x8. v1 dell'8 nov 2026.
# Generato da rng_predictor/haysingle/gen.py (percorso da route.py, regime tarato con regime_sim.py).
# Schema: due erbe adiacenti A = (0, 0) e C = (1, 0) e 30 cespugli su tutte le altre celle dei due
# rombi di raggio 3: il companion e' valido con prob. 1/3 x 23/24, ogni raccolto valido vale 81.920,
# ne servono circa 1.221. Il drone alterna A e C: harvest, reroll finche' il companion e' valido, mossa.
# - Semina: 35 mosse e 30 piante in un giro unico; su ogni cella attraversata l'erba iniziale e' matura:
#   se il suo companion punta a un cespuglio gia' piantato la raccoglie (circa 3,6 raccolti gratuiti).
# - Acqua: un drone solo ha tutto il serbatoio, quindi le erbe stanno vicine a 1 (crescita in circa
#   0,1 s): ogni 8 cicli, se l'acqua e' sotto WT, 4 unita' in una sola azione.
# - can_harvest solo quando serve: se l'altra cella ha trovato il companion al primo raccolto
#   (fast), il tempo dall'ultimo raccolto qui e' di sole 3 azioni e l'erba potrebbe non essere pronta;
#   altrimenti sono almeno 4 azioni e con acqua >= 0.75 e' sempre pronta.
# - Fine: controllo del fieno a ogni raccolto solo negli ultimi 3 milioni, poi return.
# Stima del simulatore: circa 2:53 (173,5 s). Non ancora provato in gioco.
GOAL = 100000000
NEAR = GOAL - 3000000
WT = 0.9

BUSH = Entities.Bush
HAY = Items.Hay
WATER = Items.Water


"""
if VER == 2:
    head = """# Classifica Hay_Single: 100.000.000 di fieno, 1 drone, campo 8x8. v2 dell'8 nov 2026.
# Generato da rng_predictor/haysingle/gen.py (VER=2, percorso route2.json da route3.py).
# La v1 ha fatto 2:52.783 in gioco (stima 2:53.5). Modifiche, misurate con regime_sim2.py su
# 80 semi appaiati:
# 1. Niente controllo can_harvest a regime e niente flag fast. Fra due raccolti della stessa erba
#    passano almeno ~810 tick (raccolto, controllo, mossa, almeno un raccolto sull'altra erba, mossa):
#    con acqua >= 0.69 l'erba e' gia' matura (3037.5 / (1 + 4w) tick). Nell'hay a 32 droni i raccolti
#    acerbi comparivano solo sotto 0.71.
# 2. Acqua solo nel ramo "companion valido al primo raccolto": if get_water() < 0.8: 4 unita' (il
#    ramo capita una volta ogni ~3 visite, quindi l'acqua non scende sotto ~0.79).
# 3. Percorso di semina di 34 mosse invece di 35 (erbe in (5, 7) e (6, 7)).
# Simulatore: circa -0.7 s sulla v1 (atteso circa 2:52.1). Verificato con emulate.py: sempre 1.221
# raccolti validi, nessun raccolto acerbo, nessun cespuglio raccolto. Non ancora provato in gioco.
GOAL = 100000000
NEAR = GOAL - 3000000
WT = 0.8

BUSH = Entities.Bush
HAY = Items.Hay
WATER = Items.Water


"""
src = head + semina + "\n\n\n" + farm + "\n\n\nsemina()\nfarm()\n"
out = os.path.join(HERE, "..", os.environ.get("OUT", "lb_hay_single_v1.py"))
open(out, "w").write(src)
print("scritto", os.path.normpath(out), src.count("\n"), "righe,", nchk, "controlli, fine semina su", "C" if X0 == C else "A")
