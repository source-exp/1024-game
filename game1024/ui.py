"""Terminal user interface for 1024."""

from .engine import Game

TILE_WIDTH = 5

STYLES = {
    0: 236,
    2: 252,
    4: 251,
    8: 215,
    16: 209,
    32: 203,
    64: 196,
    128: 220,
    256: 226,
    512: 227,
    1024: 228,
}


def _tile(value):
    if not value:
        return " " * TILE_WIDTH
    background = STYLES.get(value, 201)
    return f"\033[48;5;{background}m{value:^{TILE_WIDTH}}"


def render(game):
    lines = []
    for row in game.grid:
        lines.append(" ".join(_tile(value) for value in row))
    return "\n".join(lines)


def run(game=None):
    game = game if game is not None else Game()
    print(render(game))
