from enum import Enum, auto
from typing import Dict, Tuple, List, Type, Iterator

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

    _size: int
    _dimension: int
    _pieces: Dict[Tuple[int, ...], Tuple[Color, Type[Piece]]]
    _is_first_movement: Dict[Tuple[int, ...], bool]
    _turn: Color

    cardinals: List[Tuple[int, ...]]
    diagonals: List[Tuple[int, ...]]
    L: List[Tuple[int, ...]]
    basis: List[Tuple[int, ...]]

    def __init__(self, size: int, dimension: int, turn: Color = Color.WHITE):
        assert dimension >= 2
        self._size = size
        self._dimension = dimension
        self._turn = turn
        self._pieces = {}
        self._is_first_movement = {}
        self.compute_cardinals()
        self.compute_diagonals()
        self.compute_L()
        self.compute_basis()

    def __getitem__(self, indices):
        assert len(indices) == self.dimension
        pieces = self._pieces.copy()
        for i, j in enumerate(indices):
            assert type(j) is slice or type(j) is int
            outside = []
            if type(j) is slice:
                k = list(range(*j.indices(self.size)))
                for position in pieces.keys():
                    if position[i] not in k:
                        outside.append(position)
            else:
                for position in pieces.keys():
                    if position[i] != j:
                        outside.append(position)
            for i in outside:
                del pieces[i]
        return Board.from_pieces(self.size, self.dimension, pieces)

    @classmethod
    def from_pieces(cls, size: int, dimension: int, pieces: Dict[Tuple[int, ...], Tuple[Color, Type[Piece]]]):
        assert all(len(i) == dimension for i in pieces.keys())
        assert all(0 <= j < size for i in pieces.keys() for j in i)
        board = cls(size, dimension)
        for position, (color, piece) in pieces.items():
            board.add(piece, position, color)
        return board

    @classmethod
    def reduce_dimensionality(cls, board, preserve: Tuple[bool, ...]):
        dimension = sum(1 for i in preserve if i)
        reduced_board = cls(board.size, dimension)
        for position, color, piece in board.pieces:
            is_first_movement = board.is_first_movement(position)
            reduced_position = tuple(j for i, j in enumerate(position) if preserve[i])
            reduced_board.add(piece, reduced_position, color, is_first_movement)
        return reduced_board

    @property
    def size(self):
        return self._size

    @property
    def dimension(self):
        return self._dimension

    @property
    def turn(self):
        return self._turn

    @property
    def pieces(self) -> Iterator[Tuple[Tuple[int, ...], Tuple[Color, Type[Piece]]]]:
        for position, (color, piece) in self._pieces.items():
            yield position, color, piece

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

    def add(self, piece: Type[Piece], position: Tuple[int, ...], color: Color, is_first_movement: bool = True):
        """Adds a piece to the Board."""
        assert len(position) == self.dimension
        assert not self.contains(position)
        self._pieces[position] = (color, piece)
        self._is_first_movement[position] = is_first_movement

    def contains(self, position: Tuple[int, ...]) -> bool:
        """Checks if a piece is contained in the Board."""
        assert len(position) == self.dimension
        return position in self._pieces

    def get(self, position: Tuple[int, ...]) -> Tuple[Color, Type[Piece]]:
        """Returns the piece in the specified position."""
        assert len(position) == self.dimension
        return self._pieces[position]

    def move(self, initial_position: Tuple[int, ...], final_position: Tuple[int, ...]):
        """Moves a piece from one position to another; handles captures."""
        assert len(initial_position) == self.dimension
        assert len(final_position) == self.dimension
        assert self.contains(initial_position)
        assert self.get(initial_position)[0] == self.turn

        color, piece = self.get(initial_position)
        assert piece.valid_next(self, initial_position, final_position, color, self.is_first_movement(initial_position))

        if self.contains(final_position):
            self.remove(final_position)

        self.add(piece, final_position, color, False)
        self.remove(initial_position)
        self.next_turn()

    def remove(self, position: Tuple[int, ...]):
        """Removes a piece from the Board."""
        assert len(position) == self.dimension
        assert self.contains(position)
        del self._pieces[position]
        del self._is_first_movement[position]

    def replace(self, position: Tuple[int, ...], final_piece: Type[Piece], is_first_movement: bool = None):
        assert len(position) == self.dimension
        color, piece = self.get(position)
        is_first_movement = self.is_first_movement(position) if is_first_movement is None else is_first_movement
        self.remove(position)
        self.add(final_piece, position, color, is_first_movement)

    def promote(self, position: Tuple[int, ...], final_piece: Type[Piece]):
        """Promotes a piece."""
        color, initial_piece = self.get(position)
        assert initial_piece.is_promotion_available(self, position, color)
        assert final_piece in initial_piece.promotions
        self.replace(position, final_piece, False)

    def next_turn(self):
        self._turn = Color.BLACK if self._turn is Color.WHITE else Color.WHITE

    def is_first_movement(self, position: Tuple[int, ...]) -> bool:
        return self._is_first_movement[position]

    def in_bounds(self, position: Tuple[int, ...]) -> bool:
        """Checks if a piece is inside the Board bounds."""
        return all(0 <= i < self.size for i in position)

    def in_check(self, color: Color):
        raise NotImplementedError

    def in_checkmate(self, color: Color):
        raise NotImplementedError

    def in_stalemate(self):
        raise NotImplementedError
