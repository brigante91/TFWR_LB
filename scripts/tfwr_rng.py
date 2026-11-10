"""RNG predictor for The Farmer Was Replaced (Mono build, Core.dll / Utils.dll).

Reverse engineered from:
  Simulation::.ctor            -> master Random(seed) + 8 derived streams
  Helper::JustSha256It         -> how sub-seeds are derived
  ProgramState::.ctor          -> per-drone stream behind the in-game random()
  MainSim::LeaderboardExecutionFinished -> seed chaining between leaderboard runs
  mscorlib System.Random       -> Knuth subtractive generator (MBIG = 2^31-1)
"""
import hashlib

MBIG = 0x7FFFFFFF
MSEED = 161803398
INV_MBIG = 4.6566128752457969e-10  # literal used by Random::Sample

# Order in which Simulation::.ctor derives the streams from the master generator.
STREAMS = ("various", "maze", "snake", "cactus", "sunflower", "pumpkin", "poly", "random")
# Order in which LeaderboardExecutionFinished samples them to build the next seed.
CHAIN_ORDER = ("various", "sunflower", "snake", "random", "pumpkin", "poly", "maze", "cactus")


def _i32(v):
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v & 0x80000000 else v


class DotNetRandom:
    """Bit-exact port of System.Random(int Seed)."""

    def __init__(self, seed):
        sa = [0] * 56
        subtraction = MBIG if seed == -0x80000000 else abs(seed)
        mj = _i32(MSEED - subtraction)
        sa[55] = mj
        mk = 1
        ii = 0
        for _ in range(1, 55):
            ii += 21
            if ii >= 55:
                ii -= 55
            sa[ii] = mk
            mk = _i32(mj - mk)
            if mk < 0:
                mk = _i32(mk + MBIG)
            mj = sa[ii]
        for _ in range(1, 5):
            for i in range(1, 56):
                n = i + 30
                if n >= 55:
                    n -= 55
                sa[i] = _i32(sa[i] - sa[1 + n])
                if sa[i] < 0:
                    sa[i] = _i32(sa[i] + MBIG)
        self.sa = sa
        self.inext = 0
        self.inextp = 21

    @classmethod
    def from_outputs(cls, outputs):
        """Rebuild the generator state from the last 55 consecutive raw samples."""
        if len(outputs) < 55:
            raise ValueError("need 55 consecutive samples")
        r = cls.__new__(cls)
        # After 55 draws slot i holds the i-th of those draws, and the pointers
        # have wrapped back to their starting offsets (lag 55 / lag 34).
        r.sa = [0] + [int(v) for v in outputs[-55:]]
        r.inext = 0
        r.inextp = 21
        return r

    def sample(self):
        """InternalSample(): raw value in [0, MBIG)."""
        i = self.inext + 1
        if i >= 56:
            i = 1
        p = self.inextp + 1
        if p >= 56:
            p = 1
        v = _i32(self.sa[i] - self.sa[p])
        if v == MBIG:
            v -= 1
        if v < 0:
            v = _i32(v + MBIG)
        self.sa[i] = v
        self.inext = i
        self.inextp = p
        return v

    def next(self, a=None, b=None):
        """Next(), Next(max) or Next(min, max)."""
        if a is None:
            return self.sample()
        lo, hi = (0, a) if b is None else (a, b)
        rng = hi - lo
        if rng <= MBIG:
            return int(self.sample() * INV_MBIG * rng) + lo
        s = self.sample()
        if self.sample() % 2 == 0:
            s = -s
        return _i32(int((s + 2147483646.0) / 4294967293.0 * rng) + lo)

    def next_double(self):
        return self.sample() * INV_MBIG

    def next_bytes(self, n):
        return bytes(self.sample() & 0xFF for _ in range(n))


def just_sha256_it(rnd):
    """Utils Helper::JustSha256It: 16 bytes -> SHA-256 -> low 31 bits of first LE int32."""
    digest = hashlib.sha256(rnd.next_bytes(16)).digest()
    return int.from_bytes(digest[:4], "little") & MBIG


def derive_seeds(seed):
    """Sub-seeds of every stream for a Simulation created with a seed >= 0."""
    master = DotNetRandom(seed)
    return {name: just_sha256_it(master) for name in STREAMS}


class SimulationRng:
    """All the generators of one Simulation, as built by Simulation::.ctor."""

    def __init__(self, seed):
        self.seed = seed
        self.seeds = derive_seeds(seed)
        for name, s in self.seeds.items():
            setattr(self, name, DotNetRandom(s))

    def new_drone(self):
        """ProgramState::.ctor: the stream read by random() for a newly started drone."""
        return DotNetRandom(self.random.next())

    def next_leaderboard_seed(self):
        """Seed of the following run in a multi-run leaderboard (consumes one sample each)."""
        total = 0
        for name in CHAIN_ORDER:
            total = _i32(total + getattr(self, name).next())
        return abs(total)


# --- companions (polyculture) -------------------------------------------------

COMPANION_RADIUS = 3
COMPANION_TYPES = ("grass", "bush", "carrot", "tree")  # index = Next(4)
# Helper::WorldSizeScale, indexed by the number of "expand" unlocks.
WORLD_SCALES = (1, 2, 3, 4, 6, 8, 12, 16, 22, 32)


def world_size(expand_level, size_limit=0):
    """GridManager::get_WorldSize as (width, height)."""
    scale = WORLD_SCALES[min(expand_level, len(WORLD_SCALES) - 1)]
    if 0 < size_limit < scale:
        return (size_limit, size_limit)
    return (1, 3) if scale == 2 else (scale, scale)


def _rem(a, b):
    """C# % operator (truncates toward zero)."""
    return a - b * int(a / b)


def _wrap(x, y, world):
    return (_rem(x + world[0], world[0]), _rem(y + world[1], world[1]))


def choose_companion(poly, pos, plant, world):
    """Growable::ChooseCompanion. Returns (type, (x, y)) with an absolute position."""
    r = COMPANION_RADIUS
    while True:
        dx = poly.next(-r, r + 1)
        dy = poly.next(-r, r + 1)
        if _wrap(pos[0] + dx, pos[1] + dy, world) != pos and abs(dx) + abs(dy) <= r:
            break
        if world[1] == 1:  # one-row worlds accept whatever was rolled
            break
    target = _wrap(pos[0] + dx, pos[1] + dy, world)
    while True:
        kind = COMPANION_TYPES[poly.next(4)]
        if kind != plant:
            return kind, target


def clear_grid(poly, world):
    """GridManager::ClearGrid(true): fresh grass on every cell, x outer / y inner."""
    return {
        (x, y): choose_companion(poly, (x, y), "grass", world)
        for x in range(world[0])
        for y in range(world[1])
    }


def startup_grid(poly, sizes):
    """Replay the world regenerations done while the Farm is being constructed.

    The grid is first built with no unlocks (1x1) and regenerated every time an
    "expand" unlock changes the size, so `sizes` is the list of sizes it went
    through. Returns the companions of the final grid.
    """
    grid = {}
    for world in sizes:
        grid = clear_grid(poly, world)
    return grid


def calibrate_startup(seed, final_world, observed):
    """Find which startup size sequences reproduce companions observed in game.

    `observed` maps (x, y) -> (type, (cx, cy)) as read with get_companion() right
    at the start of a simulate() run with a known seed, before any harvest/plant.
    Tries every ascending subset of the possible intermediate sizes.
    """
    area = final_world[0] * final_world[1]
    steps = [w for w in (world_size(i) for i in range(len(WORLD_SCALES))) if w[0] * w[1] < area]
    matches = []
    for mask in range(1 << len(steps)):
        sizes = [w for i, w in enumerate(steps) if mask >> i & 1] + [final_world]
        grid = startup_grid(DotNetRandom(derive_seeds(seed)["poly"]), sizes)
        if all(grid.get(pos) == val for pos, val in observed.items()):
            matches.append(sizes)
    return matches


def parse_companion_dump(text):
    """Parse lines holding `x y <type> cx cy` (any separators) into an observed dict."""
    import re

    observed = {}
    for line in text.splitlines():
        kind = re.search(r"grass|bush|carrot|tree", line.lower())
        nums = [int(n) for n in re.findall(r"-?\d+", line)]
        if kind and len(nums) >= 4:
            observed[(nums[0], nums[1])] = (kind.group(), (nums[-2], nums[-1]))
    return observed


def raw_from_random(value):
    """Turn an in-game random() result back into the raw integer sample."""
    return round(value * MBIG)


def predict_random(observed, count=10):
    """Given >= 55 consecutive in-game random() values, predict the next `count`."""
    rnd = DotNetRandom.from_outputs([raw_from_random(v) for v in observed])
    return [rnd.next_double() for _ in range(count)]


if __name__ == "__main__":
    import sys

    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    sim = SimulationRng(seed)
    print(f"seed {seed}")
    for name in STREAMS:
        print(f"  {name:<10} seed={sim.seeds[name]}")
    drone = sim.new_drone()
    print("  drone 0 random():", [drone.next_double() for _ in range(5)])
