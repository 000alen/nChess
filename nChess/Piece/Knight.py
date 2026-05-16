from nChess.nBoard import nBoard, IntegerVector, Move
from nChess.Piece import Piece


class Knight(Piece):
    """Implements the Knight piece and its generalization to higher dimensions."""

    is_promotable = staticmethod(lambda: False)

    def all_moves(self) -> tuple["Move", ...]:
        moves = []
        for offset in self.board.L:
            move = Move(self.position, tuple(self.position[i] + offset[i] for i in range(self.board.dimension)))
            if self.board.move_in_conflict(move, force=True, validate_check=False):
                continue
            moves.append(move)
        return moves
