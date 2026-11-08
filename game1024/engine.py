"""Game logic for 1024."""

import random


class Game:
    DIRECTIONS = ("left", "right", "up", "down")

    def __init__(self, size=4, target=1024, seed=None):
        self.size = size
        self.target = target
        self._grid = []
        self._score = 0
        self._best = 0
        self._won = False
        self._history = []
        self.reset()

    @property
    def grid(self):
        return [row[:] for row in self._grid]

    @property
    def score(self):
        return self._score

    @property
    def best(self):
        return self._best

    def reset(self):
        self._grid = [[0] * self.size for _ in range(self.size)]
        self._score = 0
        self.spawn_tile()
        self.spawn_tile()

    def spawn_tile(self):
        empty = [
            (row, col)
            for row in range(self.size)
            for col in range(self.size)
            if self._grid[row][col] == 0
        ]
        if not empty:
            return 0
        row, col = random.choice(empty)
        value = 4 if random.random() < 0.1 else 2
        self._grid[row][col] = value
        return value


    def move(self, direction):
        if direction not in self.DIRECTIONS:
            raise ValueError(f"unknown direction: {direction}")

        lines = self._read_lines(direction)
        new_lines = []
        gained = 0
        moved = False
        for line in lines:
            tiles = [value for value in line if value]
            merged = []
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
            merged += [0] * (self.size - len(merged))
            moved = moved or merged != line
            new_lines.append(merged)

        if not moved:
            return False

        self._history.append(self._snapshot())
        self._write_lines(new_lines, direction)
        self._score += gained
        self._best = max(self._best, self._score)

        if any(value >= self.target for row in self._grid for value in row):
            self._won = True

        self.spawn_tile()
        return True

    def _read_lines(self, direction):
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

    def _write_lines(self, lines, direction):
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
    def can_move(self):
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
    def has_won(self):
        return self._won or any(
            value >= self.target for row in self._grid for value in row
        )
    def undo(self):
        if not self._history:
            return False
        grid, score, won = self._history.pop()
        self._grid = grid
        self._score = score
        self._won = won
        return True

    def _snapshot(self):
        return ([row[:] for row in self._grid], self._score, self._won)
