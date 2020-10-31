from typing import Tuple

from Chess.Piece import Piece


class Pawn(Piece):
    """Implements the Pawn piece and its generalization to higher dimensions."""

    @staticmethod
    def next(board, position: Tuple[int, ...], color):
        movements = Piece.ad_nauseam(board, position, color, board.basis[1:], 1)

        capture_movements = []
        for movement in movements:
            for i in (-1, 1):
                new_position = (movement[0] + i, *movement[1:])
                # noinspection PyTypeChecker
                if Piece.no_conflict(board, position, new_position, color) and board.contains(new_position):
                    capture_movements.append(new_position)

        return movements + capture_movements
