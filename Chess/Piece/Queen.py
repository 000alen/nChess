from typing import Tuple

from Chess.Piece import Piece


class Queen(Piece):
    """Implements the Queen piece and its generalization to higher dimensions."""

    @staticmethod
    def next(board, position: Tuple[int, ...], color):
        return Piece.ad_nauseam(board, position, color, board.cardinals + board.diagonals, board.size - 1)
