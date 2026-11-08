"""Pure game logic for 1024.

This module performs no I/O. It can be used by any front end (the bundled
terminal UI, a test suite, or another program) without side effects.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Optional, Sequence, Tuple


@dataclass
class _Snapshot:
    """State saved before a successful move so it can be undone."""

    grid: List[List[int]]
    score: int
    won: bool


class Game:
    """A sliding-tile merge game whose goal is the target tile.

    The board is a square grid of integers. ``0`` represents an empty cell.
    Equal tiles merge when they collide, and each tile may merge at most once
    per move.
    """

    DIRECTIONS = ("left", "right", "up", "down")
    MAX_UNDO = 20

    def __init__(
        self,
        size: int = 4,
        target: int = 1024,
        seed: Optional[int] = None,
    ) -> None:
        """Create a new game and spawn its first two tiles.

        Args:
            size: Number of rows and columns on the board.
            target: Tile value that counts as a win.
            seed: Optional seed for the random number generator. Supplying the
                same seed to two games makes their tile sequences identical.

        Raises:
            ValueError: If ``size`` or ``target`` is smaller than 2.
        """
        if size < 2:
            raise ValueError("size must be at least 2")
        if target < 2:
            raise ValueError("target must be at least 2")

        self.size = size
        self.target = target
        self._rng = random.Random(seed)
        self._grid: List[List[int]] = []
        self._score = 0
        self._best = 0
        self._won = False
        self._history: Deque[_Snapshot] = deque(maxlen=self.MAX_UNDO)
        self.reset()

    # ------------------------------------------------------------------
    # Read-only state
    # ------------------------------------------------------------------
    @property
    def grid(self) -> List[List[int]]:
        """A copy of the board as rows of integers (``0`` means empty)."""
        return [row[:] for row in self._grid]

    @property
    def score(self) -> int:
        """Current score: the sum of every merged tile value."""
        return self._score

    @property
    def best(self) -> int:
        """Highest score reached by this ``Game`` instance.

        The value is a high-water mark: it survives resets and undos and never
        decreases.
        """
        return self._best

    # ------------------------------------------------------------------
    # Game setup
    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Start a new round with an empty board and two random tiles.

        The score, win flag, and undo history are cleared. The best score is
        kept as a high-water mark.
        """
        self._grid = [[0] * self.size for _ in range(self.size)]
        self._score = 0
        self._won = False
        self._history.clear()
        self.spawn_tile()
        self.spawn_tile()

    def spawn_tile(self) -> int:
        """Place a 2 (90%) or a 4 (10%) in a random empty cell.

        Returns:
            The value of the new tile, or ``0`` if the board is full.
        """
        empty_cells = [
            (row, col)
            for row in range(self.size)
            for col in range(self.size)
            if self._grid[row][col] == 0
        ]
        if not empty_cells:
            return 0

        row, col = self._rng.choice(empty_cells)
        value = 4 if self._rng.random() < 0.1 else 2
        self._grid[row][col] = value
        return value

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------
    def move(self, direction: str) -> bool:
        """Slide every tile in ``direction`` and spawn a new tile.

        Args:
            direction: One of ``"left"``, ``"right"``, ``"up"``, ``"down"``.

        Returns:
            ``True`` if the board changed, otherwise ``False``. A move that
            does not change the board does not spawn a tile or create an undo
            checkpoint.

        Raises:
            ValueError: If ``direction`` is not a valid direction.
        """
        direction = direction.lower()
        if direction not in self.DIRECTIONS:
            raise ValueError(
                f"invalid direction {direction!r}; "
                f"expected one of {', '.join(self.DIRECTIONS)}"
            )
        if self.is_game_over():
            return False

        lines = self._read_lines(direction)
        new_lines: List[List[int]] = []
        gained = 0
        moved = False

        for line in lines:
            new_line, line_score = self._slide_line(line)
            gained += line_score
            moved = moved or new_line != line
            new_lines.append(new_line)

        if not moved:
            return False

        # Save the pre-move state, including the RNG state, so that undo also
        # rewinds future tile spawns.
        self._history.append(self._snapshot())
        self._write_lines(new_lines, direction)
        self._score += gained
        self._best = max(self._best, self._score)

        if any(value >= self.target for row in self._grid for value in row):
            self._won = True

        self.spawn_tile()
        return True

    def can_move(self) -> bool:
        """Return ``True`` if an empty cell or a mergeable pair exists."""
        for row in self._grid:
            if 0 in row:
                return True

        for row in range(self.size):
            for col in range(self.size):
                value = self._grid[row][col]
                if col + 1 < self.size and self._grid[row][col + 1] == value:
                    return True
                if row + 1 < self.size and self._grid[row + 1][col] == value:
                    return True
        return False

    def has_won(self) -> bool:
        """Return ``True`` once a tile has reached the target value.

        The win flag is remembered after the target tile is merged into a
        larger one, and the current board is also checked directly.
        """
        return self._won or any(
            value >= self.target for row in self._grid for value in row
        )

    def is_game_over(self) -> bool:
        """Return ``True`` when no legal move remains."""
        return not self.can_move()

    # ------------------------------------------------------------------
    # Undo
    # ------------------------------------------------------------------
    def undo(self) -> bool:
        """Restore the state before the most recent successful move.

        At most :attr:`MAX_UNDO` moves are remembered. The best score is a
        high-water mark and is not rolled back.

        Returns:
            ``True`` if a move was undone, ``False`` if there is no history.
        """
        if not self._history:
            return False

        snapshot = self._history.pop()
        self._grid = snapshot.grid
        self._score = snapshot.score
        self._won = snapshot.won
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _snapshot(self) -> _Snapshot:
        return _Snapshot(
            grid=[row[:] for row in self._grid],
            score=self._score,
            won=self._won,
        )

    def _read_lines(self, direction: str) -> List[List[int]]:
        """Extract board lines oriented so index 0 is the movement direction."""
        size = self.size
        if direction == "left":
            return [row[:] for row in self._grid]
        if direction == "right":
            return [row[::-1] for row in self._grid]
        if direction == "up":
            return [
                [self._grid[row][col] for row in range(size)]
                for col in range(size)
            ]
        # down: read each column from the bottom upwards
        return [
            [self._grid[row][col] for row in range(size - 1, -1, -1)]
            for col in range(size)
        ]

    def _write_lines(self, lines: List[List[int]], direction: str) -> None:
        """Write transformed lines back into the board."""
        size = self.size
        if direction == "left":
            self._grid = [line[:] for line in lines]
        elif direction == "right":
            self._grid = [line[::-1] for line in lines]
        elif direction == "up":
            self._grid = [
                [lines[col][row] for col in range(size)]
                for row in range(size)
            ]
        else:  # down
            self._grid = [
                [lines[col][size - 1 - row] for col in range(size)]
                for row in range(size)
            ]

    def _slide_line(self, line: Sequence[int]) -> Tuple[List[int], int]:
        """Slide and merge one line towards index 0.

        Each tile participates in at most one merge, so ``[2, 2, 2, 2]``
        becomes ``[4, 4, 0, 0]`` and ``[4, 4, 4, 0]`` becomes ``[8, 4, 0, 0]``.

        Returns:
            The resulting line and the score gained from its merges.
        """
        tiles = [value for value in line if value != 0]
        merged: List[int] = []
        gained = 0
        index = 0

        while index < len(tiles):
            if index + 1 < len(tiles) and tiles[index] == tiles[index + 1]:
                value = tiles[index] * 2
                merged.append(value)
                gained += value
                index += 2
            else:
                merged.append(tiles[index])
                index += 1

        merged.extend([0] * (self.size - len(merged)))
        return merged, gained
