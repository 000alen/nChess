from nChess.Board import Board, IntegerVector, Move
from nChess.Piece import Piece


class Bishop(Piece):
    """Implements the Bishop piece and its generalization for higher dimensions."""

    is_promotable = staticmethod(lambda: False)

    def all_moves(self) -> tuple["Move", ...]:
        return self.ad_nauseam(self.board.diagonals, max(self.board.size) - 1)
