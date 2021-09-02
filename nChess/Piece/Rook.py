
from nChess.nBoard import nBoard, IntegerVector, Move
from nChess.Piece import Piece


class Rook(Piece):
    """Implements the Rook piece and its generalization to higher dimensions."""

    is_promotable = staticmethod(lambda: False)

    def all_moves(self) -> tuple["Move", ...]:
        return self.ad_nauseam(self.board.cardinals, max(self.board.size) - 1)
