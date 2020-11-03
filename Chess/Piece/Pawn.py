from typing import Tuple, Type, TypeVar

from Chess.Piece import Piece
from Chess.Piece.Bishop import Bishop
from Chess.Piece.Knight import Knight
from Chess.Piece.Queen import Queen
from Chess.Piece.Rook import Rook

_Piece = Type[Piece]
_Position = Tuple[int, ...]
_Color = TypeVar("_Color")


class Pawn(Piece):
    """Implements the Pawn piece and its generalization to higher dimensions."""

    promotions: Tuple[_Piece] = (Bishop, Knight, Queen, Rook)

    @staticmethod
    def is_promotion_available(
            board,
            position: _Position
    ):
        from Chess.Board import Color
        return all(i == (board.size - 1 if board.get(position).color == Color.WHITE else 0) for i in position[1:])

    @staticmethod
    def next(
            board,
            position: _Position
    ):
        movements = Pawn.ad_nauseam(board, position, board.basis[1:], 1)
        first_movements = Pawn.ad_nauseam(board, position, board.basis[1:], 2) \
            if board.is_first_movement(position) else []

        capture_movements = []
        for movement in movements:
            for i in (-1, 1):
                new_position = (movement[0] + i, *movement[1:])
                if Pawn.no_conflict(board, position, new_position) and board.contains(new_position):
                    capture_movements.append(new_position)

        return movements + first_movements + capture_movements
