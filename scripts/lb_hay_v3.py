# Togli il '#' alle 2 righe sotto quando lanci leaderboard_run!
GOAL = 2000000000
W = 0.72

BUSH = Entities.Bush
WATER = Items.Water
HAY = Items.Hay
BLOCKS = 32

# Mappa pre-calcolata: elimina block_origin(b) e assegna i blocchi piu' lontani
# ai rami con meno overhead di spawn (0 bit a 1 -> 5 bit a 1)
BLOCKS_POS = (
    (12, 12), # b=0  (0 salti, 25 passi)
    (8, 8),   # b=1  (1 salto, 17 passi)
    (4, 12),  # b=2  (1 salto, 17 passi)
    (24, 16), # b=3  (2 salti, 14 passi)
    (20, 12), # b=4  (1 salto, 22 passi)
    (24, 8),  # b=5  (2 salti, 14 passi)
    (20, 20), # b=6  (2 salti, 14 passi)
    (24, 0),  # b=7  (3 salti, 6 passi)
    (16, 16), # b=8  (1 salto, 22 passi)
    (20, 4),  # b=9  (2 salti, 14 passi)
    (16, 24), # b=10 (2 salti, 14 passi)
    (4, 28),  # b=11 (3 salti, 7 passi)
    (16, 0),  # b=12 (2 salti, 14 passi)
    (8, 24),  # b=13 (3 salti, 9 passi)
    (8, 0),   # b=14 (3 salti, 9 passi)
    (0, 0),   # b=15 (4 salti, 1 passo)
    (16, 8),  # b=16 (1 salto, 22 passi)
    (12, 28), # b=17 (2 salti, 15 passi)
    (12, 20), # b=18 (2 salti, 17 passi)
    (4, 20),  # b=19 (3 salti, 9 passi)
    (12, 4),  # b=20 (2 salti, 17 passi)
    (4, 4),   # b=21 (3 salti, 9 passi)
    (0, 16),  # b=22 (3 salti, 9 passi)
    (28, 28), # b=23 (4 salti, 4 passi)
    (8, 16),  # b=24 (2 salti, 17 passi)
    (0, 8),   # b=25 (3 salti, 9 passi)
    (20, 28), # b=26 (3 salti, 12 passi)
    (28, 20), # b=27 (4 salti, 6 passi)
    (28, 12), # b=28 (3 salti, 14 passi)
    (28, 4),  # b=29 (4 salti, 6 passi)
    (24, 24), # b=30 (4 salti, 6 passi)
    (0, 24),  # b=31 (5 salti, 1 passo)
)


def work_block(b, w, goal):
    bx, by = BLOCKS_POS[b]
    west = (bx, by)
    east = (bx + 1, by)

    if bx < 16:
        if by >= 12:
            # Quadrante 1 (Alto-Sinistra): entra da (bx, by + 7), finisce su east
            for _ in range(bx):
                move(East)
            ty = (by + 7) % 32
            if ty == 3:
                for _ in range(3):
                    move(North)
            else:
                for _ in range(32 - ty):
                    move(South)

            for d in (East, West, East, West, East, West, East):
                plant(BUSH)
                move(d)
                plant(BUSH)
                move(d)
                plant(BUSH)
                move(d)
                plant(BUSH)
                move(South)
            plant(BUSH)
            move(West)
            plant(BUSH)
            move(West)
        else:
            # Quadrante 3 (Basso-Sinistra): entra da (bx, by + 1), U-path, finisce su east
            for _ in range(bx):
                move(East)
            for _ in range(by + 1):
                move(North)

            for d in (East, West, East, West, East, West):
                plant(BUSH)
                move(d)
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
            for d in (West, East, West, East, West, East):
                plant(BUSH)
                move(d)
                plant(BUSH)
                move(South)
            plant(BUSH)
            move(West)
            plant(BUSH)
            move(West)

        a1, d1, a2, d2 = west, West, east, East
    else:
        if by >= 12:
            # Quadrante 2 (Alto-Destra): entra da (bx + 3, by + 7), finisce su west
            for _ in range(29 - bx):
                move(West)
            ty = (by + 7) % 32
            if ty == 3:
                for _ in range(3):
                    move(North)
            else:
                for _ in range(32 - ty):
                    move(South)

            for d in (West, East, West, East, West, East):
                plant(BUSH)
                move(d)
                plant(BUSH)
                move(d)
                plant(BUSH)
                move(d)
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
            move(West)
            plant(BUSH)
            move(South)
        else:
            # Quadrante 4 (Basso-Destra): entra da (bx + 2, by), U-path, finisce su west
            for _ in range(30 - bx):
                move(West)
            for _ in range(by):
                move(North)

            for d in (East, West, East, West, East, West, East):
                plant(BUSH)
                move(d)
                plant(BUSH)
                move(North)
            plant(BUSH)
            move(West)
            plant(BUSH)
            move(West)
            plant(BUSH)
            move(West)
            plant(BUSH)
            move(South)
            for d in (East, West, East, West, East):
                plant(BUSH)
                move(d)
                plant(BUSH)
                move(South)
            plant(BUSH)
            move(West)
            plant(BUSH)
            move(South)

        a1, d1, a2, d2 = east, East, west, West

    while num_items(HAY) < goal:
        if get_water() < w and num_items(WATER) > 16:
            if get_water() < 0.3 and num_items(WATER) >= 4:
                use_item(WATER, 4)
            else:
                use_item(WATER)
        while not can_harvest():
            pass
        harvest()
        c, pos = get_companion()
        while c != BUSH or pos == a1:
            harvest()
            c, pos = get_companion()
        move(d1)

        if get_water() < w and num_items(WATER) > 16:
            if get_water() < 0.3 and num_items(WATER) >= 4:
                use_item(WATER, 4)
            else:
                use_item(WATER)
        while not can_harvest():
            pass
        harvest()
        c, pos = get_companion()
        while c != BUSH or pos == a2:
            harvest()
            c, pos = get_companion()
        move(d2)


def make_task(lo, hi, w, goal):
    def fn():
        run_range(lo, hi, w, goal)
    return fn


def run_range(lo, hi, w, goal):
    while hi - lo > 1:
        mid = (lo + hi) // 2
        spawn_drone(make_task(mid, hi, w, goal))
        hi = mid
    work_block(lo, w, goal)


run_range(0, BLOCKS, W, GOAL)
