from typing import Tuple

from Chess.Piece import Piece


class Knight(Piece):
    """Implements the Knight piece and its generalization to higher dimensions."""

    @staticmethod
    def next(board, position: Tuple[int, ...], color):
        return Piece.ad_nauseam(board, position, color, board.L, 1)
