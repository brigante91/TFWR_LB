# === IN-GAME ===  code window "cactus_yf_test"
# Misura YieldFactor del cactus: un cactus ISOLATO e' "ordinato" -> pop da 1 ->
# resa = 1^2 * YieldFactor = YieldFactor esatto.
# Lancia CON SEMI:  simulate("cactus_yf_test", Unlocks, {Items.Cactus: 10}, {}, 1, 1)
# Riporta la riga YF (o plant_fallito).

CACTUS = Entities.Cactus

if get_entity_type() != None:
	harvest()
if get_ground_type() != Grounds.Soil:
	till()
if not plant(CACTUS):
	quick_print("plant_fallito_servono_semi")
else:
	while not can_harvest():
		pass
	before = num_items(Items.Cactus)
	harvest()
	quick_print("YF", num_items(Items.Cactus) - before)
