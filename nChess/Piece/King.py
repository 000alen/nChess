from nChess.nBoard import nBoard, IntegerVector, Move
from nChess.Piece import Piece


class King(Piece):
    """Implements the King piece and its generalization for higher dimensions."""

    is_promotable = staticmethod(lambda: False)

    def all_moves(self) -> tuple["Move", ...]:
        return self.ad_nauseam(self.board.cardinals + self.board.diagonals, 1)
