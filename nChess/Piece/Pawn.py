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

    def is_promotable(self) -> bool:
        from nChess.nBoard.Board import ClassicColor
        return all(
            i == (self.board.size[i] - 1 if self.board.get(self.position).color == ClassicColor.white else 0)
            for i in self.position[1::]
        )

    def all_moves(self) -> tuple["Move", ...]:
        from nChess.nBoard.Board import ClassicColor

        direction = 1 if self.color is ClassicColor.white else -1
        
        moves = []
        for i, base in enumerate(self.board.basis):
            if i == self.capture_axis:
                continue
            unfiltered_move = Move(self.position, tuple(self.position[i] + base[i] * direction for i in range(self.board.dimension)))
            if self.board.in_bounds(unfiltered_move.final_position) and not self.board.contains(unfiltered_move.final_position):
                moves.append(unfiltered_move)
                unfiltered_move = Move(self.position, tuple(self.position[i] + base[i] * direction * 2 for i in range(self.board.dimension)))
                if self.board.in_bounds(unfiltered_move.final_position) and not self.board.contains(unfiltered_move.final_position):
                    moves.append(unfiltered_move)

        capture_moves = []
        for i in (-1, 1):
            for base in self.board.basis:
                unfiltered_move = Move(self.position, tuple(
                    self.position[j] + base[j] * direction + i * self.board.basis[self.capture_axis][j] for j in range(self.board.dimension)
                    )
                )
                if not self.board.move_in_conflict(unfiltered_move) and self.board.contains(unfiltered_move.final_position):
                    capture_moves.append(unfiltered_move)

        return tuple(moves + capture_moves)
