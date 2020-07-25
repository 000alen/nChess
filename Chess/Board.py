from typing import List

from Chess.Annotation import DistributionType, BoardType, PositionType, Color
from Chess.Distribution import Classic

__all__ = (
    "Board"
)


class Board:
    size: int
    dimension: int
    pieces: BoardType
    turn: Color

    cardinals: List[PositionType] = None
    diagonals: List[PositionType] = None

    def __init__(
            self,
            size: int = 8,
            dimension: int = 2,
            distribution: DistributionType = Classic
    ):
        self.size = size
        self.dimension = dimension
        self.pieces = []
        self.turn = Color.WHITE
        self._compute_cardinals()
        self._compute_diagonals()
        self._load_distribution(distribution)

    def __contains__(self, position: PositionType):
        return self.contains(position)

    def _compute_cardinals(self):
        self.cardinals = [
            tuple(k if j == i else 0 for j in range(self.dimension))
            for i in range(self.dimension)
            for k in (-1, 1)
        ]

    def _compute_diagonals(self):
        from itertools import product
        self.diagonals = list(
            tuple((1, -1)[i] for i in indices)
            for indices in product(range(2), repeat=self.dimension)
        )

    def _load_distribution(
            self,
            distribution: DistributionType
    ):
        for color, board in distribution.items():
            for position, piece_type in board.items():
                assert len(position) == self.dimension
                self.add(
                    position
                    if color is Color.WHITE
                    else tuple(self.size - coordinate - 1 for coordinate in position),
                    color,
                    piece_type
                )

    def next_turn(self):
        self.turn = Color.BLACK if self.turn is Color.WHITE else Color.WHITE

    def is_check(
            self,
            color: Color
    ) -> bool:
        from Chess.Piece.King import King
        king_position = None
        base_positions = []
        for piece in self.pieces:
            if isinstance(piece, King) and piece.color is color:
                king_position = piece.position
            elif piece.color is not color:
                base_positions.append(piece.position)
        if king_position:
            return any(
                self.get(base_position).is_valid_next(king_position)
                for base_position in base_positions
            )

    def in_bounds(
            self,
            position: PositionType
    ) -> bool:
        assert len(position) == self.dimension
        return all(
            0 <= i < self.size
            for i in position
        )

    def contains(
            self,
            position: PositionType
    ) -> bool:
        assert self.in_bounds(position)
        return any(piece.position == position for piece in self.pieces)

    def add(
            self,
            position: PositionType,
            color: Color,
            piece_type
    ):
        assert self.in_bounds(position)
        self.pieces.append(piece_type(self, position, color))

    def get(
            self,
            position: PositionType
    ):
        assert self.in_bounds(position)
        for piece in self.pieces:
            if piece.position == position:
                return piece

    def move(
            self,
            start: PositionType,
            end: PositionType
    ):
        assert self.contains(start)
        assert self.in_bounds(end)
        target = self.get(start)
        if target.is_valid_next(end):
            if self.contains(end):
                self.remove(end)
            target.move(end)
        else:
            raise Exception

    def remove(
            self,
            position: PositionType
    ):
        assert self.in_bounds(position)
        self.pieces.remove(self.get(position))
