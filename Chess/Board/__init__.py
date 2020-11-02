from enum import Enum, auto
from typing import Dict, Tuple, List, Type

from Chess.Piece import Piece


class Color(Enum):
    """Stores the piece colors."""

    WHITE = auto()
    BLACK = auto()


class Board:
    """Stores and manages the pieces.

    Attributes:
        size (int)
        dimension (int)
    """

    size: int
    dimension: int

    board: Dict[Tuple[int, ...], Tuple[Color, Type[Piece]]]
    is_first_movement: Dict[Tuple[int, ...], bool]

    cardinals: List[Tuple[int, ...]]
    diagonals: List[Tuple[int, ...]]
    L: List[Tuple[int, ...]]
    basis: List[Tuple[int, ...]]

    def __init__(self, size: int = 8, dimension: int = 2):
        assert dimension >= 2
        self.size = size
        self.dimension = dimension
        self.board = {}
        self.is_first_movement = {}
        self.compute_cardinals()
        self.compute_diagonals()
        self.compute_L()
        self.compute_basis()

    def compute_cardinals(self):
        self.cardinals = [
            tuple(j if k == i else 0 for k in range(self.dimension))
            for j in (-1, 1)
            for i in range(self.dimension)
        ]

    def compute_diagonals(self):
        from itertools import product
        self.diagonals = [
            tuple((1, -1)[k] for k in J) if i == self.dimension
            else tuple((-1, 1)[k] for k in J) + (0,) * (self.dimension - i)
            for i in range(2, self.dimension + 1)
            for J in product(range(2), repeat=i)
        ]

    def compute_L(self):
        from itertools import product
        self.L = []
        for i in range(self.dimension):
            for j in range(self.dimension):
                if i == j: continue
                for p, q in product((-1, 1), repeat=2):
                    movement = [0] * self.dimension
                    movement[i] = 2 * p
                    movement[j] = q
                    self.L.append(tuple(movement))

    def compute_basis(self):
        self.basis = []
        for i in range(self.dimension):
            u = [0] * self.dimension
            u[i] = 1
            self.basis.append(tuple(u))

    def add(self, piece: Type[Piece], position: Tuple[int, ...], color: Color):
        """Adds a piece to the Board."""
        assert len(position) == self.dimension
        assert position not in self.board
        self.board[position] = (color, piece)
        self.is_first_movement[position] = True

    def contains(self, position: Tuple[int, ...]) -> bool:
        """Checks if a piece is contained in the Board."""
        assert len(position) == self.dimension
        return position in self.board

    def get(self, position: Tuple[int, ...]) -> Tuple[Color, Type[Piece]]:
        """Returns the piece in the specified position."""
        assert len(position) == self.dimension
        return self.board[position]

    def move(self, initial_position: Tuple[int, ...], final_position: Tuple[int, ...]):
        """Moves a piece from one position to another; handles captures."""
        assert len(initial_position) == self.dimension
        assert len(final_position) == self.dimension
        assert self.contains(initial_position)

        color, piece = self.get(initial_position)
        assert piece.valid_next(self, initial_position, final_position, color, self.is_first_movement[initial_position])

        if self.contains(final_position):
            self.remove(final_position)

        self.add(piece, final_position, color)
        self.remove(initial_position)
        self.is_first_movement[final_position] = False

    def remove(self, position: Tuple[int, ...]):
        """Removes a piece from the Board."""
        assert len(position) == self.dimension
        assert position in self.board
        del self.board[position]
        del self.is_first_movement[position]

    def promote(self, position: Tuple[int, ...], final_piece: Type[Piece]):
        """Promotes a piece."""
        color, initial_piece = self.get(position)
        assert initial_piece.is_promotion_available(self, position, color)
        assert final_piece in initial_piece.promotions
        self.remove(position)
        self.add(final_piece, position, color)
        self.is_first_movement[position] = False

    def in_bounds(self, position: Tuple[int, ...]) -> bool:
        """Checks if a piece is inside the Board bounds."""
        return all(0 <= i < self.size for i in position)

    def in_check(self, color: Color):
        raise NotImplementedError

    def in_checkmate(self, color: Color):
        raise NotImplementedError

    def in_stalemate(self):
        raise NotImplementedError
