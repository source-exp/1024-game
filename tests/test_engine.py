"""Unit tests for the 1024 engine.

Run from the project root with::

    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest
from typing import List

from game1024 import Game

CHECKERBOARD = [
    [2, 4, 2, 4],
    [4, 2, 4, 2],
    [2, 4, 2, 4],
    [4, 2, 4, 2],
]

EMPTY_BOARD = [
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
]


def make_game(grid: List[List[int]], **kwargs) -> Game:
    """Create a game with a fixed board and random spawning disabled."""
    game = Game(seed=0, **kwargs)
    game._grid = [row[:] for row in grid]
    game._score = 0
    game._won = False
    game._history.clear()
    game.spawn_tile = lambda: 0  # type: ignore[method-assign]
    return game


def tile_count(game: Game) -> int:
    return sum(1 for row in game.grid for value in row if value)


class InitialStateTests(unittest.TestCase):
    def test_starts_with_two_tiles(self) -> None:
        game = Game(seed=1)
        values = [value for row in game.grid for value in row if value]

        self.assertEqual(len(values), 2)
        self.assertTrue(all(value in (2, 4) for value in values))
        self.assertEqual(game.score, 0)
        self.assertEqual(game.best, 0)
        self.assertFalse(game.has_won())
        self.assertFalse(game.is_game_over())

    def test_board_size_and_target_are_configurable(self) -> None:
        game = Game(size=3, target=64, seed=2)

        self.assertEqual(len(game.grid), 3)
        self.assertTrue(all(len(row) == 3 for row in game.grid))
        self.assertEqual(game.target, 64)

    def test_grid_property_returns_a_copy(self) -> None:
        game = Game(seed=1)
        grid = game.grid
        grid[0][0] = 999

        self.assertNotEqual(game.grid[0][0], 999)

    def test_same_seed_produces_the_same_starting_board(self) -> None:
        self.assertEqual(Game(seed=99).grid, Game(seed=99).grid)


class MoveTests(unittest.TestCase):
    def assert_move(
        self,
        grid: List[List[int]],
        direction: str,
        expected: List[List[int]],
        expected_score: int,
    ) -> Game:
        game = make_game(grid)
        self.assertTrue(game.move(direction))
        self.assertEqual(game.grid, expected)
        self.assertEqual(game.score, expected_score)
        return game

    def test_move_left(self) -> None:
        self.assert_move(
            [[2, 2, 0, 0]] + EMPTY_BOARD[1:],
            "left",
            [[4, 0, 0, 0]] + EMPTY_BOARD[1:],
            4,
        )

    def test_move_right(self) -> None:
        self.assert_move(
            [[0, 0, 2, 2]] + EMPTY_BOARD[1:],
            "right",
            [[0, 0, 0, 4]] + EMPTY_BOARD[1:],
            4,
        )

    def test_move_up(self) -> None:
        self.assert_move(
            [
                [2, 0, 0, 0],
                [2, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
            ],
            "up",
            [[4, 0, 0, 0]] + EMPTY_BOARD[1:],
            4,
        )

    def test_move_down(self) -> None:
        self.assert_move(
            [
                [2, 0, 0, 0],
                [2, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
            ],
            "down",
            EMPTY_BOARD[:3] + [[4, 0, 0, 0]],
            4,
        )

    def test_each_tile_merges_only_once(self) -> None:
        self.assert_move(
            [[2, 2, 2, 2]] + EMPTY_BOARD[1:],
            "left",
            [[4, 4, 0, 0]] + EMPTY_BOARD[1:],
            8,
        )

    def test_444_becomes_84(self) -> None:
        self.assert_move(
            [[4, 4, 4, 0]] + EMPTY_BOARD[1:],
            "left",
            [[8, 4, 0, 0]] + EMPTY_BOARD[1:],
            8,
        )


if __name__ == "__main__":
    unittest.main()
