"""Game logic for 1024."""

import random


class Game:
    def __init__(self, size=4, target=1024, seed=None):
        self.size = size
        self.target = target
        self._grid = []
        self._score = 0
        self.reset()

    @property
    def grid(self):
        return [row[:] for row in self._grid]

    @property
    def score(self):
        return self._score

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
        if direction not in ("left", "right"):
            raise ValueError(f"unknown direction: {direction}")

        lines = [row[:] for row in self._grid]
        if direction == "right":
            lines = [row[::-1] for row in lines]

        new_lines = []
        moved = False
        for line in lines:
            tiles = [value for value in line if value]
            merged = []
            for value in tiles:
                if merged and merged[-1] == value:
                    merged[-1] *= 2
                else:
                    merged.append(value)
            merged += [0] * (self.size - len(merged))
            moved = moved or merged != line
            new_lines.append(merged)

        if not moved:
            return False

        if direction == "right":
            new_lines = [line[::-1] for line in new_lines]
        self._grid = new_lines
        self.spawn_tile()
        return True
