# LANCIATORE: scegli la classifica e premi play su questo file.
# Ogni voce = (classifica, nome del file di gioco con la soluzione)

SCELTA = "hay"
SPEEDUP = 1000000

CLASSIFICHE = {
	"hay": (Leaderboards.Hay, "lb_hay"),
	"wood": (Leaderboards.Wood, "lb_wood"),
	"carrots": (Leaderboards.Carrots, "lb_carrots"),
	"cactus": (Leaderboards.Cactus, "lb_cactus"),
	"pumpkins": (Leaderboards.Pumpkins, "lb_pumpkins"),
	"sunflowers": (Leaderboards.Sunflowers, "lb_sunflowers"),
	"dinosaur": (Leaderboards.Dinosaur, "lb_dinosaur"),
	"maze": (Leaderboards.Maze, "lb_maze"),
}

board, filename = CLASSIFICHE[SCELTA]
leaderboard_run(board, filename, SPEEDUP)
