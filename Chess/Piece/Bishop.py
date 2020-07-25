from typing import List

from Chess.Annotation import PositionType, Color
from Chess.Piece.Piece import Piece


class Bishop(Piece):
    representation = {
        Color.WHITE: "♗",
        Color.BLACK: "♝"
    }

    def available_next(
            self,
    ) -> List[PositionType]:
        return self.ad_nauseam(self.board.diagonals, self.board.size)
