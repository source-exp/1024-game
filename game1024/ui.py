"""Terminal user interface for 1024.

The board is drawn with plain ANSI escape codes (no ``curses``), so it works
in the macOS Terminal and most other modern terminals.

When stdin and stdout are TTYs, the UI uses single-key input and redraws the
whole screen. When they are not (for example when input is piped), it falls
back to reading one command per line so the game can be scripted.
"""

from __future__ import annotations

import os
import re
import select
import shutil
import sys
from typing import Dict, Optional, TextIO

from .engine import Game

try:  # termios/tty are Unix-only; the line-based fallback still works without them.
    import termios
    import tty
except ImportError:  # pragma: no cover - exercised on Windows only
    termios = None  # type: ignore[assignment]
    tty = None  # type: ignore[assignment]


# ----------------------------------------------------------------------
# Appearance
# ----------------------------------------------------------------------
TILE_WIDTH = 9
TILE_HEIGHT = 3

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"

# 256-colour ANSI palette: value -> (background, foreground, highlighted).
# Values of 256 and above are drawn in bold to make progress obvious.
TILE_STYLES: Dict[int, tuple] = {
    0: (236, 250, False),
    2: (252, 235, False),
    4: (251, 235, False),
    8: (215, 231, False),
    16: (209, 231, False),
    32: (203, 231, False),
    64: (196, 231, False),
    128: (220, 235, False),
    256: (226, 16, True),
    512: (227, 16, True),
    1024: (228, 16, True),
    2048: (220, 16, True),
}
FALLBACK_TILE = (201, 231, True)

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

_ESCAPE_KEYS = {
    "\x1b[A": "up",
    "\x1b[B": "down",
    "\x1b[C": "right",
    "\x1b[D": "left",
    # Some terminals use "application cursor" mode.
    "\x1bOA": "up",
    "\x1bOB": "down",
    "\x1bOC": "right",
    "\x1bOD": "left",
}

_LINE_DIRECTIONS = {
    "left": "left",
    "a": "left",
    "right": "right",
    "d": "right",
    "up": "up",
    "w": "up",
    "down": "down",
    "s": "down",
}


# ----------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------
def _visible_width(text: str) -> int:
    """Length of ``text`` without ANSI colour codes."""
    return len(_ANSI_RE.sub("", text))


def _paint(text: str, codes: str, color: bool) -> str:
    return f"{codes}{text}{RESET}" if color else text


def _tile_line(value: int, line_index: int, color: bool) -> str:
    """Render one of the three text lines of a single tile."""
    if line_index == 1 and value:
        content = f"{value:^{TILE_WIDTH}}"
    else:
        content = " " * TILE_WIDTH

    if not color:
        return content

    background, foreground, highlighted = TILE_STYLES.get(value, FALLBACK_TILE)
    codes = f"\033[48;5;{background}m\033[38;5;{foreground}m"
    if highlighted:
        codes += BOLD
    return f"{codes}{content}{RESET}"


def render(game: Game, width: int = 0, color: bool = True) -> str:
    """Build the complete screen for ``game``.

    Args:
        game: Game to draw.
        width: If positive, centre every line within this many columns.
        color: Emit ANSI colour codes when ``True``.

    Returns:
        A newline-separated string, without a trailing newline.
    """
    grid = game.grid
    lines = [
        _paint(
            f"{game.target}   SCORE {game.score}   BEST {game.best}",
            BOLD + YELLOW,
            color,
        ),
        "",
    ]

    for row_index, row in enumerate(grid):
        for line_index in range(TILE_HEIGHT):
            lines.append(
                " ".join(_tile_line(value, line_index, color) for value in row)
            )
        if row_index < len(grid) - 1:
            lines.append("")

    lines.append("")

    if game.has_won():
        lines.append(
            _paint(
                f"You reached {game.target}! Keep going for a higher score.",
                BOLD + GREEN,
                color,
            )
        )
    else:
        lines.append("")

    if game.is_game_over():
        lines.append(
            _paint(
                f"Game over! Final score: {game.score}. "
                "Press R to restart or Q to quit.",
                BOLD + RED,
                color,
            )
        )
    else:
        lines.append("")

    lines.append("Arrows / WASD: move   U: undo   R: restart   Q: quit")

    if width > 0:
        lines = [
            " " * max((width - _visible_width(line)) // 2, 0) + line
            for line in lines
        ]

    return "\n".join(lines)


# ----------------------------------------------------------------------
# Input
# ----------------------------------------------------------------------
def _is_tty(stream: TextIO) -> bool:
    try:
        return bool(stream.isatty())
    except (AttributeError, ValueError):
        return False


def _read_key(fd: int) -> str:
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


# ----------------------------------------------------------------------
# Main loops
# ----------------------------------------------------------------------
def _run_interactive(game: Game, stdin: TextIO, stdout: TextIO) -> None:
    """Full-screen loop with single-key input."""
    fd = stdin.fileno()
    saved_attributes = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    stdout.write("\033[?25l")  # hide the cursor
    stdout.flush()

    try:
        while True:
            terminal = shutil.get_terminal_size((80, 24))
            frame = render(game, width=terminal.columns, color=True)
            top_margin = max(
                (terminal.lines - frame.count("\n") - 1) // 2 - 1,
                0,
            )

            stdout.write("\033[2J\033[H")
            stdout.write("\n" * top_margin)
            stdout.write(frame)
            stdout.write("\n")
            stdout.flush()

            key = _read_key(fd)

            if key in ("q", "quit"):
                return
            if key == "r":
                game.reset()
            elif key == "u":
                game.undo()
            elif key in ("left", "right", "up", "down"):
                game.move(key)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved_attributes)
        stdout.write("\033[?25h" + RESET + "\n")  # show the cursor
        stdout.flush()


def _run_line_mode(game: Game, stdin: TextIO, stdout: TextIO) -> None:
    """Read one command per line and print a new board after each command."""
    color = _is_tty(stdout)
    stdout.write(render(game, color=color) + "\n")
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
        elif command in _LINE_DIRECTIONS:
            if not game.move(_LINE_DIRECTIONS[command]):
                stdout.write("That move does not change the board.\n")
                stdout.flush()
                continue
        else:
            stdout.write(f"Unknown command: {command}\n")
            stdout.write("Use left/right/up/down, w/a/s/d, u, r, or q.\n")
            stdout.flush()
            continue

        stdout.write(render(game, color=color) + "\n")
        stdout.flush()


def run(
    game: Optional[Game] = None,
    stdin: Optional[TextIO] = None,
    stdout: Optional[TextIO] = None,
) -> None:
    """Run the terminal UI until the player quits.

    Args:
        game: Game instance to play. A new one is created by default.
        stdin: Input stream. Defaults to ``sys.stdin``.
        stdout: Output stream. Defaults to ``sys.stdout``.
    """
    game = game if game is not None else Game()
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout

    interactive = (
        termios is not None and _is_tty(stdin) and _is_tty(stdout)
    )
    if interactive:
        _run_interactive(game, stdin, stdout)
    else:
        _run_line_mode(game, stdin, stdout)


def main() -> int:
    """Console entry point. Returns a process exit code."""
    try:
        run()
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        sys.stdout.flush()
    except BrokenPipeError:
        pass
    return 0
