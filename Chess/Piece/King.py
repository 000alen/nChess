from typing import Tuple

from Chess.Piece import Piece


class King(Piece):
    """Implements the King piece and its generalization for higher dimensions."""

    @staticmethod
    def next(board, position: Tuple[int, ...], color, is_first_movement: bool):
        return Piece.ad_nauseam(board, position, color, board.cardinals + board.diagonals, 1)
