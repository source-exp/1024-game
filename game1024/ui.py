"""Terminal user interface for 1024."""

import os
import sys

from .engine import Game

try:
    import termios
    import tty
except ImportError:  # pragma: no cover
    termios = None
    tty = None

TILE_WIDTH = 9

RESET = "\033[0m"
BOLD = "\033[1m"
YELLOW = "\033[33m"

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


_ESCAPE_KEYS = {
    "\x1b[A": "up",
    "\x1b[B": "down",
    "\x1b[C": "right",
    "\x1b[D": "left",
}


def _read_key(fd):
    char = os.read(fd, 1).decode("utf-8", "ignore")
    if char == "\x1b":
        sequence = char + os.read(fd, 1).decode("utf-8", "ignore")
        return _ESCAPE_KEYS.get(sequence, "escape")
    return char.lower()

def _tile(value):
    if not value:
        return " " * TILE_WIDTH
    background = STYLES.get(value, 201)
    return f"\033[48;5;{background}m{value:^{TILE_WIDTH}}{RESET}"


def render(game):
    lines = [
        f"\033[1m\033[33m{game.target}   SCORE {game.score}   BEST {game.best}{RESET}",
        "",
    ]
    for row in game.grid:
        lines.append(" ".join(_tile(value) for value in row))
    return "\n".join(lines)


def run(game=None):
    game = game if game is not None else Game()
    print(render(game))
