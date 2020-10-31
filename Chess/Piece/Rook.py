from typing import Tuple

from Chess.Piece import Piece


class Rook(Piece):
    """Implements the Rook piece and its generalization to higher dimensions."""

    @staticmethod
    def next(board, position: Tuple[int, ...], color):
        return Piece.ad_nauseam(board, position, color, board.cardinals, board.size)
