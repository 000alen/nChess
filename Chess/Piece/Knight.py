from typing import List

from Chess.Annotation import PositionType, Color
from Chess.Piece.Piece import Piece


class Knight(Piece):
    representation = {
        Color.WHITE: "♘",
        Color.BLACK: "♞"
    }

    def knight_list(
            self,
            int1: int,
            int2: int
    ) -> List[PositionType]:
        # TODO: Generalize to higher dimensions.
        return [
            (self.position[0] + i * i_int, self.position[1] + j * j_int)
            for i in (-1, 1)
            for i_int in (int1, int2)
            for j in (-1, 1)
            for j_int in (int1, int2)
        ]

    def available_next(
            self,
    ) -> List[PositionType]:
        from itertools import permutations, product
        return [
            permutation
            for i, j in product((-1, 1), repeat=2)
            for permutation in permutations((i * 2, j * 1, *(0 for _ in range(self.board.dimension - 2))))
            if self.no_conflict(permutation)
        ]
