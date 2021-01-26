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
    def _unfiltered_movements(
        board, 
        position: _Position,
        capture_axis: int = 0
    ):
        movement_offsets = board.basis[:capture_axis] + board.basis[capture_axis + 1:]
        movements = Pawn.ad_nauseam(board, position, movement_offsets, 2 if board.is_first_movement(position) else 1)

        capture_offset = board.basis[capture_axis]
        captures = []
        for movement in movements:
            for i in (-1, 1):
                partial_capture = tuple(movement[j] + i * capture_offset[j] for j in range(board.dimension))
                if board.no_conflict(position, partial_capture) and board.contains(partial_capture):
                    captures.append(partial_capture)
        
        return movements + captures
