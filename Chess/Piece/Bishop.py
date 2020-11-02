from typing import Tuple

from Chess.Piece import Piece


class Bishop(Piece):
    """Implements the Bishop piece and its generalization for higher dimensions."""

    @staticmethod
    def next(board, position: Tuple[int, ...], color, is_first_movement: bool):
        return Piece.ad_nauseam(board, position, color, board.diagonals, board.size - 1)
