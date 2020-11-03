from enum import Enum, auto
from typing import Dict, Tuple, Type, Iterator, TypeVar, Union, NamedTuple

from Chess.Exception import InvalidBoardSize, InvalidBoardDimension, InvalidBoardTurnOrder, UnexpectedPosition, SelectionOverlapping
from Chess.Piece import Piece

_Piece = Type[Piece]
_Position = Tuple[int, ...]
_Color = TypeVar("_Color")


class _PieceValue(NamedTuple):
    color: _Color
    piece: _Piece


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
    _pieces: Dict[_Position, Tuple[_Color, _Piece]]
    _is_first_movement: Dict[_Position, bool]
    _turn_number: int
    _turn_order: Tuple[_Color]

    _cardinals: Tuple[_Position]
    _diagonals: Tuple[_Position]
    _L: Tuple[_Position]
    _basis: Tuple[_Position]

    def __init__(
            self,
            size: int,
            dimension: int,
            turn_number: int = 1,
            turn_order: Tuple[_Color] = (Color.WHITE, Color.BLACK)
    ):
        if size < 1:
            raise InvalidBoardSize(size)
        if dimension < 1:
            raise InvalidBoardDimension(dimension)
        if turn_number < 1:
            raise ValueError("Turn number must be at least 1.")
        if len(turn_order) < 1:
            raise InvalidBoardTurnOrder(turn_order)

        self._size = size
        self._dimension = dimension
        self._pieces = {}
        self._is_first_movement = {}
        self._turn_number = turn_number
        self._turn_order = turn_order
        self._cardinals = self._compute_cardinals()
        self._diagonals = self._compute_diagonals()
        self._L = self._compute_L()
        self._basis = self._compute_basis()

    def __getitem__(self, indices):
        return self.slice(indices)

    def _compute_cardinals(self) -> Tuple[_Position]:
        return tuple(
            tuple(j if k == i else 0 for k in range(self.dimension))
            for j in (-1, 1)
            for i in range(self.dimension)
        )

    def _compute_diagonals(self) -> Tuple[_Position]:
        from itertools import product
        # noinspection PyTypeChecker
        return tuple(
            tuple((1, -1)[k] for k in J) if i == self.dimension
            else tuple((-1, 1)[k] for k in J) + (0,) * (self.dimension - i)
            for i in range(2, self.dimension + 1)
            for J in product(range(2), repeat=i)
        )

    def _compute_L(self) -> Tuple[_Position]:
        from itertools import product
        # noinspection PyTypeChecker
        return tuple(
            tuple(
                2 * p if k == i
                else q if k == j
                else 0
                for k in range(self.dimension)
            )
            for i in range(self.dimension)
            for j in range(self.dimension)
            for p, q in product((-1, 1), repeat=2)
            if i != j
        )

    def _compute_basis(self) -> Tuple[_Position]:
        return tuple(
            tuple(
                1 if i == j
                else 0
                for j in range(self.dimension)
            )
            for i in range(self.dimension)
        )

    @classmethod
    def from_pieces(
            cls,
            size: int,
            dimension: int,
            pieces: Dict[_Position, Tuple[Color, _Piece]],
            is_first_movement: Dict[_Position, bool] = None,
            turn_number: int = 1,
            turn_order: Tuple[_Color] = (Color.WHITE, Color.BLACK)
    ):
        if is_first_movement is None:
            is_first_movement = {}
        board = cls(size, dimension, turn_number, turn_order)
        for position, (color, piece) in pieces.items():
            board.add(piece, position, color, is_first_movement.get(position, True))
        return board

    @property
    def cardinals(self):
        return self._cardinals

    @property
    def diagonals(self):
        return self._diagonals

    # noinspection PyPropertyDefinition
    @property
    def L(self):
        return self._L

    @property
    def basis(self):
        return self._basis

    @property
    def size(self) -> int:
        return self._size

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def turn(self) -> _Color:
        return self._turn_order[(self._turn_number - 1) % len(self._turn_order)]

    @property
    def turn_number(self) -> int:
        return self._turn_number

    @property
    def turn_order(self) -> Tuple[_Color]:
        return self._turn_order

    @property
    def pieces(self) -> Iterator[Tuple[_Position, Color, _Piece]]:
        for position, (color, piece) in self._pieces.items():
            yield position, color, piece

    def add(
            self,
            piece: _Piece,
            position: _Position,
            color: _Color,
            is_first_movement: bool = True
    ):
        """Adds a piece to the Board."""
        assert self.in_bounds(position)
        assert not self.contains(position)
        self._pieces[position] = (color, piece)
        self._is_first_movement[position] = is_first_movement

    def contains(
            self,
            position: _Position
    ) -> bool:
        """Checks if a piece is contained in the Board."""
        assert self.in_bounds(position)
        return position in self._pieces

    def get(
            self,
            position: _Position
    ) -> _PieceValue:
        """Returns the piece in the specified position."""
        assert self.contains(position)
        return _PieceValue(*self._pieces[position])

    def move(
            self,
            initial_position: _Position,
            final_position: _Position,
            use_turn: bool = True
    ):
        """Moves a piece from one position to another; handles captures."""
        assert self.contains(initial_position)
        assert self.in_bounds(final_position)

        color, piece = self.get(initial_position)
        if use_turn:
            assert color is self.turn
            self.next_turn()

        assert piece.valid_next(self, initial_position, final_position)
        if self.contains(final_position):
            self.remove(final_position)

        self.add(piece, final_position, color, False)
        self.remove(initial_position)

    def remove(
            self,
            position: _Position
    ):
        """Removes a piece from the Board."""
        assert self.contains(position)
        del self._pieces[position]
        del self._is_first_movement[position]

    def replace(
            self,
            position: _Position,
            final_piece: _Piece,
            is_first_movement: bool = None
    ):
        assert len(position) == self.dimension
        color, piece = self.get(position)
        self.remove(position)
        self.add(
            final_piece,
            position,
            color,
            self.is_first_movement(position) if is_first_movement is None
            else is_first_movement
        )

    def promote(
            self,
            position: _Position,
            final_piece: _Piece
    ):
        """Promotes a piece."""
        color, initial_piece = self.get(position)
        assert initial_piece.is_promotion_available(self, position)
        assert final_piece in initial_piece.promotions
        self.replace(position, final_piece, False)

    def next_turn(self):
        self._turn_number += 1

    def slice(
            self,
            indices: Tuple[Union[slice, int], ...]
    ) -> "Board":
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
            for p in outside:
                del pieces[p]
        return Board.from_pieces(
            self.size,
            self.dimension,
            pieces,
            turn_number=self.turn_number,
            turn_order=self.turn_order
        )

    def select(
            self,
            selection: Tuple[bool, ...]
    ) -> "Board":
        board = Board(
            self.size,
            sum(1 for i in selection if i),
            turn_number=self.turn_number,
            turn_order=self.turn_order
        )
        for position, color, piece in self.pieces:
            new_position = tuple(j for i, j in enumerate(position) if selection[i])
            if board.contains(new_position):
                raise SelectionOverlapping(position, new_position, self.dimension, sum(1 for i in selection if i))
            board.add(
                piece,
                new_position,
                color,
                self.is_first_movement(position)
            )
        return board

    def is_first_movement(
            self,
            position: _Position
    ) -> bool:
        return self._is_first_movement[position]

    def in_bounds(
            self,
            position: _Position
    ) -> bool:
        """Checks if a piece is inside the Board bounds."""
        if len(position) != self.dimension:
            raise UnexpectedPosition(position, self.size, self.dimension)
        return all(0 <= i < self.size for i in position)

    def in_check(self):
        raise NotImplementedError

    def in_checkmate(self):
        raise NotImplementedError

    def in_stalemate(self):
        raise NotImplementedError

    def slice_in_place(self):
        raise NotImplementedError

    def select_in_place(self):
        raise NotImplementedError
