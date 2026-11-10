"""1024: a terminal sliding-tile merge game.

The public API is the :class:`game1024.engine.Game` class, re-exported here::

    from game1024 import Game

    game = Game(seed=1)
    game.move("left")
    print(game.score)
"""

from .engine import Game

__all__ = ["Game"]
__version__ = "1.0.0"
