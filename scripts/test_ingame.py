# Test in gioco: lancia con simulate(...) o direttamente nel drone principale.
# Ogni blocco stampa "atteso -> misurato". get_tick_count/quick_print costano 0.
# Imposta quale test eseguire:
TEST = "costi"   # "costi" | "cactus" | "dino" | "maze"

def tick():
    return get_tick_count()

# ---------------------------------------------------------------- costi interprete
def test_costi():
    quick_print("--- costi interprete (atteso -> misurato)")
    a = 5
    b = [1, 2, 3]
    d = {1: 1}
    t0 = tick(); x = a + 1;          quick_print("a+1 (op)        1 ->", tick() - t0)
    t0 = tick(); x = a;              quick_print("x = a            0 ->", tick() - t0)
    t0 = tick(); x += 1;             quick_print("x += 1           1 ->", tick() - t0)
    t0 = tick(); x = b[1];           quick_print("b[1] (indice)    0 ->", tick() - t0)
    t0 = tick(); x = not a;          quick_print("not a            0 ->", tick() - t0)
    t0 = tick(); x = a < 3;          quick_print("a < 3            1 ->", tick() - t0)
    t0 = tick(); x = (a, a) == (1, 1); quick_print("tupla==tupla   2+2 ->", tick() - t0)
    t0 = tick(); x = (1, 2);         quick_print("tupla letterale  1 ->", tick() - t0)
    t0 = tick(); x = [1, 2, 3, 4];   quick_print("lista 4 elem     4 ->", tick() - t0)
    t0 = tick(); x = 2 in b;         quick_print("2 in lista(3)  <=3 ->", tick() - t0)
    t0 = tick(); x = 1 in d;         quick_print("1 in dict        1 ->", tick() - t0)
    t0 = tick()
    if a: pass
    quick_print("if a             1 ->", tick() - t0)
    t0 = tick()
    for _ in range(10): pass
    quick_print("for 10 iter   ~10-11 ->", tick() - t0)
    t0 = tick()
    i = 0
    while i < 10: i += 1
    quick_print("while 10 (test+ +=) ~21 ->", tick() - t0)
    t0 = tick(); x = tick();         quick_print("chiamata propria 1 ->", tick() - t0)
    t0 = tick(); x = len(b);         quick_print("len              1 ->", tick() - t0)
    t0 = tick(); x = get_pos_x();    quick_print("get_pos_x        1 ->", tick() - t0)
    t0 = tick(); x = can_harvest();  quick_print("can_harvest      1 ->", tick() - t0)
    t0 = tick(); x = get_time();     quick_print("get_time         0 ->", tick() - t0)
    t0 = tick(); move(North);        quick_print("move ok        200 ->", tick() - t0)
    t0 = tick(); x = measure();      quick_print("measure          1 ->", tick() - t0)

# ---------------------------------------------------------------- cactus
def test_cactus():
    quick_print("--- cactus")
    clear()
    while get_ground_type() != Grounds.Soil: till()
    plant(Entities.Cactus)
    s0 = measure()
    quick_print("size su seedling (0-9):", s0)
    t0 = tick(); h = harvest(); quick_print("harvest seedling: 200 ->", tick() - t0, "ritorno", h, "entita' ancora li'?", get_entity_type())
    quick_print("size dopo harvest fallito (uguale):", measure())
    # swap scambia i numeri
    move(East)
    while get_ground_type() != Grounds.Soil: till()
    plant(Entities.Cactus)
    s1 = measure()
    t0 = tick(); swap(West); dt = tick() - t0
    quick_print("swap: 200 ->", dt, " qui ora", measure(), "(atteso", s0, ") ovest", end="")
    move(West); quick_print(measure(), "(atteso", s1, ")")
    # till rimuove l'entita'
    till(); quick_print("dopo till entita' =", get_entity_type(), "(atteso None)")
    # vicino immaturo blocca il taglio: 0,0 maturo e vicino E seedling, raccogli 0,0 e conta
    clear()
    while get_ground_type() != Grounds.Soil: till()
    plant(Entities.Cactus)
    while not can_harvest(): pass
    move(East)
    while get_ground_type() != Grounds.Soil: till()
    plant(Entities.Cactus)      # seedling, immaturo
    move(West)
    n0 = num_items(Items.Cactus)
    harvest()
    quick_print("raccolto con vicino immaturo (atteso solo il proprio, k^2*32 con k=", "?", "):", num_items(Items.Cactus) - n0)
    move(East); quick_print("vicino E ancora presente? (atteso Cactus):", get_entity_type())

# ---------------------------------------------------------------- dinosauro
def test_dino():
    quick_print("--- dinosauro")
    clear()
    change_hat(Hats.Dinosaur_Hat)
    t0 = tick(); move(North); quick_print("1o move: 400 ->", tick() - t0)
    nxt = measure()
    quick_print("measure = prossima mela:", nxt)
    # vai verso la mela e misura il costo del move dopo averla presa
    eaten = 0
    cost = 400
    for step in range(60):
        tx, ty = measure()
        x, y = get_pos_x(), get_pos_y()
        d = North
        if tx != x:
            if (tx - x) % get_world_size() <= get_world_size() // 2: d = East
            else: d = West
        elif (ty - y) % get_world_size() > get_world_size() // 2: d = South
        t0 = tick(); move(d); dt = tick() - t0
        if measure() != (tx, ty):
            eaten += 1
            nc = cost - cost * 3 // 100
            quick_print("mela", eaten, "mangiata: move da ora atteso", nc)
            cost = nc
        elif dt != cost:
            quick_print("ANOMALIA: move costo", dt, "atteso", cost)
    quick_print("mele", eaten, "costo move finale", cost)
    change_hat(Hats.Straw_Hat)

# ---------------------------------------------------------------- labirinto
def test_maze():
    quick_print("--- labirinto")
    clear()
    while get_ground_type() != Grounds.Soil: till()
    plant(Entities.Bush)
    g0 = num_items(Items.Gold)
    use_item(Items.Weird_Substance, get_world_size())
    quick_print("sostanza usata; raggiungi il tesoro (random walk: sostituisci con il tuo solver)")
    # trova il tesoro con misure semplici: cammina casualmente finche' get_entity_type()==Treasure
    seen = 0
    while get_entity_type() != Entities.Treasure and seen < 20000:
        d = [North, East, South, West][int(random() * 4)]
        move(d); seen += 1
    quick_print("tesoro trovato dopo", seen, "move")
    t0 = tick(); ok = use_item(Items.Weird_Substance, get_world_size()); quick_print("reuse (use_item): 200 ->", tick() - t0, "ok", ok, "oro +", num_items(Items.Gold) - g0, "(atteso 32768 con upgrade 16)")
    g1 = num_items(Items.Gold)
    t0 = tick(); ok2 = use_item(Items.Weird_Substance, get_world_size()); quick_print("2o use_item durante trasloco: fallisce, 200 ->", tick() - t0, "ok", ok2)
    t0 = tick(); h = harvest(); quick_print("harvest durante trasloco: 200 ->", tick() - t0, "ritorno", h, "oro +", num_items(Items.Gold) - g1, "(atteso 0)")
    quick_print("entita' qui ora:", get_entity_type(), "measure:", measure())

if TEST == "costi": test_costi()
if TEST == "cactus": test_cactus()
if TEST == "dino": test_dino()
if TEST == "maze": test_maze()
