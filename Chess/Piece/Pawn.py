from typing import Tuple, List, Type

from Chess.Piece import Piece
from Chess.Piece.Bishop import Bishop
from Chess.Piece.Knight import Knight
from Chess.Piece.Queen import Queen
from Chess.Piece.Rook import Rook


class Pawn(Piece):
    """Implements the Pawn piece and its generalization to higher dimensions."""

    promotions: List[Type[Piece]] = [Bishop, Knight, Queen, Rook]

    @staticmethod
    def is_promotion_available(board, position: Tuple[int, ...], color):
        from Chess.Board import Color
        return all(i == (board.size - 1 if color == Color.WHITE else 0) for i in position[1:])

    @staticmethod
    def next(board, position: Tuple[int, ...], color, is_first_movement: bool):
        movements = Piece.ad_nauseam(board, position, color, board.basis[1:], 1)
        first_movements = Piece.ad_nauseam(board, position, color, board.basis[1:], 2) if is_first_movement else []

        capture_movements = []
        for movement in movements:
            for i in (-1, 1):
                new_position = (movement[0] + i, *movement[1:])
                # noinspection PyTypeChecker
                if Piece.no_conflict(board, position, new_position, color) and board.contains(new_position):
                    capture_movements.append(new_position)

        return movements + first_movements + capture_movements
