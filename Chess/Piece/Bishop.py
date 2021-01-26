from typing import Tuple, Type, TypeVar

from Chess.Piece import Piece

_Piece = Type[Piece]
_Position = Tuple[int, ...]
_Color = TypeVar("_Color")


class Bishop(Piece):
    """Implements the Bishop piece and its generalization for higher dimensions."""

    is_promotion_available = staticmethod(lambda board, position: False)

    @staticmethod
    def _unfiltered_movements(
            board,
            position: _Position
    ):
        return Piece.ad_nauseam(board, position, board.diagonals, board.size - 1)
