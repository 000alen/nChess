from Chess.Piece.King import King
from enum import Enum, auto
from typing import Dict, Tuple, Type, Iterator, TypeVar, Union, NamedTuple

from Chess.Exception import InvalidBoardSize, InvalidBoardDimension, InvalidBoardTurnOrder, InvalidPosition, SelectionOverlapping
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
        self._cardinals = Board._compute_cardinals(self._dimension)
        self._diagonals = Board._compute_diagonals(self._dimension)
        self._L = Board._compute_L(self._dimension)
        self._basis = Board._compute_basis(self._dimension)

    @staticmethod
    def _compute_cardinals(dimension: int) -> Tuple[_Position]:
        # noinspection PyTypeChecker
        return tuple(
            tuple(j if k == i else 0 for k in range(dimension))
            for j in (-1, 1)
            for i in range(dimension)
        )

    @staticmethod
    def _compute_diagonals(dimension: int) -> Tuple[_Position]:
        from itertools import product
        # noinspection PyTypeChecker
        return tuple(
            tuple((1, -1)[k] for k in j) + (0,) * (dimension - i)
            for i in range(2, dimension + 1)
            for j in product(range(2), repeat=i)
        )

    @staticmethod
    def _compute_L(dimension: int) -> Tuple[_Position]:
        from itertools import product
        # noinspection PyTypeChecker
        return tuple(
            tuple(
                2 * p if k == i
                else q if k == j
                else 0
                for k in range(dimension)
            )
            for i in range(dimension)
            for j in range(dimension)
            for p, q in product((-1, 1), repeat=2)
            if i != j
        )

    @staticmethod
    def _compute_basis(dimension: int) -> Tuple[_Position]:
        return tuple(
            tuple(
                1 if i == j
                else 0
                for j in range(dimension)
            )
            for i in range(dimension)
        )

    def copy(self) -> "Board":
        board = Board(self.size, self.dimension,
                      self.turn_number, self.turn_order)
        board._pieces = self._pieces.copy()
        board._is_first_movement = self._is_first_movement.copy()
        return board

    def assumption_movement(
        self,
        initial_position: _Position,
        final_position: _Position,
        use_turn: bool = False
    ) -> "Board":
        board = self.copy()
        board.move(initial_position, final_position, use_turn, True)
        return board

    @property
    def cardinals(self) -> Tuple[_Position]:
        return self._cardinals

    @property
    def diagonals(self) -> Tuple[_Position]:
        return self._diagonals

    # noinspection PyPropertyDefinition
    @property
    def L(self) -> Tuple[_Position]:
        return self._L

    @property
    def basis(self) -> Tuple[_Position]:
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
    def pieces(self) -> Iterator[Tuple[_Position, _Color, _Piece]]:
        for position, (color, piece) in self._pieces.items():
            yield position, _PieceValue(color, piece)

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
            use_turn: bool = True,
            force: bool = False
    ):
        """Moves a piece from one position to another; handles captures."""
        assert self.contains(initial_position)
        assert self.in_bounds(final_position)

        color, piece = self.get(initial_position)
        if use_turn:
            assert color is self.turn
            self.next_turn()

        if not force:
            assert final_position in piece.movements(self, initial_position)

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
        assert self.contains(position)
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
        assert self.contains(position)
        color, initial_piece = self.get(position)
        assert initial_piece.is_promotion_available(self, position)
        assert final_piece in initial_piece.promotions
        self.replace(position, final_piece, False)

    def next_turn(self):
        self._turn_number += 1

    def is_first_movement(
            self,
            position: _Position
    ) -> bool:
        assert self.contains(position)
        return self._is_first_movement[position]

    def in_bounds(
            self,
            position: _Position
    ) -> bool:
        """Checks if a piece is inside the Board bounds."""
        if len(position) != self.dimension:
            raise InvalidPosition(position, self.size, self.dimension)
        return all(0 <= i < self.size for i in position)

    def no_conflict(
            self,
            initial_position: _Position,
            final_position: _Position
    ):
        """Checks if a given position doesn't cause a conflict."""
        return (
            self.in_bounds(final_position)
            and (
                not self.contains(final_position)
                or self.get(initial_position).color != self.get(final_position).color
            )
        )

    def find(
        self,
        piece: _Piece = None,
        color: _Color = None
    ) -> Tuple[_Position]:
        assert piece is not None or color is not None
        matches = []
        for current_position, (current_color, current_piece) in self.pieces:
            if piece is not None and current_piece != piece:
                continue
            if color is not None and current_color is not color:
                continue
            matches.append(current_position)
        return tuple(matches)

    def in_check(self, color: _Color, position: _Position = None) -> bool:
        king_positions = self.find(
            King, color) if position is None else [position]

        attacking_colors = set(self.turn_order) - {color}
        attacking_positions = []
        for attacking_color in attacking_colors:
            attacking_positions.extend(self.find(color=attacking_color))

        for attacking_position in attacking_positions:
            attacking_color, attacking_piece = self.get(attacking_position)
            for king_position in king_positions:
                if king_position in attacking_piece.movements(self, attacking_position):
                    return True
        return False

    def in_checkmate(self, color: _Color, position: _Position = None) -> bool:
        king_positions = self.find(
            King, color) if position is None else [position]

        defending_colors = {color}
        defending_positions = []
        for defending_color in defending_colors:
            defending_positions.extend(self.find(color=defending_color))

        attacking_colors = set(self.turn_order) - {color}
        attacking_positions = []
        for attacking_color in attacking_colors:
            attacking_positions.extend(self.find(color=attacking_color))

        for king_position in king_positions:
            in_check = self.in_check(color, king_position)
            in_stalemate = all(
                self.assumption_movement(king_position, unfiltered_movement).in_check(
                    color, unfiltered_movement)
                for unfiltered_movement in King._unfiltered_movements(self, king_position)
            )
            has_defense = None
            for defending_position in defending_positions:
                defending_color, defending_piece = self.get(defending_position)
                if defending_piece == King:
                    continue
                has_defense = any(
                    not self.assumption_movement(
                        defending_position, unfiltered_movement).in_check(color, king_position)
                    for unfiltered_movement in defending_piece._unfiltered_movements(self, defending_position)
                )
            if in_check and in_stalemate and not has_defense:
                return True
        return False

    def in_stalemate(self, color: _Color, position: _Position = None) -> bool:
        king_positions = self.find(
            King, color) if position is None else [position]

        defending_colors = {color}
        defending_positions = []
        for defending_color in defending_colors:
            defending_positions.extend(self.find(color=defending_color))

        attacking_colors = set(self.turn_order) - {color}
        attacking_positions = []
        for attacking_color in attacking_colors:
            attacking_positions.extend(self.find(color=attacking_color))

        for king_position in king_positions:
            in_check = self.in_check(color, king_position)
            in_stalemate = all(
                self.assumption_movement(king_position, unfiltered_movement).in_check(
                    color, unfiltered_movement)
                for unfiltered_movement in King._unfiltered_movements(self, king_position)
            )
            has_defense = None
            for defending_position in defending_positions:
                defending_color, defending_piece = self.get(defending_position)
                if defending_piece == King:
                    continue
                has_defense = any(
                    not self.assumption_movement(
                        defending_position, unfiltered_movement).in_check(color, king_position)
                    for unfiltered_movement in defending_piece._unfiltered_movements(self, defending_position)
                )
            if in_stalemate and not in_check and not has_defense:
                return True
        return False
