"""Terminal user interface for 1024."""

import os
import select
import shutil
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
    """Read a single key press from a raw/cbreak terminal."""
    try:
        data = os.read(fd, 1)
    except OSError:
        return "quit"

    if not data:
        return "quit"

    char = data.decode("utf-8", "ignore")

    if char == "\x1b":
        # Arrow keys arrive as a short escape sequence. Wait briefly for the
        # rest so a lone Escape does not block forever.
        sequence = char
        while len(sequence) < 3 and select.select([fd], [], [], 0.02)[0]:
            sequence += os.read(fd, 1).decode("utf-8", "ignore")
        return _ESCAPE_KEYS.get(sequence, "escape")

    if char == "\x03":  # Ctrl-C when ISIG is disabled
        return "quit"

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
    if game.score >= game.target:
        lines.append("")
        lines.append(
            f"You reached {game.target}! Keep going for a higher score."
        )

    return "\n".join(lines)


def _run_interactive(game, stdin, stdout):
    fd = stdin.fileno()
    saved_attributes = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    stdout.write("\033[?25l")
    stdout.flush()

    try:
        while True:
            terminal = shutil.get_terminal_size((80, 24))
            frame = render(game)
            top_margin = max((terminal.lines - frame.count("\n") - 1) // 2 - 1, 0)

            stdout.write("\033[2J\033[H")
            stdout.write("\n" * top_margin)
            stdout.write(frame + "\n")
            stdout.flush()

            key = _read_key(fd)

            if key in ("q", "quit"):
                return
            if key == "r":
                game.reset()
            elif key == "u":
                game.undo()
            elif key in game.DIRECTIONS:
                game.move(key)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved_attributes)
        stdout.write("\033[?25h" + RESET + "\n")
        stdout.flush()

def _is_tty(stream):
    try:
        return bool(stream.isatty())
    except (AttributeError, ValueError):
        return False


def _run_line_mode(game, stdin, stdout):
    color = _is_tty(stdout)
    stdout.write(render(game) + "\n")
    stdout.flush()

    for raw_line in stdin:
        command = raw_line.strip().lower()
        if not command:
            continue

        if command in ("q", "quit", "exit"):
            return

        if command in ("r", "restart"):
            game.reset()
        elif command in ("u", "undo"):
            if not game.undo():
                stdout.write("Nothing to undo.\n")
                stdout.flush()
                continue
        elif command in ("left", "a", "right", "d", "up", "w", "down", "s"):
            direction = {"a": "left", "d": "right", "w": "up", "s": "down"}.get(
                command, command
            )
            if not game.move(direction):
                stdout.write("That move does not change the board.\n")
                stdout.flush()
                continue
        else:
            stdout.write(f"Unknown command: {command}\n")
            stdout.flush()
            continue

        stdout.write(render(game) + "\n")
        stdout.flush()


def run(game=None, stdin=None, stdout=None):
    game = game if game is not None else Game()
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout

    if termios is not None and _is_tty(stdin) and _is_tty(stdout):
        _run_interactive(game, stdin, stdout)
    else:
        _run_line_mode(game, stdin, stdout)
