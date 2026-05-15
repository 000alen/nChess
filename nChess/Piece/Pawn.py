from typing import Type

from nChess.nBoard import nBoard, Move
from nChess.Piece import Piece
from nChess.Piece.Bishop import Bishop
from nChess.Piece.Knight import Knight
from nChess.Piece.Queen import Queen
from nChess.Piece.Rook import Rook


class Pawn(Piece):
    """Implements the Pawn piece and its generalization to higher dimensions."""

    promotions: tuple[Type["Piece"]] = (Bishop, Knight, Queen, Rook)

    def __init__(self, position, color, has_moved=False, board=None, capture_axis=0) -> None:
        super().__init__(position, color, has_moved, board)
        self.capture_axis = capture_axis

    @property
    def direction(self) -> int:
        return 1 if getattr(self.color, "name", self.color) == "white" else -1

    def is_promotable(self) -> bool:
        return all(
            self.position[axis] == (self.board.size[axis] - 1 if self.direction == 1 else 0)
            for axis in range(self.board.dimension)
            if axis != self.capture_axis
        )

    def all_moves(self) -> tuple["Move", ...]:
        moves = []
        for axis, base in enumerate(self.board.basis):
            if axis == self.capture_axis:
                continue
            unfiltered_move = Move(self.position, tuple(self.position[i] + base[i] * self.direction for i in range(self.board.dimension)))
            if self.board.in_bounds(unfiltered_move.final_position) and not self.board.contains(unfiltered_move.final_position):
                moves.append(unfiltered_move)
                unfiltered_move = Move(self.position, tuple(self.position[i] + base[i] * self.direction * 2 for i in range(self.board.dimension)))
                if self.board.in_bounds(unfiltered_move.final_position) and not self.board.contains(unfiltered_move.final_position):
                    if not self.has_moved:
                        moves.append(unfiltered_move)

        capture_moves = []
        for i in (-1, 1):
            for axis, base in enumerate(self.board.basis):
                if axis == self.capture_axis:
                    continue
                unfiltered_move = Move(self.position, tuple(
                    self.position[j] + base[j] * self.direction + i * self.board.basis[self.capture_axis][j] for j in range(self.board.dimension)
                    )
                )
                if self.board.contains(unfiltered_move.final_position) and not self.board.move_in_conflict(unfiltered_move, force=True, validate_check=False):
                    capture_moves.append(unfiltered_move)

        return tuple(moves + capture_moves)
