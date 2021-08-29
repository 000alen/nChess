from nChess.Board import Board, IntegerVector, Move
from nChess.Piece import Piece


class Queen(Piece):
    """Implements the Queen piece and its generalization to higher dimensions."""

    is_promotable = staticmethod(lambda: False)

    def all_moves(self) -> tuple["Move", ...]:
        return self.ad_nauseam(self.board.cardinals + self.board.diagonals, max(self.board.size) - 1)
