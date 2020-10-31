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
    cardinals: List[Tuple[int, ...]]
    diagonals: List[Tuple[int, ...]]
    L: List[Tuple[int, ...]]
    basis: List[Tuple[int, ...]]

    def __init__(self, size: int = 8, dimension: int = 2):
        assert dimension >= 2
        self.size = size
        self.dimension = dimension
        self.board = {}
        self.compute_cardinals()
        self.compute_diagonals()
        self.compute_L()
        self.compute_basis()

    def compute_cardinals(self):
        self.cardinals = []
        for i in range(self.dimension):
            for offset in (-1, 1):
                self.cardinals.append(
                    tuple(offset if j == i else 0 for j in range(self.dimension))
                )

    def compute_diagonals(self):
        from itertools import product
        self.diagonals = []
        for partial_dimension in range(2, self.dimension + 1):
            for indices in product(range(2), repeat=partial_dimension):
                diagonal = tuple((1, -1)[i] for i in indices)
                self.diagonals.append(
                    diagonal
                    if len(diagonal) == self.dimension
                    else diagonal + (0,) * (self.dimension - len(diagonal))
                )

    def compute_L(self):
        from itertools import product
        self.L = []
        for i in range(self.dimension):
            for j in range(self.dimension):
                if i == j:
                    continue
                for p, q in product((-1, 1), repeat=2):
                    move = [0] * self.dimension
                    move[i] = 2 * p
                    move[j] = q
                    self.L.append(tuple(move))

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
        assert initial_position in self.board

        color, piece = self.get(initial_position)
        assert piece.valid_next(self, initial_position, final_position, color)

        if final_position in self.board:
            self.remove(final_position)

        self.add(piece, final_position, color)
        self.remove(initial_position)

    def remove(self, position: Tuple[int, ...]):
        """Removes a piece from the Board."""
        assert len(position) == self.dimension
        assert position in self.board
        del self.board[position]

    def in_bounds(self, position: Tuple[int, ...]) -> bool:
        """Checks if a piece is inside the Board bounds."""
        return all(0 <= i < self.size for i in position)

    def promote(self, position: Tuple[int, ...], final_piece: Type[Piece]):
        """Promotes a piece."""
        color, initial_piece = self.get(position)
        assert initial_piece.is_promotion_available(self, position, color)
        assert final_piece in initial_piece.promotions

        self.remove(position)
        self.add(final_piece, position, color)
