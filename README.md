# 1024 — a terminal tile-merging game

A complete, dependency-free implementation of the classic 1024 sliding-tile
puzzle (a 2048-style game where the winning tile is **1024**). It runs directly
in the terminal, uses plain ANSI colours, and is built with the Python standard
library only.

```
1024   SCORE 128   BEST 512

    2       4       8      16
   32      64     128     256
  512    1024      ...
```

---

## Features

- 4×4 sliding-tile board with classic merge rules
- Goal tile of 1024, with the option to keep playing after winning
- Score tracking plus a best-score high-water mark
- Undo up to 20 moves, including rewinding random tile spawns
- ANSI-coloured tiles; 256, 512, and 1024 are highlighted
- Single-key input with arrow keys or WASD
- Graceful line-based fallback when input is piped or not a TTY
- Pure engine with no I/O, fully covered by unit tests
- No third-party packages and no installation step

---

## Requirements

- Python 3.9 or newer
- A terminal with ANSI colour support (macOS Terminal, iTerm2, most Linux
  terminals, Windows Terminal)
- No `pip install` needed

Check your Python version:

```bash
python3 --version
```

---

## Quick start

From the project directory:

```bash
python3 -m game1024
```

The board is drawn immediately. Use the arrow keys (or WASD) to slide the
tiles. Press `q` to quit.

> Run the package as a module (`python3 -m game1024`). Running
> `python3 game1024/ui.py` directly will not work because the UI uses relative
> imports.

---

## Controls

| Key | Action |
| --- | --- |
| `←` / `A` | Slide tiles left |
| `→` / `D` | Slide tiles right |
| `↑` / `W` | Slide tiles up |
| `↓` / `S` | Slide tiles down |
| `U` | Undo the last move (up to 20) |
| `R` | Restart with a fresh board |
| `Q` / `Ctrl-C` | Quit |

Input is read one key press at a time — no Enter required. The terminal is put
into cbreak mode while the game runs and restored on exit, including when you
press `Ctrl-C`.

### Playing without a TTY

If stdin is not a terminal (for example, when piping a file), the UI switches
to line mode. Each line is one command:

```bash
printf 'left\ndown\nright\nup\nu\nr\nq\n' | python3 -m game1024
```

Accepted commands: `left`, `right`, `up`, `down`, `a`, `d`, `w`, `s`, `u`,
`r`, `q`. Unknown commands print a short help message. Colours are disabled
when output is redirected.

---

## Rules

1. The game starts with two random tiles, each a **2** or a **4**.
2. A move slides every tile as far as possible in the chosen direction.
3. Two equal tiles that collide merge into one tile with double the value.
   Each tile can merge only once per move:
   - `2 2 2 2` → `4 4`
   - `4 4 4` → `8 4`
4. A new tile is spawned after every successful move:
   - **90%** chance of a 2
   - **10%** chance of a 4
5. A move that does not change the board is ignored: no tile spawns and no
   undo checkpoint is created.
6. The game is won when a **1024** tile appears. Play continues so you can
   build an even higher score.
7. The game ends when the board is full and no adjacent tiles can be merged.

### Scoring

Every merge adds the value of the new tile to the score. Merging two 8s creates
a 16 and adds **16** points.

The **BEST** value is a high-water mark for the current `Game` instance. It
never decreases, even after an undo or a restart. Starting a new process starts
a new best score.

---

## Project structure

```
1024-game/
├── game1024/
│   ├── __init__.py      # exports Game
│   ├── engine.py        # pure game logic (no I/O)
│   ├── ui.py            # ANSI rendering, key input, main loop
│   └── __main__.py      # python3 -m game1024 entry point
├── tests/
│   └── test_engine.py   # unittest suite for the engine
├── README.md
└── FLEET_PROMPT.md      # original task specification
```

---

## Engine API

The engine is deliberately independent of the terminal, so it can be reused by
another front end or imported in a script:

```python
from game1024 import Game

game = Game(size=4, target=1024, seed=42)

print(game.grid)          # list of rows, 0 = empty
print(game.score)         # current score
print(game.best)          # high-water mark
print(game.has_won())     # True once a 1024 tile has appeared
print(game.is_game_over())  # True when no moves remain

if game.move("left"):     # True if the board changed
    print("moved!", game.score)

game.undo()               # restore the previous move
game.reset()              # start a new round
game.spawn_tile()         # place a 2/4 and return its value (0 if full)
```

### `Game` reference

| Member | Description |
| --- | --- |
| `Game(size=4, target=1024, seed=None)` | Create a game. `seed` makes tile spawns deterministic. |
| `DIRECTIONS` | `("left", "right", "up", "down")` |
| `MAX_UNDO` | `20` |
| `grid` | Copy of the board as rows of ints; `0` means empty |
| `score` | Sum of all merge values so far |
| `best` | Highest score reached by this instance (never decreases) |
| `move(direction)` | Slide tiles, merge, spawn, and return whether the board changed |
| `can_move()` | `True` if an empty cell or mergeable pair exists |
| `has_won()` | `True` once the target tile has been reached |
| `is_game_over()` | `True` when `can_move()` is `False` |
| `undo()` | Restore the previous move; `False` if there is no history |
| `reset()` | Start a new round with two tiles |
| `spawn_tile()` | Place a 2/4 in a random empty cell; returns its value, or `0` if full |

`move()` raises `ValueError` for an unknown direction.

---

## How the move algorithm works

All four directions share one code path:

1. **Read lines.** The board is read into four lines oriented so that index 0
   is the direction of travel:
   - left: rows as-is
   - right: rows reversed
   - up: columns top-to-bottom
   - down: columns bottom-to-top
2. **Slide each line.** Zeros are removed, then equal neighbours are merged in
   a single left-to-right pass. A merge consumes both tiles, which guarantees
   that each tile merges at most once per move.
3. **Write lines back**, reversing the same transformation used when reading.
4. **Update state.** Add the gained points to the score, update the best score,
   set the win flag if the target was reached, and spawn a new tile.
5. **Check for game over.** The board is over when every cell is filled and no
   horizontal or vertical neighbours are equal.

The RNG state is saved with each undo checkpoint. Undoing a move therefore also
rewinds future spawns, so replaying the same move produces the same tile.

---

## Running the tests

The suite uses only the standard library:

```bash
python3 -m unittest discover -s tests -v
```

It covers:

- initial two-tile spawn and deterministic seeding
- moves and merges in all four directions
- the `4 4 4 → 8 4` merge-once rule
- no-op moves returning `False` without spawning
- score accumulation across moves
- win detection at 1024 and continuing after a win
- game-over detection, including a move that ends the game
- undo restoration, RNG replay, empty history, and the 20-move limit
- reset behaviour, best-score preservation, and tile spawning

Quick engine smoke test:

```bash
python3 -c "from game1024 import Game; g = Game(seed=1); [g.move('left') for _ in range(3)]; print(g.score, g.has_won())"
```

Verify that the UI imports cleanly (it does not touch the terminal on import):

```bash
python3 -c "import game1024.ui"
```

---

## Customising

The engine supports other board sizes and targets:

```python
from game1024 import Game

# 5×5 board, win at 2048
game = Game(size=5, target=2048, seed=7)
```

The terminal UI adapts its tile count to `game.size`, though the 9-character
tile width is designed for readable 4×4 boards. Very large boards may not fit
narrow terminals.

Tile colours live in `TILE_STYLES` near the top of `game1024/ui.py`. Each entry
maps a tile value to a `(background, foreground, highlighted)` triple of
256-colour ANSI indices. Add entries to restyle higher tiles; unknown values
use `FALLBACK_TILE`.

---

## Troubleshooting

**Colours look wrong or the board does not redraw**
Use a terminal with ANSI support. If output is redirected, colours are disabled
automatically. Try a different terminal emulator if the screen does not clear.

**Arrow keys print characters instead of moving**
The UI only enables single-key mode when both stdin and stdout are TTYs. In an
IDE run terminal that is not a real TTY, use line mode by piping commands or
run the game in a normal terminal window.

**The terminal is left in a strange state after a crash**
The UI restores the terminal in a `finally` block. If a hard kill leaves the
terminal in cbreak mode, run `reset` (or `stty sane`) in that terminal.

**`ModuleNotFoundError: No module named 'game1024'`**
Run the command from the project root, or add the project directory to
`PYTHONPATH`.

**Windows**
`termios` and `tty` are Unix-only. The package still imports and runs in
line mode, where commands are read one per line. For single-key play, use
WSL or a Unix-like environment.

---

## License

This project is provided for learning and personal use. Do whatever you like
with it.
