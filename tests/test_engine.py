"""Unit tests for the 1024 engine.

Run from the project root with::

    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest

from game1024 import Game


class InitialStateTests(unittest.TestCase):
    def test_starts_with_two_tiles(self) -> None:
        game = Game(seed=1)
        values = [value for row in game.grid for value in row if value]

        self.assertEqual(len(values), 2)
        self.assertTrue(all(value in (2, 4) for value in values))
        self.assertEqual(game.score, 0)
        self.assertFalse(game.is_game_over())

    def test_board_size_is_configurable(self) -> None:
        game = Game(size=3, seed=2)

        self.assertEqual(len(game.grid), 3)
        self.assertTrue(all(len(row) == 3 for row in game.grid))


class SpawnTests(unittest.TestCase):
    def test_spawn_tile_returns_two_or_four(self) -> None:
        game = Game(seed=3)
        game._grid = [[0] * 4 for _ in range(4)]

        value = game.spawn_tile()

        self.assertIn(value, (2, 4))


if __name__ == "__main__":
    unittest.main()
