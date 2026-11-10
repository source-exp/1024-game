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

    def test_score_accumulates_across_moves(self) -> None:
        game = make_game(
            [
                [2, 2, 0, 0],
                [2, 2, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
            ]
        )

        self.assertTrue(game.move("left"))
        self.assertEqual(game.score, 8)
        self.assertEqual(game.grid[0], [4, 0, 0, 0])
        self.assertEqual(game.grid[1], [4, 0, 0, 0])

        self.assertTrue(game.move("up"))
        self.assertEqual(game.score, 16)
        self.assertEqual(game.grid[0][0], 8)

    def test_no_op_move_returns_false_and_does_not_spawn(self) -> None:
        game = Game(seed=4)
        game._grid = [[2, 4, 0, 0]] + EMPTY_BOARD[1:]
        game._score = 0
        game._won = False
        game._history.clear()
        before = game.grid

        self.assertFalse(game.move("left"))
        self.assertEqual(game.grid, before)
        self.assertEqual(game.score, 0)

    def test_successful_move_spawns_one_tile(self) -> None:
        game = Game(seed=4)
        game._grid = [[2, 4, 0, 0]] + EMPTY_BOARD[1:]
        game._score = 0
        game._won = False
        game._history.clear()
        before = tile_count(game)

        self.assertTrue(game.move("right"))
        self.assertEqual(tile_count(game), before + 1)

    def test_invalid_direction_raises(self) -> None:
        with self.assertRaises(ValueError):
            make_game(EMPTY_BOARD).move("sideways")

    def test_full_checkerboard_is_game_over(self) -> None:
        game = make_game(CHECKERBOARD)

        self.assertFalse(game.can_move())
        self.assertTrue(game.is_game_over())
        self.assertFalse(game.move("left"))

    def test_move_can_end_the_game(self) -> None:
        game = make_game(
            [
                [0, 2, 4, 2],
                [4, 2, 4, 2],
                [2, 4, 2, 4],
                [4, 2, 4, 2],
            ]
        )

        def fill_last_cell() -> int:
            game._grid[0][3] = 4
            return 4

        game.spawn_tile = fill_last_cell  # type: ignore[method-assign]

        self.assertTrue(game.move("left"))
        self.assertEqual(game.grid[0], [2, 4, 2, 4])
        self.assertTrue(game.is_game_over())

    def test_win_when_target_is_reached(self) -> None:
        game = make_game([[512, 512, 0, 0]] + EMPTY_BOARD[1:])

        self.assertTrue(game.move("left"))
        self.assertEqual(game.grid[0][0], 1024)
        self.assertEqual(game.score, 1024)
        self.assertTrue(game.has_won())

    def test_has_won_scans_the_current_grid(self) -> None:
        game = make_game([[1024, 0, 0, 0]] + EMPTY_BOARD[1:])

        self.assertTrue(game.has_won())

    def test_custom_target_counts_as_a_win(self) -> None:
        game = make_game([[32, 32, 0, 0]] + EMPTY_BOARD[1:], target=64)

        self.assertTrue(game.move("left"))
        self.assertTrue(game.has_won())

    def test_game_continues_after_winning(self) -> None:
        game = make_game([[512, 512, 0, 0]] + EMPTY_BOARD[1:])
        game.move("left")

        self.assertTrue(game.has_won())
        self.assertTrue(game.move("right"))
        self.assertTrue(game.has_won())

    def test_seeded_games_play_identically(self) -> None:
        first = Game(seed=123)
        second = Game(seed=123)

        for direction in ("left", "down", "right", "up", "left", "up"):
            self.assertEqual(
                first.move(direction),
                second.move(direction),
            )

        self.assertEqual(first.grid, second.grid)
        self.assertEqual(first.score, second.score)
        self.assertEqual(first.best, second.best)


if __name__ == "__main__":
    unittest.main()
