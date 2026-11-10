# === IN-GAME SCRIPT ===  (code window da chiamare "hay_probe")
# Scopo: campionare la sequenza esatta dei companion del flusso poly su UN drone,
#        per validare il co-simulatore offline contro un seed noto.
#
# Come lanciarlo (dalla fattoria normale, singolo drone):
#   simulate("hay_probe", Unlocks, {}, {}, 746272860, 1)
# (seed esplicito = ricrea il mondo dell'indice 15 in modo ripetibile)
#
# Copia TUTTO l'output console qui, poi offline:
#   python3 match_poly.py 746272860 output.txt        # validazione (tuo tool)
#   python3 hay_pred/predict_poly.py 746272860         # predizione pura da confrontare
#
# NON fa spawn_drone: così l'unico consumatore di poly dopo lo startup e' questo drone
# e la sequenza e' deterministica.

N = 25

S = get_world_size()
quick_print("pos", get_pos_x(), get_pos_y(), "S", S)

# Il campo e' gia' tutto erba (ClearGrid di startup). Leggo il companion corrente,
# poi harvest (rimuove+ricresce erba => nuovo companion), e ripeto.
for i in range(N):
	quick_print("c", get_companion())
	harvest()
