N = 2000000000
W = 0.7
RESERVE = 16
WARM = 24        # iterazioni iniziali con annaffiatura attiva
FAST_END = True  # il drone principale chiude la run con clear()

S = get_world_size()
BUSH = Entities.Bush
HAY = Items.Hay
WATER = Items.Water
BLOCKS = 32


def goto(tx, ty):
    dx = (tx - get_pos_x()) % S
    if dx <= S // 2:
        for _ in range(dx):
            move(East)
    else:
        for _ in range(S - dx):
            move(West)
    dy = (ty - get_pos_y()) % S
    if dy <= S // 2:
        for _ in range(dy):
            move(North)
    else:
        for _ in range(S - dy):
            move(South)


def work_block(b):
    i = b % 8
    bx = 4 * i
    by = (8 * (b // 8) + 4 * (i % 2)) % S

    # serpentina dall'alto verso il basso: 30 bush, finisce sull'erba est
    goto(bx, by + 7)
    for k in range(7):
        if k % 2 == 0:
            d = East
        else:
            d = West
        for _ in range(3):
            plant(BUSH)
            move(d)
        plant(BUSH)
        move(South)
    plant(BUSH)
    move(West)
    plant(BUSH)
    move(West)

    west = (bx, by)
    east = (bx + 1, by)
    # siamo sull'erba est: entrambi i cicli partono da qui

    # avvio: l'acqua e' scarsa (1 unita' ogni ~237 tick per tutta la fattoria).
    # Una sola unita' per visita, cosi' si distribuisce su tutte le celle
    # invece di saturare le prime: la prima unita' vale molto piu' della terza.
    for _ in range(WARM):
        if get_water() < W and num_items(WATER) > RESERVE:
            use_item(WATER)
        while not can_harvest():
            pass
        harvest()
        while True:
            while get_companion()[0] != BUSH:
                harvest()
            if get_companion()[1] != west:
                break
            harvest()
        move(West)

        if get_water() < W and num_items(WATER) > RESERVE:
            use_item(WATER)
        while not can_harvest():
            pass
        harvest()
        while True:
            while get_companion()[0] != BUSH:
                harvest()
            if get_companion()[1] != east:
                break
            harvest()
        move(East)

    # regime: con FAST_END solo il drone principale controlla il fieno
    forever = FAST_END and b != 0
    while forever or num_items(HAY) < N:
        while not can_harvest():
            if get_water() < W and num_items(WATER) > RESERVE:
                use_item(WATER)
        harvest()
        while True:
            while get_companion()[0] != BUSH:
                harvest()
            if get_companion()[1] != west:
                break
            harvest()
        move(West)

        while not can_harvest():
            if get_water() < W and num_items(WATER) > RESERVE:
                use_item(WATER)
        harvest()
        while True:
            while get_companion()[0] != BUSH:
                harvest()
            if get_companion()[1] != east:
                break
            harvest()
        move(East)

    if FAST_END:
        # la run finisce solo quando tutti i droni hanno terminato:
        # clear() rimuove gli altri subito invece di aspettare che se ne accorgano
        clear()


def make_task(lo, hi):
    def fn():
        run_range(lo, hi)
    return fn


def run_range(lo, hi):
    while hi - lo > 1:
        mid = (lo + hi) // 2
        spawn_drone(make_task(mid, hi))
        hi = mid
    work_block(lo)


run_range(0, BLOCKS)
