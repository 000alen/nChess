from typing import Type

from nChess.Board import Board, Move
from nChess.Piece import Piece
from nChess.Piece.Bishop import Bishop
from nChess.Piece.Knight import Knight
from nChess.Piece.Queen import Queen
from nChess.Piece.Rook import Rook


class Pawn(Piece):
    """Implements the Pawn piece and its generalization to higher dimensions."""

    promotions: tuple[Type["Piece"]] = (Bishop, Knight, Queen, Rook)

    def __init__(self, position, color, has_moved=False, board=None, capture_axis=1) -> None:
        super().__init__(position, color, has_moved, board)
        self.capture_axis = capture_axis

    def is_promotable(self) -> bool:
        from nChess.Board.Classic import ClassicColor
        return all(
            i == (self.board.size[i] - 1 if self.board.get(self.position).color == ClassicColor.white else 0)
            for i in self.position[1::]
        )

    def all_moves(self) -> tuple["Move", ...]:
        from nChess.Board.Classic import ClassicColor
        k = 1 if self.color is ClassicColor.white else -1
        offsets = self.board.basis[:self.capture_axis] + self.board.basis[self.capture_axis + 1:]
        
        moves = []
        for offset in offsets:
            unfiltered_move = Move(self.position, tuple(self.position[i] + k * offset[i] for i in range(self.board.dimension)))
            if self.board.in_bounds(unfiltered_move.final_position) and not self.board.contains(unfiltered_move.final_position):
                moves.append(unfiltered_move)

        first_moves = []
        if self.has_moved:
            for offset in offsets:
                unfiltered_move = Move(self.position, tuple(self.position[i] + 2 * k * offset[i] for i in range(self.board.dimension))) 
                if self.board.in_bounds(unfiltered_move.final_position) and not self.board.contains(unfiltered_move.final_position):
                    first_moves.append(unfiltered_move)

        capture_offsets = [
            self.board.basis[self.capture_axis],
            tuple(-1 * self.board.basis[self.capture_axis][i] for i in range(self.board.dimension))
        ]
        capture_moves = []
        for move in moves:
            for capture_offset in capture_offsets:
                unfiltered_capture = Move(self.position, tuple(move.final_position[i] + capture_offset[i] for i in range(self.board.dimension)))
                if not self.board.move_in_conflict(unfiltered_capture) and self.board.contains(unfiltered_capture.final_position):
                    capture_moves.append(unfiltered_capture)
        
        return tuple(moves + first_moves + capture_moves)
