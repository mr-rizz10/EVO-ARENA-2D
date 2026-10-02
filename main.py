"""
main.py
-------
Entry point. Run this file to play EvoArena.

    pip install pygame
    python main.py
"""

from game import Game


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
