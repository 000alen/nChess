from typing import List

from Chess.Annotation import PositionType, Color
from Chess.Piece.Piece import Piece


class Queen(Piece):
    representation = {
        Color.WHITE: "♕",
        Color.BLACK: "♛"
    }

    def available_next(
            self,
    ) -> List[PositionType]:
        return self.ad_nauseam(self.board.cardinals + self.board.diagonals, self.board.size)
