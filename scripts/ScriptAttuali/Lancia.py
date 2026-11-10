# LANCIATORE: scegli la classifica e premi play su questo file.
# Ogni voce = (classifica, nome del file di gioco con la soluzione)

SCELTA = "reset"
SPEEDUP = 1000000

CLASSIFICHE = {
	"hay": (Leaderboards.Hay, "f0"),
	"wood": (Leaderboards.Wood, "lb_wood"),
	"carrots": (Leaderboards.Carrots, "lb_carrots"),
	"cactus": (Leaderboards.Cactus, "lb_cactus_v3"),
	"pumpkins": (Leaderboards.Pumpkins, "zucca"),
	"sunflowers": (Leaderboards.Sunflowers, "sunv3"),
	"dinosaur": (Leaderboards.Dinosaur, "lb_dinosaur"),
	"maze": (Leaderboards.Maze, "f1"),
	"reset": (Leaderboards.Fastest_Reset, "lb_reset"),
}

board, filename = CLASSIFICHE[SCELTA]
leaderboard_run(board, filename, SPEEDUP)
