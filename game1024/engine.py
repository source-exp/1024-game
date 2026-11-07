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

        self._write_lines(new_lines, direction)
        self._score += gained
        self._best = max(self._best, self._score)
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
