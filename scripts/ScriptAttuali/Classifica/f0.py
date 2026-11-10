# Classifica Hay: 2e9 fieno, 32 droni. Disposizione densa delle coppie d'erba (reticolo (6,0),(3,2),
# 421 cespugli condivisi) come lb_hay_dense.py, con tre modifiche misurate su haysim/dsim.py:
#  1. visita anticipata: ogni percorso passa su A e C a meta' piantagione; se il companion iniziale
#     non e' gia' valido si raccoglie e si rerolla subito, cosi' la prima ricrescita (a secco, 0.5 s)
#     avviene mentre il drone pianta il resto dei cespugli invece di farlo aspettare;
#  2. dizionari dei companion validi come letterali (circa 70 tick ciascuno invece di circa 390);
#  3. al rientro su A: harvest+reroll, acqua, mossa (idem su C), poi warmup e regime identici.
# Simulatore (dsim.py, 96 run, stesse sequenze di companion): circa -0.04 s rispetto a lb_hay_dense.
GOAL = 2000000000
NEAR = GOAL - 50000000
W = 0.68       # soglia acqua nella fase iniziale (solo durante le attese)
W0 = 0.4      # soglia piu' bassa nei primi cicli: il serbatoio parte vuoto
EARLY = 10    # cicli iniziali con W0
WR = 0.73     # soglia acqua a regime (controllata ogni 8 cicli; 0.71 produce raccolti acerbi)
THR = 64      # passaggio al regime quando il serbatoio supera questa scorta

BUSH = Entities.Bush
HAY = Items.Hay
WATER = Items.Water
BLOCKS = 32


def early(other):
	# visita anticipata: se il companion iniziale e' gia' un cespuglio valido lo si tiene,
	# altrimenti primo harvest e reroll economico (senza dizionario)
	c = get_companion()
	if c[0] == BUSH and c[1] != other:
		return
	harvest()
	while True:
		while get_companion()[0] != BUSH:
			harvest()
		if get_companion()[1] != other:
			return
		harvest()


# percorsi di piantagione: dall'origine, piantano i cespugli assegnati passando su A e C,
# finiscono su A e restituiscono i dizionari dei companion validi di A e di C
def r0():
	plant(BUSH)
	move(North)
	move(North)
	early((31, 2))
	move(West)
	early((0, 2))
	move(South)
	move(South)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	okA = {(BUSH, (0, 31)): True, (BUSH, (31, 0)): True, (BUSH, (0, 0)): True, (BUSH, (1, 0)): True, (BUSH, (30, 1)): True, (BUSH, (31, 1)): True, (BUSH, (0, 1)): True, (BUSH, (1, 1)): True, (BUSH, (2, 1)): True, (BUSH, (29, 2)): True, (BUSH, (30, 2)): True, (BUSH, (1, 2)): True, (BUSH, (2, 2)): True, (BUSH, (3, 2)): True, (BUSH, (30, 3)): True, (BUSH, (31, 3)): True, (BUSH, (0, 3)): True, (BUSH, (1, 3)): True, (BUSH, (2, 3)): True, (BUSH, (31, 4)): True, (BUSH, (0, 4)): True, (BUSH, (1, 4)): True, (BUSH, (0, 5)): True}
	okC = {(BUSH, (31, 31)): True, (BUSH, (30, 0)): True, (BUSH, (31, 0)): True, (BUSH, (0, 0)): True, (BUSH, (29, 1)): True, (BUSH, (30, 1)): True, (BUSH, (31, 1)): True, (BUSH, (0, 1)): True, (BUSH, (1, 1)): True, (BUSH, (28, 2)): True, (BUSH, (29, 2)): True, (BUSH, (30, 2)): True, (BUSH, (1, 2)): True, (BUSH, (2, 2)): True, (BUSH, (29, 3)): True, (BUSH, (30, 3)): True, (BUSH, (31, 3)): True, (BUSH, (0, 3)): True, (BUSH, (1, 3)): True, (BUSH, (30, 4)): True, (BUSH, (31, 4)): True, (BUSH, (0, 4)): True, (BUSH, (31, 5)): True}
	return okA, okC


def r1():
	move(South)
	plant(BUSH)
	move(South)
	early((31, 30))
	move(West)
	early((0, 30))
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	okA = {(BUSH, (0, 27)): True, (BUSH, (31, 28)): True, (BUSH, (0, 28)): True, (BUSH, (1, 28)): True, (BUSH, (30, 29)): True, (BUSH, (31, 29)): True, (BUSH, (0, 29)): True, (BUSH, (1, 29)): True, (BUSH, (2, 29)): True, (BUSH, (29, 30)): True, (BUSH, (30, 30)): True, (BUSH, (1, 30)): True, (BUSH, (2, 30)): True, (BUSH, (3, 30)): True, (BUSH, (30, 31)): True, (BUSH, (31, 31)): True, (BUSH, (0, 31)): True, (BUSH, (1, 31)): True, (BUSH, (2, 31)): True, (BUSH, (31, 0)): True, (BUSH, (0, 0)): True, (BUSH, (1, 0)): True, (BUSH, (0, 1)): True}
	okC = {(BUSH, (31, 27)): True, (BUSH, (30, 28)): True, (BUSH, (31, 28)): True, (BUSH, (0, 28)): True, (BUSH, (29, 29)): True, (BUSH, (30, 29)): True, (BUSH, (31, 29)): True, (BUSH, (0, 29)): True, (BUSH, (1, 29)): True, (BUSH, (28, 30)): True, (BUSH, (29, 30)): True, (BUSH, (30, 30)): True, (BUSH, (1, 30)): True, (BUSH, (2, 30)): True, (BUSH, (29, 31)): True, (BUSH, (30, 31)): True, (BUSH, (31, 31)): True, (BUSH, (0, 31)): True, (BUSH, (1, 31)): True, (BUSH, (30, 0)): True, (BUSH, (31, 0)): True, (BUSH, (0, 0)): True, (BUSH, (31, 1)): True}
	return okA, okC


def r2():
	move(East)
	move(East)
	early((3, 0))
	move(East)
	early((2, 0))
	move(West)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	okA = {(BUSH, (3, 29)): True, (BUSH, (2, 30)): True, (BUSH, (3, 30)): True, (BUSH, (4, 30)): True, (BUSH, (1, 31)): True, (BUSH, (2, 31)): True, (BUSH, (3, 31)): True, (BUSH, (4, 31)): True, (BUSH, (5, 31)): True, (BUSH, (0, 0)): True, (BUSH, (1, 0)): True, (BUSH, (4, 0)): True, (BUSH, (5, 0)): True, (BUSH, (6, 0)): True, (BUSH, (1, 1)): True, (BUSH, (2, 1)): True, (BUSH, (3, 1)): True, (BUSH, (4, 1)): True, (BUSH, (5, 1)): True, (BUSH, (2, 2)): True, (BUSH, (3, 2)): True, (BUSH, (4, 2)): True, (BUSH, (3, 3)): True}
	okC = {(BUSH, (2, 29)): True, (BUSH, (1, 30)): True, (BUSH, (2, 30)): True, (BUSH, (3, 30)): True, (BUSH, (0, 31)): True, (BUSH, (1, 31)): True, (BUSH, (2, 31)): True, (BUSH, (3, 31)): True, (BUSH, (4, 31)): True, (BUSH, (31, 0)): True, (BUSH, (0, 0)): True, (BUSH, (1, 0)): True, (BUSH, (4, 0)): True, (BUSH, (5, 0)): True, (BUSH, (0, 1)): True, (BUSH, (1, 1)): True, (BUSH, (2, 1)): True, (BUSH, (3, 1)): True, (BUSH, (4, 1)): True, (BUSH, (1, 2)): True, (BUSH, (2, 2)): True, (BUSH, (3, 2)): True, (BUSH, (2, 3)): True}
	return okA, okC


def r3():
	move(West)
	move(West)
	plant(BUSH)
	move(West)
	move(West)
	early((29, 0))
	move(East)
	early((28, 0))
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	okA = {(BUSH, (29, 29)): True, (BUSH, (28, 30)): True, (BUSH, (29, 30)): True, (BUSH, (30, 30)): True, (BUSH, (27, 31)): True, (BUSH, (28, 31)): True, (BUSH, (29, 31)): True, (BUSH, (30, 31)): True, (BUSH, (31, 31)): True, (BUSH, (26, 0)): True, (BUSH, (27, 0)): True, (BUSH, (30, 0)): True, (BUSH, (31, 0)): True, (BUSH, (0, 0)): True, (BUSH, (27, 1)): True, (BUSH, (28, 1)): True, (BUSH, (29, 1)): True, (BUSH, (30, 1)): True, (BUSH, (31, 1)): True, (BUSH, (28, 2)): True, (BUSH, (29, 2)): True, (BUSH, (30, 2)): True, (BUSH, (29, 3)): True}
	okC = {(BUSH, (28, 29)): True, (BUSH, (27, 30)): True, (BUSH, (28, 30)): True, (BUSH, (29, 30)): True, (BUSH, (26, 31)): True, (BUSH, (27, 31)): True, (BUSH, (28, 31)): True, (BUSH, (29, 31)): True, (BUSH, (30, 31)): True, (BUSH, (25, 0)): True, (BUSH, (26, 0)): True, (BUSH, (27, 0)): True, (BUSH, (30, 0)): True, (BUSH, (31, 0)): True, (BUSH, (26, 1)): True, (BUSH, (27, 1)): True, (BUSH, (28, 1)): True, (BUSH, (29, 1)): True, (BUSH, (30, 1)): True, (BUSH, (27, 2)): True, (BUSH, (28, 2)): True, (BUSH, (29, 2)): True, (BUSH, (28, 3)): True}
	return okA, okC


def r4():
	move(North)
	plant(BUSH)
	move(North)
	move(North)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	early((31, 6))
	move(West)
	early((0, 6))
	move(East)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	okA = {(BUSH, (31, 3)): True, (BUSH, (30, 4)): True, (BUSH, (31, 4)): True, (BUSH, (0, 4)): True, (BUSH, (29, 5)): True, (BUSH, (30, 5)): True, (BUSH, (31, 5)): True, (BUSH, (0, 5)): True, (BUSH, (1, 5)): True, (BUSH, (28, 6)): True, (BUSH, (29, 6)): True, (BUSH, (30, 6)): True, (BUSH, (1, 6)): True, (BUSH, (2, 6)): True, (BUSH, (29, 7)): True, (BUSH, (30, 7)): True, (BUSH, (31, 7)): True, (BUSH, (0, 7)): True, (BUSH, (1, 7)): True, (BUSH, (30, 8)): True, (BUSH, (31, 8)): True, (BUSH, (0, 8)): True, (BUSH, (31, 9)): True}
	okC = {(BUSH, (0, 3)): True, (BUSH, (31, 4)): True, (BUSH, (0, 4)): True, (BUSH, (1, 4)): True, (BUSH, (30, 5)): True, (BUSH, (31, 5)): True, (BUSH, (0, 5)): True, (BUSH, (1, 5)): True, (BUSH, (2, 5)): True, (BUSH, (29, 6)): True, (BUSH, (30, 6)): True, (BUSH, (1, 6)): True, (BUSH, (2, 6)): True, (BUSH, (3, 6)): True, (BUSH, (30, 7)): True, (BUSH, (31, 7)): True, (BUSH, (0, 7)): True, (BUSH, (1, 7)): True, (BUSH, (2, 7)): True, (BUSH, (31, 8)): True, (BUSH, (0, 8)): True, (BUSH, (1, 8)): True, (BUSH, (0, 9)): True}
	return okA, okC


def r5():
	move(East)
	move(North)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	move(North)
	early((3, 4))
	move(East)
	early((2, 4))
	move(West)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	okA = {(BUSH, (3, 1)): True, (BUSH, (2, 2)): True, (BUSH, (3, 2)): True, (BUSH, (4, 2)): True, (BUSH, (1, 3)): True, (BUSH, (2, 3)): True, (BUSH, (3, 3)): True, (BUSH, (4, 3)): True, (BUSH, (5, 3)): True, (BUSH, (0, 4)): True, (BUSH, (1, 4)): True, (BUSH, (4, 4)): True, (BUSH, (5, 4)): True, (BUSH, (6, 4)): True, (BUSH, (1, 5)): True, (BUSH, (2, 5)): True, (BUSH, (3, 5)): True, (BUSH, (4, 5)): True, (BUSH, (5, 5)): True, (BUSH, (2, 6)): True, (BUSH, (3, 6)): True, (BUSH, (4, 6)): True, (BUSH, (3, 7)): True}
	okC = {(BUSH, (2, 1)): True, (BUSH, (1, 2)): True, (BUSH, (2, 2)): True, (BUSH, (3, 2)): True, (BUSH, (0, 3)): True, (BUSH, (1, 3)): True, (BUSH, (2, 3)): True, (BUSH, (3, 3)): True, (BUSH, (4, 3)): True, (BUSH, (31, 4)): True, (BUSH, (0, 4)): True, (BUSH, (1, 4)): True, (BUSH, (4, 4)): True, (BUSH, (5, 4)): True, (BUSH, (0, 5)): True, (BUSH, (1, 5)): True, (BUSH, (2, 5)): True, (BUSH, (3, 5)): True, (BUSH, (4, 5)): True, (BUSH, (1, 6)): True, (BUSH, (2, 6)): True, (BUSH, (3, 6)): True, (BUSH, (2, 7)): True}
	return okA, okC


def r6():
	move(South)
	move(South)
	move(South)
	move(South)
	move(South)
	plant(BUSH)
	move(South)
	early((31, 26))
	move(West)
	early((0, 26))
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	okA = {(BUSH, (0, 23)): True, (BUSH, (31, 24)): True, (BUSH, (0, 24)): True, (BUSH, (1, 24)): True, (BUSH, (30, 25)): True, (BUSH, (31, 25)): True, (BUSH, (0, 25)): True, (BUSH, (1, 25)): True, (BUSH, (2, 25)): True, (BUSH, (29, 26)): True, (BUSH, (30, 26)): True, (BUSH, (1, 26)): True, (BUSH, (2, 26)): True, (BUSH, (3, 26)): True, (BUSH, (30, 27)): True, (BUSH, (31, 27)): True, (BUSH, (0, 27)): True, (BUSH, (1, 27)): True, (BUSH, (2, 27)): True, (BUSH, (31, 28)): True, (BUSH, (0, 28)): True, (BUSH, (1, 28)): True, (BUSH, (0, 29)): True}
	okC = {(BUSH, (31, 23)): True, (BUSH, (30, 24)): True, (BUSH, (31, 24)): True, (BUSH, (0, 24)): True, (BUSH, (29, 25)): True, (BUSH, (30, 25)): True, (BUSH, (31, 25)): True, (BUSH, (0, 25)): True, (BUSH, (1, 25)): True, (BUSH, (28, 26)): True, (BUSH, (29, 26)): True, (BUSH, (30, 26)): True, (BUSH, (1, 26)): True, (BUSH, (2, 26)): True, (BUSH, (29, 27)): True, (BUSH, (30, 27)): True, (BUSH, (31, 27)): True, (BUSH, (0, 27)): True, (BUSH, (1, 27)): True, (BUSH, (30, 28)): True, (BUSH, (31, 28)): True, (BUSH, (0, 28)): True, (BUSH, (31, 29)): True}
	return okA, okC


def r7():
	move(East)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	move(South)
	move(South)
	early((3, 28))
	move(East)
	early((2, 28))
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	move(East)
	plant(BUSH)
	move(South)
	okA = {(BUSH, (3, 25)): True, (BUSH, (2, 26)): True, (BUSH, (3, 26)): True, (BUSH, (4, 26)): True, (BUSH, (1, 27)): True, (BUSH, (2, 27)): True, (BUSH, (3, 27)): True, (BUSH, (4, 27)): True, (BUSH, (5, 27)): True, (BUSH, (0, 28)): True, (BUSH, (1, 28)): True, (BUSH, (4, 28)): True, (BUSH, (5, 28)): True, (BUSH, (6, 28)): True, (BUSH, (1, 29)): True, (BUSH, (2, 29)): True, (BUSH, (3, 29)): True, (BUSH, (4, 29)): True, (BUSH, (5, 29)): True, (BUSH, (2, 30)): True, (BUSH, (3, 30)): True, (BUSH, (4, 30)): True, (BUSH, (3, 31)): True}
	okC = {(BUSH, (2, 25)): True, (BUSH, (1, 26)): True, (BUSH, (2, 26)): True, (BUSH, (3, 26)): True, (BUSH, (0, 27)): True, (BUSH, (1, 27)): True, (BUSH, (2, 27)): True, (BUSH, (3, 27)): True, (BUSH, (4, 27)): True, (BUSH, (31, 28)): True, (BUSH, (0, 28)): True, (BUSH, (1, 28)): True, (BUSH, (4, 28)): True, (BUSH, (5, 28)): True, (BUSH, (0, 29)): True, (BUSH, (1, 29)): True, (BUSH, (2, 29)): True, (BUSH, (3, 29)): True, (BUSH, (4, 29)): True, (BUSH, (1, 30)): True, (BUSH, (2, 30)): True, (BUSH, (3, 30)): True, (BUSH, (2, 31)): True}
	return okA, okC


def r8():
	move(West)
	move(West)
	move(West)
	move(North)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	early((28, 4))
	move(West)
	early((29, 4))
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	okA = {(BUSH, (29, 1)): True, (BUSH, (28, 2)): True, (BUSH, (29, 2)): True, (BUSH, (30, 2)): True, (BUSH, (27, 3)): True, (BUSH, (28, 3)): True, (BUSH, (29, 3)): True, (BUSH, (30, 3)): True, (BUSH, (31, 3)): True, (BUSH, (26, 4)): True, (BUSH, (27, 4)): True, (BUSH, (30, 4)): True, (BUSH, (31, 4)): True, (BUSH, (0, 4)): True, (BUSH, (27, 5)): True, (BUSH, (28, 5)): True, (BUSH, (29, 5)): True, (BUSH, (30, 5)): True, (BUSH, (31, 5)): True, (BUSH, (28, 6)): True, (BUSH, (29, 6)): True, (BUSH, (30, 6)): True, (BUSH, (29, 7)): True}
	okC = {(BUSH, (28, 1)): True, (BUSH, (27, 2)): True, (BUSH, (28, 2)): True, (BUSH, (29, 2)): True, (BUSH, (26, 3)): True, (BUSH, (27, 3)): True, (BUSH, (28, 3)): True, (BUSH, (29, 3)): True, (BUSH, (30, 3)): True, (BUSH, (25, 4)): True, (BUSH, (26, 4)): True, (BUSH, (27, 4)): True, (BUSH, (30, 4)): True, (BUSH, (31, 4)): True, (BUSH, (26, 5)): True, (BUSH, (27, 5)): True, (BUSH, (28, 5)): True, (BUSH, (29, 5)): True, (BUSH, (30, 5)): True, (BUSH, (27, 6)): True, (BUSH, (28, 6)): True, (BUSH, (29, 6)): True, (BUSH, (28, 7)): True}
	return okA, okC


def r9():
	move(West)
	move(West)
	move(West)
	move(South)
	move(South)
	move(South)
	plant(BUSH)
	move(South)
	early((28, 28))
	move(West)
	early((29, 28))
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	okA = {(BUSH, (29, 25)): True, (BUSH, (28, 26)): True, (BUSH, (29, 26)): True, (BUSH, (30, 26)): True, (BUSH, (27, 27)): True, (BUSH, (28, 27)): True, (BUSH, (29, 27)): True, (BUSH, (30, 27)): True, (BUSH, (31, 27)): True, (BUSH, (26, 28)): True, (BUSH, (27, 28)): True, (BUSH, (30, 28)): True, (BUSH, (31, 28)): True, (BUSH, (0, 28)): True, (BUSH, (27, 29)): True, (BUSH, (28, 29)): True, (BUSH, (29, 29)): True, (BUSH, (30, 29)): True, (BUSH, (31, 29)): True, (BUSH, (28, 30)): True, (BUSH, (29, 30)): True, (BUSH, (30, 30)): True, (BUSH, (29, 31)): True}
	okC = {(BUSH, (28, 25)): True, (BUSH, (27, 26)): True, (BUSH, (28, 26)): True, (BUSH, (29, 26)): True, (BUSH, (26, 27)): True, (BUSH, (27, 27)): True, (BUSH, (28, 27)): True, (BUSH, (29, 27)): True, (BUSH, (30, 27)): True, (BUSH, (25, 28)): True, (BUSH, (26, 28)): True, (BUSH, (27, 28)): True, (BUSH, (30, 28)): True, (BUSH, (31, 28)): True, (BUSH, (26, 29)): True, (BUSH, (27, 29)): True, (BUSH, (28, 29)): True, (BUSH, (29, 29)): True, (BUSH, (30, 29)): True, (BUSH, (27, 30)): True, (BUSH, (28, 30)): True, (BUSH, (29, 30)): True, (BUSH, (28, 31)): True}
	return okA, okC


def r10():
	move(East)
	move(East)
	move(North)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	move(East)
	early((6, 2))
	move(East)
	early((5, 2))
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	okA = {(BUSH, (6, 31)): True, (BUSH, (5, 0)): True, (BUSH, (6, 0)): True, (BUSH, (7, 0)): True, (BUSH, (4, 1)): True, (BUSH, (5, 1)): True, (BUSH, (6, 1)): True, (BUSH, (7, 1)): True, (BUSH, (8, 1)): True, (BUSH, (3, 2)): True, (BUSH, (4, 2)): True, (BUSH, (7, 2)): True, (BUSH, (8, 2)): True, (BUSH, (9, 2)): True, (BUSH, (4, 3)): True, (BUSH, (5, 3)): True, (BUSH, (6, 3)): True, (BUSH, (7, 3)): True, (BUSH, (8, 3)): True, (BUSH, (5, 4)): True, (BUSH, (6, 4)): True, (BUSH, (7, 4)): True, (BUSH, (6, 5)): True}
	okC = {(BUSH, (5, 31)): True, (BUSH, (4, 0)): True, (BUSH, (5, 0)): True, (BUSH, (6, 0)): True, (BUSH, (3, 1)): True, (BUSH, (4, 1)): True, (BUSH, (5, 1)): True, (BUSH, (6, 1)): True, (BUSH, (7, 1)): True, (BUSH, (2, 2)): True, (BUSH, (3, 2)): True, (BUSH, (4, 2)): True, (BUSH, (7, 2)): True, (BUSH, (8, 2)): True, (BUSH, (3, 3)): True, (BUSH, (4, 3)): True, (BUSH, (5, 3)): True, (BUSH, (6, 3)): True, (BUSH, (7, 3)): True, (BUSH, (4, 4)): True, (BUSH, (5, 4)): True, (BUSH, (6, 4)): True, (BUSH, (5, 5)): True}
	return okA, okC


def r11():
	move(East)
	move(East)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	move(East)
	early((6, 30))
	move(East)
	early((5, 30))
	move(West)
	move(West)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	okA = {(BUSH, (6, 27)): True, (BUSH, (5, 28)): True, (BUSH, (6, 28)): True, (BUSH, (7, 28)): True, (BUSH, (4, 29)): True, (BUSH, (5, 29)): True, (BUSH, (6, 29)): True, (BUSH, (7, 29)): True, (BUSH, (8, 29)): True, (BUSH, (3, 30)): True, (BUSH, (4, 30)): True, (BUSH, (7, 30)): True, (BUSH, (8, 30)): True, (BUSH, (9, 30)): True, (BUSH, (4, 31)): True, (BUSH, (5, 31)): True, (BUSH, (6, 31)): True, (BUSH, (7, 31)): True, (BUSH, (8, 31)): True, (BUSH, (5, 0)): True, (BUSH, (6, 0)): True, (BUSH, (7, 0)): True, (BUSH, (6, 1)): True}
	okC = {(BUSH, (5, 27)): True, (BUSH, (4, 28)): True, (BUSH, (5, 28)): True, (BUSH, (6, 28)): True, (BUSH, (3, 29)): True, (BUSH, (4, 29)): True, (BUSH, (5, 29)): True, (BUSH, (6, 29)): True, (BUSH, (7, 29)): True, (BUSH, (2, 30)): True, (BUSH, (3, 30)): True, (BUSH, (4, 30)): True, (BUSH, (7, 30)): True, (BUSH, (8, 30)): True, (BUSH, (3, 31)): True, (BUSH, (4, 31)): True, (BUSH, (5, 31)): True, (BUSH, (6, 31)): True, (BUSH, (7, 31)): True, (BUSH, (4, 0)): True, (BUSH, (5, 0)): True, (BUSH, (6, 0)): True, (BUSH, (5, 1)): True}
	return okA, okC


def r12():
	move(West)
	move(West)
	move(West)
	move(West)
	move(West)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	early((25, 2))
	move(West)
	early((26, 2))
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	okA = {(BUSH, (26, 31)): True, (BUSH, (25, 0)): True, (BUSH, (26, 0)): True, (BUSH, (27, 0)): True, (BUSH, (24, 1)): True, (BUSH, (25, 1)): True, (BUSH, (26, 1)): True, (BUSH, (27, 1)): True, (BUSH, (28, 1)): True, (BUSH, (23, 2)): True, (BUSH, (24, 2)): True, (BUSH, (27, 2)): True, (BUSH, (28, 2)): True, (BUSH, (29, 2)): True, (BUSH, (24, 3)): True, (BUSH, (25, 3)): True, (BUSH, (26, 3)): True, (BUSH, (27, 3)): True, (BUSH, (28, 3)): True, (BUSH, (25, 4)): True, (BUSH, (26, 4)): True, (BUSH, (27, 4)): True, (BUSH, (26, 5)): True}
	okC = {(BUSH, (25, 31)): True, (BUSH, (24, 0)): True, (BUSH, (25, 0)): True, (BUSH, (26, 0)): True, (BUSH, (23, 1)): True, (BUSH, (24, 1)): True, (BUSH, (25, 1)): True, (BUSH, (26, 1)): True, (BUSH, (27, 1)): True, (BUSH, (22, 2)): True, (BUSH, (23, 2)): True, (BUSH, (24, 2)): True, (BUSH, (27, 2)): True, (BUSH, (28, 2)): True, (BUSH, (23, 3)): True, (BUSH, (24, 3)): True, (BUSH, (25, 3)): True, (BUSH, (26, 3)): True, (BUSH, (27, 3)): True, (BUSH, (24, 4)): True, (BUSH, (25, 4)): True, (BUSH, (26, 4)): True, (BUSH, (25, 5)): True}
	return okA, okC


def r13():
	move(West)
	move(West)
	move(West)
	move(West)
	move(West)
	move(West)
	move(South)
	plant(BUSH)
	move(South)
	early((25, 30))
	move(West)
	early((26, 30))
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	okA = {(BUSH, (26, 27)): True, (BUSH, (25, 28)): True, (BUSH, (26, 28)): True, (BUSH, (27, 28)): True, (BUSH, (24, 29)): True, (BUSH, (25, 29)): True, (BUSH, (26, 29)): True, (BUSH, (27, 29)): True, (BUSH, (28, 29)): True, (BUSH, (23, 30)): True, (BUSH, (24, 30)): True, (BUSH, (27, 30)): True, (BUSH, (28, 30)): True, (BUSH, (29, 30)): True, (BUSH, (24, 31)): True, (BUSH, (25, 31)): True, (BUSH, (26, 31)): True, (BUSH, (27, 31)): True, (BUSH, (28, 31)): True, (BUSH, (25, 0)): True, (BUSH, (26, 0)): True, (BUSH, (27, 0)): True, (BUSH, (26, 1)): True}
	okC = {(BUSH, (25, 27)): True, (BUSH, (24, 28)): True, (BUSH, (25, 28)): True, (BUSH, (26, 28)): True, (BUSH, (23, 29)): True, (BUSH, (24, 29)): True, (BUSH, (25, 29)): True, (BUSH, (26, 29)): True, (BUSH, (27, 29)): True, (BUSH, (22, 30)): True, (BUSH, (23, 30)): True, (BUSH, (24, 30)): True, (BUSH, (27, 30)): True, (BUSH, (28, 30)): True, (BUSH, (23, 31)): True, (BUSH, (24, 31)): True, (BUSH, (25, 31)): True, (BUSH, (26, 31)): True, (BUSH, (27, 31)): True, (BUSH, (24, 0)): True, (BUSH, (25, 0)): True, (BUSH, (26, 0)): True, (BUSH, (25, 1)): True}
	return okA, okC


def r14():
	move(East)
	move(East)
	move(East)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	move(East)
	early((9, 0))
	move(East)
	early((8, 0))
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	okA = {(BUSH, (9, 29)): True, (BUSH, (8, 30)): True, (BUSH, (9, 30)): True, (BUSH, (10, 30)): True, (BUSH, (7, 31)): True, (BUSH, (8, 31)): True, (BUSH, (9, 31)): True, (BUSH, (10, 31)): True, (BUSH, (11, 31)): True, (BUSH, (6, 0)): True, (BUSH, (7, 0)): True, (BUSH, (10, 0)): True, (BUSH, (11, 0)): True, (BUSH, (12, 0)): True, (BUSH, (7, 1)): True, (BUSH, (8, 1)): True, (BUSH, (9, 1)): True, (BUSH, (10, 1)): True, (BUSH, (11, 1)): True, (BUSH, (8, 2)): True, (BUSH, (9, 2)): True, (BUSH, (10, 2)): True, (BUSH, (9, 3)): True}
	okC = {(BUSH, (8, 29)): True, (BUSH, (7, 30)): True, (BUSH, (8, 30)): True, (BUSH, (9, 30)): True, (BUSH, (6, 31)): True, (BUSH, (7, 31)): True, (BUSH, (8, 31)): True, (BUSH, (9, 31)): True, (BUSH, (10, 31)): True, (BUSH, (5, 0)): True, (BUSH, (6, 0)): True, (BUSH, (7, 0)): True, (BUSH, (10, 0)): True, (BUSH, (11, 0)): True, (BUSH, (6, 1)): True, (BUSH, (7, 1)): True, (BUSH, (8, 1)): True, (BUSH, (9, 1)): True, (BUSH, (10, 1)): True, (BUSH, (7, 2)): True, (BUSH, (8, 2)): True, (BUSH, (9, 2)): True, (BUSH, (8, 3)): True}
	return okA, okC


def r15():
	move(West)
	move(West)
	move(West)
	move(West)
	move(West)
	move(West)
	move(West)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(West)
	move(West)
	early((23, 0))
	move(East)
	early((22, 0))
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	move(North)
	plant(BUSH)
	move(West)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(South)
	move(South)
	okA = {(BUSH, (22, 29)): True, (BUSH, (21, 30)): True, (BUSH, (22, 30)): True, (BUSH, (23, 30)): True, (BUSH, (20, 31)): True, (BUSH, (21, 31)): True, (BUSH, (22, 31)): True, (BUSH, (23, 31)): True, (BUSH, (24, 31)): True, (BUSH, (19, 0)): True, (BUSH, (20, 0)): True, (BUSH, (21, 0)): True, (BUSH, (24, 0)): True, (BUSH, (25, 0)): True, (BUSH, (20, 1)): True, (BUSH, (21, 1)): True, (BUSH, (22, 1)): True, (BUSH, (23, 1)): True, (BUSH, (24, 1)): True, (BUSH, (21, 2)): True, (BUSH, (22, 2)): True, (BUSH, (23, 2)): True, (BUSH, (22, 3)): True}
	okC = {(BUSH, (23, 29)): True, (BUSH, (22, 30)): True, (BUSH, (23, 30)): True, (BUSH, (24, 30)): True, (BUSH, (21, 31)): True, (BUSH, (22, 31)): True, (BUSH, (23, 31)): True, (BUSH, (24, 31)): True, (BUSH, (25, 31)): True, (BUSH, (20, 0)): True, (BUSH, (21, 0)): True, (BUSH, (24, 0)): True, (BUSH, (25, 0)): True, (BUSH, (26, 0)): True, (BUSH, (21, 1)): True, (BUSH, (22, 1)): True, (BUSH, (23, 1)): True, (BUSH, (24, 1)): True, (BUSH, (25, 1)): True, (BUSH, (22, 2)): True, (BUSH, (23, 2)): True, (BUSH, (24, 2)): True, (BUSH, (23, 3)): True}
	return okA, okC


def r16():
	move(North)
	move(North)
	move(North)
	move(North)
	move(North)
	move(North)
	move(North)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	move(North)
	early((0, 10))
	move(East)
	early((31, 10))
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(East)
	move(East)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	okA = {(BUSH, (0, 7)): True, (BUSH, (31, 8)): True, (BUSH, (0, 8)): True, (BUSH, (1, 8)): True, (BUSH, (30, 9)): True, (BUSH, (31, 9)): True, (BUSH, (0, 9)): True, (BUSH, (1, 9)): True, (BUSH, (2, 9)): True, (BUSH, (29, 10)): True, (BUSH, (30, 10)): True, (BUSH, (1, 10)): True, (BUSH, (2, 10)): True, (BUSH, (3, 10)): True, (BUSH, (30, 11)): True, (BUSH, (31, 11)): True, (BUSH, (0, 11)): True, (BUSH, (1, 11)): True, (BUSH, (2, 11)): True, (BUSH, (31, 12)): True, (BUSH, (0, 12)): True, (BUSH, (1, 12)): True, (BUSH, (0, 13)): True}
	okC = {(BUSH, (31, 7)): True, (BUSH, (30, 8)): True, (BUSH, (31, 8)): True, (BUSH, (0, 8)): True, (BUSH, (29, 9)): True, (BUSH, (30, 9)): True, (BUSH, (31, 9)): True, (BUSH, (0, 9)): True, (BUSH, (1, 9)): True, (BUSH, (28, 10)): True, (BUSH, (29, 10)): True, (BUSH, (30, 10)): True, (BUSH, (1, 10)): True, (BUSH, (2, 10)): True, (BUSH, (29, 11)): True, (BUSH, (30, 11)): True, (BUSH, (31, 11)): True, (BUSH, (0, 11)): True, (BUSH, (1, 11)): True, (BUSH, (30, 12)): True, (BUSH, (31, 12)): True, (BUSH, (0, 12)): True, (BUSH, (31, 13)): True}
	return okA, okC


def r17():
	move(East)
	move(North)
	move(North)
	move(North)
	move(North)
	move(North)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	early((3, 8))
	move(East)
	early((2, 8))
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	okA = {(BUSH, (2, 5)): True, (BUSH, (1, 6)): True, (BUSH, (2, 6)): True, (BUSH, (3, 6)): True, (BUSH, (0, 7)): True, (BUSH, (1, 7)): True, (BUSH, (2, 7)): True, (BUSH, (3, 7)): True, (BUSH, (4, 7)): True, (BUSH, (31, 8)): True, (BUSH, (0, 8)): True, (BUSH, (1, 8)): True, (BUSH, (4, 8)): True, (BUSH, (5, 8)): True, (BUSH, (0, 9)): True, (BUSH, (1, 9)): True, (BUSH, (2, 9)): True, (BUSH, (3, 9)): True, (BUSH, (4, 9)): True, (BUSH, (1, 10)): True, (BUSH, (2, 10)): True, (BUSH, (3, 10)): True, (BUSH, (2, 11)): True}
	okC = {(BUSH, (3, 5)): True, (BUSH, (2, 6)): True, (BUSH, (3, 6)): True, (BUSH, (4, 6)): True, (BUSH, (1, 7)): True, (BUSH, (2, 7)): True, (BUSH, (3, 7)): True, (BUSH, (4, 7)): True, (BUSH, (5, 7)): True, (BUSH, (0, 8)): True, (BUSH, (1, 8)): True, (BUSH, (4, 8)): True, (BUSH, (5, 8)): True, (BUSH, (6, 8)): True, (BUSH, (1, 9)): True, (BUSH, (2, 9)): True, (BUSH, (3, 9)): True, (BUSH, (4, 9)): True, (BUSH, (5, 9)): True, (BUSH, (2, 10)): True, (BUSH, (3, 10)): True, (BUSH, (4, 10)): True, (BUSH, (3, 11)): True}
	return okA, okC


def r18():
	move(South)
	move(South)
	move(South)
	move(South)
	move(South)
	move(South)
	move(South)
	move(South)
	move(South)
	plant(BUSH)
	move(South)
	early((31, 22))
	move(West)
	early((0, 22))
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(East)
	move(East)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	okA = {(BUSH, (0, 19)): True, (BUSH, (31, 20)): True, (BUSH, (0, 20)): True, (BUSH, (1, 20)): True, (BUSH, (30, 21)): True, (BUSH, (31, 21)): True, (BUSH, (0, 21)): True, (BUSH, (1, 21)): True, (BUSH, (2, 21)): True, (BUSH, (29, 22)): True, (BUSH, (30, 22)): True, (BUSH, (1, 22)): True, (BUSH, (2, 22)): True, (BUSH, (3, 22)): True, (BUSH, (30, 23)): True, (BUSH, (31, 23)): True, (BUSH, (0, 23)): True, (BUSH, (1, 23)): True, (BUSH, (2, 23)): True, (BUSH, (31, 24)): True, (BUSH, (0, 24)): True, (BUSH, (1, 24)): True, (BUSH, (0, 25)): True}
	okC = {(BUSH, (31, 19)): True, (BUSH, (30, 20)): True, (BUSH, (31, 20)): True, (BUSH, (0, 20)): True, (BUSH, (29, 21)): True, (BUSH, (30, 21)): True, (BUSH, (31, 21)): True, (BUSH, (0, 21)): True, (BUSH, (1, 21)): True, (BUSH, (28, 22)): True, (BUSH, (29, 22)): True, (BUSH, (30, 22)): True, (BUSH, (1, 22)): True, (BUSH, (2, 22)): True, (BUSH, (29, 23)): True, (BUSH, (30, 23)): True, (BUSH, (31, 23)): True, (BUSH, (0, 23)): True, (BUSH, (1, 23)): True, (BUSH, (30, 24)): True, (BUSH, (31, 24)): True, (BUSH, (0, 24)): True, (BUSH, (31, 25)): True}
	return okA, okC


def r19():
	move(East)
	move(South)
	move(South)
	move(South)
	move(South)
	move(South)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	early((3, 24))
	move(East)
	early((2, 24))
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(South)
	okA = {(BUSH, (2, 21)): True, (BUSH, (1, 22)): True, (BUSH, (2, 22)): True, (BUSH, (3, 22)): True, (BUSH, (0, 23)): True, (BUSH, (1, 23)): True, (BUSH, (2, 23)): True, (BUSH, (3, 23)): True, (BUSH, (4, 23)): True, (BUSH, (31, 24)): True, (BUSH, (0, 24)): True, (BUSH, (1, 24)): True, (BUSH, (4, 24)): True, (BUSH, (5, 24)): True, (BUSH, (0, 25)): True, (BUSH, (1, 25)): True, (BUSH, (2, 25)): True, (BUSH, (3, 25)): True, (BUSH, (4, 25)): True, (BUSH, (1, 26)): True, (BUSH, (2, 26)): True, (BUSH, (3, 26)): True, (BUSH, (2, 27)): True}
	okC = {(BUSH, (3, 21)): True, (BUSH, (2, 22)): True, (BUSH, (3, 22)): True, (BUSH, (4, 22)): True, (BUSH, (1, 23)): True, (BUSH, (2, 23)): True, (BUSH, (3, 23)): True, (BUSH, (4, 23)): True, (BUSH, (5, 23)): True, (BUSH, (0, 24)): True, (BUSH, (1, 24)): True, (BUSH, (4, 24)): True, (BUSH, (5, 24)): True, (BUSH, (6, 24)): True, (BUSH, (1, 25)): True, (BUSH, (2, 25)): True, (BUSH, (3, 25)): True, (BUSH, (4, 25)): True, (BUSH, (5, 25)): True, (BUSH, (2, 26)): True, (BUSH, (3, 26)): True, (BUSH, (4, 26)): True, (BUSH, (3, 27)): True}
	return okA, okC


def r20():
	move(West)
	move(North)
	move(North)
	move(North)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	move(North)
	move(North)
	move(North)
	plant(BUSH)
	move(West)
	early((28, 8))
	move(West)
	early((29, 8))
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(South)
	move(South)
	move(South)
	okA = {(BUSH, (28, 5)): True, (BUSH, (27, 6)): True, (BUSH, (28, 6)): True, (BUSH, (29, 6)): True, (BUSH, (26, 7)): True, (BUSH, (27, 7)): True, (BUSH, (28, 7)): True, (BUSH, (29, 7)): True, (BUSH, (30, 7)): True, (BUSH, (25, 8)): True, (BUSH, (26, 8)): True, (BUSH, (27, 8)): True, (BUSH, (30, 8)): True, (BUSH, (31, 8)): True, (BUSH, (26, 9)): True, (BUSH, (27, 9)): True, (BUSH, (28, 9)): True, (BUSH, (29, 9)): True, (BUSH, (30, 9)): True, (BUSH, (27, 10)): True, (BUSH, (28, 10)): True, (BUSH, (29, 10)): True, (BUSH, (28, 11)): True}
	okC = {(BUSH, (29, 5)): True, (BUSH, (28, 6)): True, (BUSH, (29, 6)): True, (BUSH, (30, 6)): True, (BUSH, (27, 7)): True, (BUSH, (28, 7)): True, (BUSH, (29, 7)): True, (BUSH, (30, 7)): True, (BUSH, (31, 7)): True, (BUSH, (26, 8)): True, (BUSH, (27, 8)): True, (BUSH, (30, 8)): True, (BUSH, (31, 8)): True, (BUSH, (0, 8)): True, (BUSH, (27, 9)): True, (BUSH, (28, 9)): True, (BUSH, (29, 9)): True, (BUSH, (30, 9)): True, (BUSH, (31, 9)): True, (BUSH, (28, 10)): True, (BUSH, (29, 10)): True, (BUSH, (30, 10)): True, (BUSH, (29, 11)): True}
	return okA, okC


def r21():
	move(East)
	move(East)
	move(North)
	move(North)
	move(North)
	plant(BUSH)
	move(North)
	move(North)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	early((6, 6))
	move(East)
	early((5, 6))
	move(South)
	plant(BUSH)
	move(North)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	okA = {(BUSH, (6, 3)): True, (BUSH, (5, 4)): True, (BUSH, (6, 4)): True, (BUSH, (7, 4)): True, (BUSH, (4, 5)): True, (BUSH, (5, 5)): True, (BUSH, (6, 5)): True, (BUSH, (7, 5)): True, (BUSH, (8, 5)): True, (BUSH, (3, 6)): True, (BUSH, (4, 6)): True, (BUSH, (7, 6)): True, (BUSH, (8, 6)): True, (BUSH, (9, 6)): True, (BUSH, (4, 7)): True, (BUSH, (5, 7)): True, (BUSH, (6, 7)): True, (BUSH, (7, 7)): True, (BUSH, (8, 7)): True, (BUSH, (5, 8)): True, (BUSH, (6, 8)): True, (BUSH, (7, 8)): True, (BUSH, (6, 9)): True}
	okC = {(BUSH, (5, 3)): True, (BUSH, (4, 4)): True, (BUSH, (5, 4)): True, (BUSH, (6, 4)): True, (BUSH, (3, 5)): True, (BUSH, (4, 5)): True, (BUSH, (5, 5)): True, (BUSH, (6, 5)): True, (BUSH, (7, 5)): True, (BUSH, (2, 6)): True, (BUSH, (3, 6)): True, (BUSH, (4, 6)): True, (BUSH, (7, 6)): True, (BUSH, (8, 6)): True, (BUSH, (3, 7)): True, (BUSH, (4, 7)): True, (BUSH, (5, 7)): True, (BUSH, (6, 7)): True, (BUSH, (7, 7)): True, (BUSH, (4, 8)): True, (BUSH, (5, 8)): True, (BUSH, (6, 8)): True, (BUSH, (5, 9)): True}
	return okA, okC


def r22():
	move(West)
	move(West)
	move(South)
	move(South)
	move(South)
	move(South)
	plant(BUSH)
	move(South)
	move(South)
	move(South)
	move(South)
	plant(BUSH)
	move(West)
	early((28, 24))
	move(West)
	early((29, 24))
	move(East)
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(South)
	move(South)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	okA = {(BUSH, (29, 21)): True, (BUSH, (28, 22)): True, (BUSH, (29, 22)): True, (BUSH, (30, 22)): True, (BUSH, (27, 23)): True, (BUSH, (28, 23)): True, (BUSH, (29, 23)): True, (BUSH, (30, 23)): True, (BUSH, (31, 23)): True, (BUSH, (26, 24)): True, (BUSH, (27, 24)): True, (BUSH, (30, 24)): True, (BUSH, (31, 24)): True, (BUSH, (0, 24)): True, (BUSH, (27, 25)): True, (BUSH, (28, 25)): True, (BUSH, (29, 25)): True, (BUSH, (30, 25)): True, (BUSH, (31, 25)): True, (BUSH, (28, 26)): True, (BUSH, (29, 26)): True, (BUSH, (30, 26)): True, (BUSH, (29, 27)): True}
	okC = {(BUSH, (28, 21)): True, (BUSH, (27, 22)): True, (BUSH, (28, 22)): True, (BUSH, (29, 22)): True, (BUSH, (26, 23)): True, (BUSH, (27, 23)): True, (BUSH, (28, 23)): True, (BUSH, (29, 23)): True, (BUSH, (30, 23)): True, (BUSH, (25, 24)): True, (BUSH, (26, 24)): True, (BUSH, (27, 24)): True, (BUSH, (30, 24)): True, (BUSH, (31, 24)): True, (BUSH, (26, 25)): True, (BUSH, (27, 25)): True, (BUSH, (28, 25)): True, (BUSH, (29, 25)): True, (BUSH, (30, 25)): True, (BUSH, (27, 26)): True, (BUSH, (28, 26)): True, (BUSH, (29, 26)): True, (BUSH, (28, 27)): True}
	return okA, okC


def r23():
	move(East)
	move(East)
	move(South)
	move(South)
	move(South)
	plant(BUSH)
	move(South)
	move(South)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	early((6, 26))
	move(East)
	early((5, 26))
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(West)
	move(North)
	okA = {(BUSH, (5, 23)): True, (BUSH, (4, 24)): True, (BUSH, (5, 24)): True, (BUSH, (6, 24)): True, (BUSH, (3, 25)): True, (BUSH, (4, 25)): True, (BUSH, (5, 25)): True, (BUSH, (6, 25)): True, (BUSH, (7, 25)): True, (BUSH, (2, 26)): True, (BUSH, (3, 26)): True, (BUSH, (4, 26)): True, (BUSH, (7, 26)): True, (BUSH, (8, 26)): True, (BUSH, (3, 27)): True, (BUSH, (4, 27)): True, (BUSH, (5, 27)): True, (BUSH, (6, 27)): True, (BUSH, (7, 27)): True, (BUSH, (4, 28)): True, (BUSH, (5, 28)): True, (BUSH, (6, 28)): True, (BUSH, (5, 29)): True}
	okC = {(BUSH, (6, 23)): True, (BUSH, (5, 24)): True, (BUSH, (6, 24)): True, (BUSH, (7, 24)): True, (BUSH, (4, 25)): True, (BUSH, (5, 25)): True, (BUSH, (6, 25)): True, (BUSH, (7, 25)): True, (BUSH, (8, 25)): True, (BUSH, (3, 26)): True, (BUSH, (4, 26)): True, (BUSH, (7, 26)): True, (BUSH, (8, 26)): True, (BUSH, (9, 26)): True, (BUSH, (4, 27)): True, (BUSH, (5, 27)): True, (BUSH, (6, 27)): True, (BUSH, (7, 27)): True, (BUSH, (8, 27)): True, (BUSH, (5, 28)): True, (BUSH, (6, 28)): True, (BUSH, (7, 28)): True, (BUSH, (6, 29)): True}
	return okA, okC


def r24():
	move(West)
	move(West)
	move(West)
	move(West)
	move(North)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	move(North)
	move(North)
	move(North)
	plant(BUSH)
	move(West)
	early((25, 6))
	move(West)
	early((26, 6))
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(South)
	move(South)
	move(South)
	okA = {(BUSH, (25, 3)): True, (BUSH, (24, 4)): True, (BUSH, (25, 4)): True, (BUSH, (26, 4)): True, (BUSH, (23, 5)): True, (BUSH, (24, 5)): True, (BUSH, (25, 5)): True, (BUSH, (26, 5)): True, (BUSH, (27, 5)): True, (BUSH, (22, 6)): True, (BUSH, (23, 6)): True, (BUSH, (24, 6)): True, (BUSH, (27, 6)): True, (BUSH, (28, 6)): True, (BUSH, (23, 7)): True, (BUSH, (24, 7)): True, (BUSH, (25, 7)): True, (BUSH, (26, 7)): True, (BUSH, (27, 7)): True, (BUSH, (24, 8)): True, (BUSH, (25, 8)): True, (BUSH, (26, 8)): True, (BUSH, (25, 9)): True}
	okC = {(BUSH, (26, 3)): True, (BUSH, (25, 4)): True, (BUSH, (26, 4)): True, (BUSH, (27, 4)): True, (BUSH, (24, 5)): True, (BUSH, (25, 5)): True, (BUSH, (26, 5)): True, (BUSH, (27, 5)): True, (BUSH, (28, 5)): True, (BUSH, (23, 6)): True, (BUSH, (24, 6)): True, (BUSH, (27, 6)): True, (BUSH, (28, 6)): True, (BUSH, (29, 6)): True, (BUSH, (24, 7)): True, (BUSH, (25, 7)): True, (BUSH, (26, 7)): True, (BUSH, (27, 7)): True, (BUSH, (28, 7)): True, (BUSH, (25, 8)): True, (BUSH, (26, 8)): True, (BUSH, (27, 8)): True, (BUSH, (26, 9)): True}
	return okA, okC


def r25():
	move(West)
	move(West)
	move(West)
	move(West)
	move(West)
	move(South)
	move(South)
	plant(BUSH)
	move(South)
	move(South)
	move(South)
	move(South)
	plant(BUSH)
	move(West)
	early((25, 26))
	move(West)
	early((26, 26))
	move(East)
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(South)
	move(South)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	okA = {(BUSH, (26, 23)): True, (BUSH, (25, 24)): True, (BUSH, (26, 24)): True, (BUSH, (27, 24)): True, (BUSH, (24, 25)): True, (BUSH, (25, 25)): True, (BUSH, (26, 25)): True, (BUSH, (27, 25)): True, (BUSH, (28, 25)): True, (BUSH, (23, 26)): True, (BUSH, (24, 26)): True, (BUSH, (27, 26)): True, (BUSH, (28, 26)): True, (BUSH, (29, 26)): True, (BUSH, (24, 27)): True, (BUSH, (25, 27)): True, (BUSH, (26, 27)): True, (BUSH, (27, 27)): True, (BUSH, (28, 27)): True, (BUSH, (25, 28)): True, (BUSH, (26, 28)): True, (BUSH, (27, 28)): True, (BUSH, (26, 29)): True}
	okC = {(BUSH, (25, 23)): True, (BUSH, (24, 24)): True, (BUSH, (25, 24)): True, (BUSH, (26, 24)): True, (BUSH, (23, 25)): True, (BUSH, (24, 25)): True, (BUSH, (25, 25)): True, (BUSH, (26, 25)): True, (BUSH, (27, 25)): True, (BUSH, (22, 26)): True, (BUSH, (23, 26)): True, (BUSH, (24, 26)): True, (BUSH, (27, 26)): True, (BUSH, (28, 26)): True, (BUSH, (23, 27)): True, (BUSH, (24, 27)): True, (BUSH, (25, 27)): True, (BUSH, (26, 27)): True, (BUSH, (27, 27)): True, (BUSH, (24, 28)): True, (BUSH, (25, 28)): True, (BUSH, (26, 28)): True, (BUSH, (25, 29)): True}
	return okA, okC


def r26():
	move(East)
	move(East)
	move(East)
	move(North)
	move(North)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	early((9, 4))
	move(East)
	early((8, 4))
	move(South)
	plant(BUSH)
	move(North)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(East)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	okA = {(BUSH, (9, 1)): True, (BUSH, (8, 2)): True, (BUSH, (9, 2)): True, (BUSH, (10, 2)): True, (BUSH, (7, 3)): True, (BUSH, (8, 3)): True, (BUSH, (9, 3)): True, (BUSH, (10, 3)): True, (BUSH, (11, 3)): True, (BUSH, (6, 4)): True, (BUSH, (7, 4)): True, (BUSH, (10, 4)): True, (BUSH, (11, 4)): True, (BUSH, (12, 4)): True, (BUSH, (7, 5)): True, (BUSH, (8, 5)): True, (BUSH, (9, 5)): True, (BUSH, (10, 5)): True, (BUSH, (11, 5)): True, (BUSH, (8, 6)): True, (BUSH, (9, 6)): True, (BUSH, (10, 6)): True, (BUSH, (9, 7)): True}
	okC = {(BUSH, (8, 1)): True, (BUSH, (7, 2)): True, (BUSH, (8, 2)): True, (BUSH, (9, 2)): True, (BUSH, (6, 3)): True, (BUSH, (7, 3)): True, (BUSH, (8, 3)): True, (BUSH, (9, 3)): True, (BUSH, (10, 3)): True, (BUSH, (5, 4)): True, (BUSH, (6, 4)): True, (BUSH, (7, 4)): True, (BUSH, (10, 4)): True, (BUSH, (11, 4)): True, (BUSH, (6, 5)): True, (BUSH, (7, 5)): True, (BUSH, (8, 5)): True, (BUSH, (9, 5)): True, (BUSH, (10, 5)): True, (BUSH, (7, 6)): True, (BUSH, (8, 6)): True, (BUSH, (9, 6)): True, (BUSH, (8, 7)): True}
	return okA, okC


def r27():
	move(East)
	move(East)
	move(East)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	move(South)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	early((9, 28))
	move(East)
	early((8, 28))
	move(North)
	plant(BUSH)
	move(East)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(West)
	move(North)
	okA = {(BUSH, (8, 25)): True, (BUSH, (7, 26)): True, (BUSH, (8, 26)): True, (BUSH, (9, 26)): True, (BUSH, (6, 27)): True, (BUSH, (7, 27)): True, (BUSH, (8, 27)): True, (BUSH, (9, 27)): True, (BUSH, (10, 27)): True, (BUSH, (5, 28)): True, (BUSH, (6, 28)): True, (BUSH, (7, 28)): True, (BUSH, (10, 28)): True, (BUSH, (11, 28)): True, (BUSH, (6, 29)): True, (BUSH, (7, 29)): True, (BUSH, (8, 29)): True, (BUSH, (9, 29)): True, (BUSH, (10, 29)): True, (BUSH, (7, 30)): True, (BUSH, (8, 30)): True, (BUSH, (9, 30)): True, (BUSH, (8, 31)): True}
	okC = {(BUSH, (9, 25)): True, (BUSH, (8, 26)): True, (BUSH, (9, 26)): True, (BUSH, (10, 26)): True, (BUSH, (7, 27)): True, (BUSH, (8, 27)): True, (BUSH, (9, 27)): True, (BUSH, (10, 27)): True, (BUSH, (11, 27)): True, (BUSH, (6, 28)): True, (BUSH, (7, 28)): True, (BUSH, (10, 28)): True, (BUSH, (11, 28)): True, (BUSH, (12, 28)): True, (BUSH, (7, 29)): True, (BUSH, (8, 29)): True, (BUSH, (9, 29)): True, (BUSH, (10, 29)): True, (BUSH, (11, 29)): True, (BUSH, (8, 30)): True, (BUSH, (9, 30)): True, (BUSH, (10, 30)): True, (BUSH, (9, 31)): True}
	return okA, okC


def r28():
	move(West)
	move(West)
	move(West)
	move(West)
	move(West)
	move(West)
	move(West)
	move(West)
	move(North)
	move(North)
	move(North)
	move(North)
	plant(BUSH)
	move(West)
	early((22, 4))
	move(West)
	early((23, 4))
	move(East)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(South)
	move(South)
	plant(BUSH)
	move(West)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	move(East)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	okA = {(BUSH, (22, 1)): True, (BUSH, (21, 2)): True, (BUSH, (22, 2)): True, (BUSH, (23, 2)): True, (BUSH, (20, 3)): True, (BUSH, (21, 3)): True, (BUSH, (22, 3)): True, (BUSH, (23, 3)): True, (BUSH, (24, 3)): True, (BUSH, (19, 4)): True, (BUSH, (20, 4)): True, (BUSH, (21, 4)): True, (BUSH, (24, 4)): True, (BUSH, (25, 4)): True, (BUSH, (20, 5)): True, (BUSH, (21, 5)): True, (BUSH, (22, 5)): True, (BUSH, (23, 5)): True, (BUSH, (24, 5)): True, (BUSH, (21, 6)): True, (BUSH, (22, 6)): True, (BUSH, (23, 6)): True, (BUSH, (22, 7)): True}
	okC = {(BUSH, (23, 1)): True, (BUSH, (22, 2)): True, (BUSH, (23, 2)): True, (BUSH, (24, 2)): True, (BUSH, (21, 3)): True, (BUSH, (22, 3)): True, (BUSH, (23, 3)): True, (BUSH, (24, 3)): True, (BUSH, (25, 3)): True, (BUSH, (20, 4)): True, (BUSH, (21, 4)): True, (BUSH, (24, 4)): True, (BUSH, (25, 4)): True, (BUSH, (26, 4)): True, (BUSH, (21, 5)): True, (BUSH, (22, 5)): True, (BUSH, (23, 5)): True, (BUSH, (24, 5)): True, (BUSH, (25, 5)): True, (BUSH, (22, 6)): True, (BUSH, (23, 6)): True, (BUSH, (24, 6)): True, (BUSH, (23, 7)): True}
	return okA, okC


def r29():
	move(West)
	move(West)
	move(West)
	move(West)
	move(West)
	move(West)
	move(West)
	move(West)
	move(West)
	move(South)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	early((22, 28))
	move(West)
	early((23, 28))
	move(North)
	plant(BUSH)
	move(West)
	move(West)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(East)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	move(South)
	plant(BUSH)
	move(West)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	move(North)
	plant(BUSH)
	move(East)
	move(North)
	plant(BUSH)
	move(West)
	okA = {(BUSH, (23, 25)): True, (BUSH, (22, 26)): True, (BUSH, (23, 26)): True, (BUSH, (24, 26)): True, (BUSH, (21, 27)): True, (BUSH, (22, 27)): True, (BUSH, (23, 27)): True, (BUSH, (24, 27)): True, (BUSH, (25, 27)): True, (BUSH, (20, 28)): True, (BUSH, (21, 28)): True, (BUSH, (24, 28)): True, (BUSH, (25, 28)): True, (BUSH, (26, 28)): True, (BUSH, (21, 29)): True, (BUSH, (22, 29)): True, (BUSH, (23, 29)): True, (BUSH, (24, 29)): True, (BUSH, (25, 29)): True, (BUSH, (22, 30)): True, (BUSH, (23, 30)): True, (BUSH, (24, 30)): True, (BUSH, (23, 31)): True}
	okC = {(BUSH, (22, 25)): True, (BUSH, (21, 26)): True, (BUSH, (22, 26)): True, (BUSH, (23, 26)): True, (BUSH, (20, 27)): True, (BUSH, (21, 27)): True, (BUSH, (22, 27)): True, (BUSH, (23, 27)): True, (BUSH, (24, 27)): True, (BUSH, (19, 28)): True, (BUSH, (20, 28)): True, (BUSH, (21, 28)): True, (BUSH, (24, 28)): True, (BUSH, (25, 28)): True, (BUSH, (20, 29)): True, (BUSH, (21, 29)): True, (BUSH, (22, 29)): True, (BUSH, (23, 29)): True, (BUSH, (24, 29)): True, (BUSH, (21, 30)): True, (BUSH, (22, 30)): True, (BUSH, (23, 30)): True, (BUSH, (22, 31)): True}
	return okA, okC


def r30():
	move(East)
	move(East)
	move(East)
	move(East)
	move(East)
	move(East)
	move(East)
	move(North)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	move(East)
	plant(BUSH)
	move(East)
	move(North)
	plant(BUSH)
	move(East)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	move(West)
	plant(BUSH)
	move(South)
	early((11, 2))
	move(West)
	early((12, 2))
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(East)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	okA = {(BUSH, (12, 31)): True, (BUSH, (11, 0)): True, (BUSH, (12, 0)): True, (BUSH, (13, 0)): True, (BUSH, (10, 1)): True, (BUSH, (11, 1)): True, (BUSH, (12, 1)): True, (BUSH, (13, 1)): True, (BUSH, (14, 1)): True, (BUSH, (9, 2)): True, (BUSH, (10, 2)): True, (BUSH, (13, 2)): True, (BUSH, (14, 2)): True, (BUSH, (15, 2)): True, (BUSH, (10, 3)): True, (BUSH, (11, 3)): True, (BUSH, (12, 3)): True, (BUSH, (13, 3)): True, (BUSH, (14, 3)): True, (BUSH, (11, 4)): True, (BUSH, (12, 4)): True, (BUSH, (13, 4)): True, (BUSH, (12, 5)): True}
	okC = {(BUSH, (11, 31)): True, (BUSH, (10, 0)): True, (BUSH, (11, 0)): True, (BUSH, (12, 0)): True, (BUSH, (9, 1)): True, (BUSH, (10, 1)): True, (BUSH, (11, 1)): True, (BUSH, (12, 1)): True, (BUSH, (13, 1)): True, (BUSH, (8, 2)): True, (BUSH, (9, 2)): True, (BUSH, (10, 2)): True, (BUSH, (13, 2)): True, (BUSH, (14, 2)): True, (BUSH, (9, 3)): True, (BUSH, (10, 3)): True, (BUSH, (11, 3)): True, (BUSH, (12, 3)): True, (BUSH, (13, 3)): True, (BUSH, (10, 4)): True, (BUSH, (11, 4)): True, (BUSH, (12, 4)): True, (BUSH, (11, 5)): True}
	return okA, okC


def r31():
	move(East)
	move(East)
	move(East)
	move(East)
	move(East)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(East)
	move(East)
	move(East)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	early((12, 30))
	move(East)
	early((11, 30))
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(East)
	move(South)
	plant(BUSH)
	move(West)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(North)
	plant(BUSH)
	move(West)
	move(West)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(East)
	plant(BUSH)
	move(South)
	okA = {(BUSH, (11, 27)): True, (BUSH, (10, 28)): True, (BUSH, (11, 28)): True, (BUSH, (12, 28)): True, (BUSH, (9, 29)): True, (BUSH, (10, 29)): True, (BUSH, (11, 29)): True, (BUSH, (12, 29)): True, (BUSH, (13, 29)): True, (BUSH, (8, 30)): True, (BUSH, (9, 30)): True, (BUSH, (10, 30)): True, (BUSH, (13, 30)): True, (BUSH, (14, 30)): True, (BUSH, (9, 31)): True, (BUSH, (10, 31)): True, (BUSH, (11, 31)): True, (BUSH, (12, 31)): True, (BUSH, (13, 31)): True, (BUSH, (10, 0)): True, (BUSH, (11, 0)): True, (BUSH, (12, 0)): True, (BUSH, (11, 1)): True}
	okC = {(BUSH, (12, 27)): True, (BUSH, (11, 28)): True, (BUSH, (12, 28)): True, (BUSH, (13, 28)): True, (BUSH, (10, 29)): True, (BUSH, (11, 29)): True, (BUSH, (12, 29)): True, (BUSH, (13, 29)): True, (BUSH, (14, 29)): True, (BUSH, (9, 30)): True, (BUSH, (10, 30)): True, (BUSH, (13, 30)): True, (BUSH, (14, 30)): True, (BUSH, (15, 30)): True, (BUSH, (10, 31)): True, (BUSH, (11, 31)): True, (BUSH, (12, 31)): True, (BUSH, (13, 31)): True, (BUSH, (14, 31)): True, (BUSH, (11, 0)): True, (BUSH, (12, 0)): True, (BUSH, (13, 0)): True, (BUSH, (12, 1)): True}
	return okA, okC


ROUTES = [r0, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14, r15, r16, r17, r18, r19, r20, r21, r22, r23, r24, r25, r26, r27, r28, r29, r30, r31]
# (d1, d2): d2 va da A a C, d1 da C ad A
DIRS = [
	(East, West),
	(East, West),
	(East, West),
	(East, West),
	(West, East),
	(East, West),
	(East, West),
	(East, West),
	(East, West),
	(East, West),
	(East, West),
	(East, West),
	(East, West),
	(East, West),
	(East, West),
	(West, East),
	(East, West),
	(West, East),
	(East, West),
	(West, East),
	(West, East),
	(East, West),
	(East, West),
	(West, East),
	(West, East),
	(East, West),
	(East, West),
	(West, East),
	(West, East),
	(East, West),
	(East, West),
	(West, East)
]

def first(okA, okC, d1, d2):
	# rientro su A: l'erba e' ricresciuta a secco durante la piantagione
	while not can_harvest():
		if get_water() < W0:
			use_item(WATER)
	harvest()
	while get_companion() not in okA:
		harvest()
	use_item(WATER)
	move(d2)
	while not can_harvest():
		if get_water() < W0:
			use_item(WATER)
	harvest()
	while get_companion() not in okC:
		harvest()
	use_item(WATER)
	move(d1)


def warmup(okA, okC, d1, d2):
	for _ in range(EARLY - 1):
		while not can_harvest():
			if get_water() < W0:
				use_item(WATER)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		while not can_harvest():
			if get_water() < W0:
				use_item(WATER)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
	while num_items(WATER) <= THR:
		while not can_harvest():
			if get_water() < W:
				use_item(WATER)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		while not can_harvest():
			if get_water() < W:
				use_item(WATER)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
	# primo ciclo a regime: acqua fino a WR e un'ultima attesa di sicurezza
	if get_water() < WR:
		use_item(WATER, 2)
	while not can_harvest():
		pass
	harvest()
	while get_companion() not in okA:
		harvest()
	move(d2)
	if get_water() < WR:
		use_item(WATER, 2)
	while not can_harvest():
		pass
	harvest()
	while get_companion() not in okC:
		harvest()
	move(d1)


def farm(okA, okC, d1, d2):
	while True:
		if get_water() < WR:
			use_item(WATER, 2)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		if get_water() < WR:
			use_item(WATER, 2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)


def farm_main(okA, okC, d1, d2):
	while num_items(HAY) < NEAR:
		if get_water() < WR:
			use_item(WATER, 2)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		if get_water() < WR:
			use_item(WATER, 2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
		harvest()
		while get_companion() not in okA:
			harvest()
		move(d2)
		harvest()
		while get_companion() not in okC:
			harvest()
		move(d1)
	while True:
		harvest()
		if num_items(HAY) >= GOAL:
			return
		while get_companion() not in okA:
			harvest()
			if num_items(HAY) >= GOAL:
				return
		move(d2)
		if num_items(HAY) >= GOAL:
			return
		harvest()
		if num_items(HAY) >= GOAL:
			return
		while get_companion() not in okC:
			harvest()
			if num_items(HAY) >= GOAL:
				return
		move(d1)
		if num_items(HAY) >= GOAL:
			return


def run_range(lo, hi):
	while hi - lo > 1:
		mid = (lo + hi) // 2
		spawn_drone(run_range, mid, hi)
		hi = mid
	okA, okC = ROUTES[lo]()
	d1, d2 = DIRS[lo]
	first(okA, okC, d1, d2)
	warmup(okA, okC, d1, d2)
	if lo == 0:
		farm_main(okA, okC, d1, d2)
		clear()
	else:
		farm(okA, okC, d1, d2)


run_range(0, BLOCKS)
