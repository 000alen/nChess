from typing import List

from Chess.Annotation import PositionType, Color
from Chess.Piece.Piece import Piece


class Pawn(Piece):
    representation = {
        Color.WHITE: "♙",
        Color.BLACK: "♟"
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.moved = False
        self.direction = 1 if self.color is Color.WHITE else -1

    def move(
            self,
            end: PositionType
    ):
        super().move(end)
        if not self.moved:
            self.moved = True

    def available_next(
            self,
    ) -> List[PositionType]:
        magnitude = 1 if self.moved else 2
        moves = []
        for x_offset in (-1, 0, 1):
            for i in range(1, self.board.dimension):
                new = (
                    self.position[0] + x_offset,
                    *(magnitude if i == j else 0 for j in range(1, self.board.dimension))
                )
                if not self.board.in_bounds(new):
                    continue
                if x_offset == 0 and not self.board.contains(new) or x_offset != 0 and self.board.contains(
                        new) and self.no_conflict(new):
                    moves.append(new)
        return moves
