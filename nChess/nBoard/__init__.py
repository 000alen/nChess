from typing import TypeVar
from copy import deepcopy

IntegerVector = tuple[int, ...]
Color = TypeVar("Color")


class nBoard:
    dimension: int
    size: IntegerVector
    pieces: list["Piece"]
    turn_number: int
    turn_order: tuple[Color, ...]

    cardinals: tuple[IntegerVector, ...]
    diagonals: tuple[IntegerVector, ...]
    L: tuple[IntegerVector, ...]
    basis: tuple[IntegerVector, ...]

    def __init__(
        self,
        dimension: int,
        size: IntegerVector,
        turn_number: int = 0,
        turn_order: tuple[Color, ...] = None,
        pieces: list["Piece"] = None
    ):
        if turn_order is None:
            turn_order = ()

        if pieces is None:
            pieces = []

        self.dimension = dimension
        self.size = size
        self.turn_number = turn_number
        self.turn_order = turn_order
        self.pieces = pieces

        self.cardinals = self.compute_cardinals(self.dimension)
        self.diagonals = self.compute_diagonals(self.dimension)
        self.L = self.compute_L(self.dimension)
        self.basis = self.compute_basis(self.dimension)

        for piece in self.pieces:
            piece.set_board(self)

    @staticmethod
    def compute_cardinals(dimension: int) -> tuple[IntegerVector, ...]:
        return tuple(
            tuple(j if k == i else 0 for k in range(dimension))
            for j in (-1, 1)
            for i in range(dimension)
        )

    @staticmethod
    def compute_diagonals(dimension: int) -> tuple[IntegerVector, ...]:
        from itertools import product
        return tuple(
            tuple((1, -1)[k] for k in j) + (0,) * (dimension - i)
            for i in range(2, dimension + 1)
            for j in product(range(2), repeat=i)
        )

    @staticmethod
    def compute_L(dimension: int) -> tuple[IntegerVector, ...]:
        from itertools import product
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
    def compute_basis(dimension: int) -> tuple[IntegerVector, ...]:
        return tuple(
            tuple(
                1 if i == j
                else 0
                for j in range(dimension)
            )
            for i in range(dimension)
        )

    def copy(self) -> "nBoard":
        return nBoard(
            self.dimension,
            self.size,
            self.turn_number,
            self.turn_order,
            deepcopy(self.pieces)
        )

    def in_bounds(self, position: IntegerVector) -> bool:
        return all(0 <= x < self.size[i] for i, x in enumerate(position))

    def current_turn(self) -> Color:
        if len(self.turn_order) == 0:
            return None
        return self.turn_order[self.turn_number % len(self.turn_order)]

    def next_turn(self):
        self.turn_number += 1

    def contains(self, position: IntegerVector) -> bool:
        for piece in self.pieces:
            if piece.position == position:
                return True

    def add(self, piece_type, position: IntegerVector, color, *args, **kwargs):
        assert not self.contains(position)
        self.pieces.append(piece_type(position, color, *args, board=self, **kwargs))

    def get(self, position: IntegerVector) -> "Piece":
        assert self.contains(position)
        for piece in self.pieces:
            if piece.position == position:
                return piece

    def remove(self, position: IntegerVector):
        assert self.contains(position)
        self.pieces.pop(self.get(position))

    def move(self, move: "Move", force: bool = False):
        assert self.contains(move.initial_position)
        assert not self.move_in_conflict(move, force=force)

        if not force:
            self.next_turn()

        if self.contains(move.final_position):
            self.remove(move.final_position)

        self.get(move.initial_position).move(move)

    def find(self, piece_data: "PieceData") -> tuple[IntegerVector]:
        return tuple(
            piece.position
            for piece in self.pieces
            if piece.matches(piece_data)
        )

    def move_in_conflict(self, move: "Move", force: bool = True) -> bool:
        return not (
            self.in_bounds(move.final_position)
            and (
                not self.contains(move.final_position)
                or self.get(move.final_position).color != self.get(move.initial_position).color
            )
            and (
                self.get(move.initial_position).color == self.current_turn()
                or force
            ) and (
                not self.assume_move(move).in_check(
                    self.get(move.initial_position).color)
            )
        )

    def assume_move(self, move: "Move", force: bool = False) -> "nBoard":
        new_board = self.copy()

        assert new_board.contains(move.initial_position)

        if not force:
            new_board.next_turn()

        if new_board.contains(move.final_position):
            new_board.remove(move.final_position)

        new_board.get(move.initial_position).move(move)
        
        return new_board

    def in_check(self, color: Color) -> bool:
        from nChess.Piece.King import King
        kings_positions = self.find(PieceData(color, King))

        for piece in self.pieces:
            if piece.color == color:
                continue
            if any(any(king_position == move.final_position for move in piece.piece.moves(self, piece.position)) for king_position in kings_positions):
                return True

        return False

    def in_checkmate(self, color: Color) -> bool:
        if not self.in_check(color):
            return False

        for piece in self.pieces:
            if piece.color != color:
                continue

            for move in piece.moves(self):
                new_board = self.assume_move(move)
                if not new_board.in_check(color):
                    return False

        return True

    def in_stalemate(self, color: Color) -> bool:
        if self.in_check(color):
            return False

        return all(len(piece.moves(self)) == 0 for piece in self.pieces if piece.color == color)


from nChess.Piece import Piece, Move, PieceData
