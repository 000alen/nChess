from typing import Tuple, Type, TypeVar

from Chess.Piece import Piece

_Piece = Type[Piece]
_Position = Tuple[int, ...]
_Color = TypeVar("_Color")


class Queen(Piece):
    """Implements the Queen piece and its generalization to higher dimensions."""

    @staticmethod
    def next(
            board,
            position: _Position
    ):
        return Piece.ad_nauseam(
            board,
            position,
            board.cardinals + board.diagonals,
            board.size - 1
        )
