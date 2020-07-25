from typing import List

from Chess.Annotation import RepresentationType, PositionType, Color


class Piece:
    # board
    position: PositionType
    color: Color

    representation: RepresentationType

    def __init__(
            self,
            board,
            position: PositionType,
            color: Color,
    ):
        self.board = board
        self.position = position
        self.color = color

    def __str__(self):
        return self.representation[self.color]

    def no_conflict(
            self,
            position: PositionType,
    ) -> bool:
        return (
                self.board.in_bounds(position)
                and (
                        not self.board.contains(position)
                        or self.board.get(position).color is not self.color
                )
        )

    def move(
            self,
            end: PositionType
    ):
        assert self.is_valid_next(end)
        self.position = end

    def ad_nauseam(
            self,
            offsets: List[PositionType],
            n: int = 1
    ):
        moves = []
        for offset in offsets:
            for i in range(1, n + 1):
                new = tuple(self.position[j] + (offset[j] * i) for j in range(self.board.dimension))
                if self.no_conflict(new):
                    moves.append(new)
        return moves

    def is_valid_next(
            self,
            position: PositionType,
    ) -> bool:
        return position in self.available_next()

    def available_next(
            self,
    ) -> List[PositionType]:
        raise NotImplementedError
