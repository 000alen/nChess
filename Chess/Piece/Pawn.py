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
        from Chess.Board import Color
        k = 1 if board.get(position).color is Color.WHITE else -1
        offsets = board.basis[:capture_axis] + board.basis[capture_axis + 1:]
        
        movements = []
        for offset in offsets:
            unfiltered_movement = tuple(position[i] + k * offset[i] for i in range(board.dimension))
            if board.in_bounds(unfiltered_movement) and  not board.contains(unfiltered_movement):
                movements.append(unfiltered_movement)

        first_movements = []
        if board.is_first_movement(position):
            for offset in offsets:
                unfiltered_movement = tuple(position[i] + 2 * k * offset[i] for i in range(board.dimension))
                if board.in_bounds(unfiltered_movement) and not board.contains(unfiltered_movement):
                    first_movements.append(unfiltered_movement)

        capture_offsets = [
            board.basis[capture_axis],
            tuple(-1 * board.basis[capture_axis][i] for i in range(board.dimension))
        ]
        capture_movements = []
        for movement in movements:
            for offset in capture_offsets:
                unfiltered_capture = tuple(movement[i] + offset[i] for i in range(board.dimension))
                if board.no_conflict(position, unfiltered_capture) and board.contains(unfiltered_capture):
                    capture_movements.append(unfiltered_capture)
        
        return movements + first_movements + capture_movements
