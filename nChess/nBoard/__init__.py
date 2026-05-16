from itertools import combinations, product
from typing import TypeVar

IntegerVector = tuple[int, ...]
Color = TypeVar("Color")


class nBoard:
    dimension: int
    size: IntegerVector
    pieces: list["Piece"]
    occupied: dict[IntegerVector, "Piece"]
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
        self.occupied = {piece.position: piece for piece in self.pieces}

    @staticmethod
    def compute_cardinals(dimension: int) -> tuple[IntegerVector, ...]:
        return tuple(
            tuple(j if k == i else 0 for k in range(dimension))
            for j in (-1, 1)
            for i in range(dimension)
        )

    @staticmethod
    def compute_diagonals(dimension: int) -> tuple[IntegerVector, ...]:
        return tuple(
            tuple(
                signs[axes.index(axis)] if axis in axes else 0
                for axis in range(dimension)
            )
            for i in range(2, dimension + 1)
            for axes in combinations(range(dimension), i)
            for signs in product((-1, 1), repeat=i)
        )

    @staticmethod
    def compute_L(dimension: int) -> tuple[IntegerVector, ...]:
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
            [piece.clone() for piece in self.pieces]
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
        return position in self.occupied

    def add(self, piece_type, position: IntegerVector, color, *args, **kwargs):
        assert self.in_bounds(position)
        assert not self.contains(position)
        piece = piece_type(position, color, *args, board=self, **kwargs)
        self.pieces.append(piece)
        self.occupied[position] = piece

    def get(self, position: IntegerVector) -> "Piece":
        assert self.contains(position)
        return self.occupied[position]

    def remove(self, position: IntegerVector):
        assert self.contains(position)
        piece = self.get(position)
        self.pieces.pop(self.pieces.index(piece))
        self.occupied.pop(position)

    def is_king_position(self, position: IntegerVector) -> bool:
        return self.contains(position) and type(self.get(position)) is King

    def promote_if_available(self, position: IntegerVector):
        piece = self.get(position)
        if not piece.is_promotable():
            return

        promotion_type = next(
            (
                candidate
                for candidate in piece.promotions
                if candidate.__name__ == "Queen"
            ),
            piece.promotions[0],
        )
        promoted_piece = promotion_type(
            piece.position,
            piece.color,
            has_moved=True,
            board=self,
        )
        self.pieces[self.pieces.index(piece)] = promoted_piece
        self.occupied[position] = promoted_piece

    def move(self, move: "Move", force: bool = False):
        assert self.contains(move.initial_position)
        assert not self.move_in_conflict(move, force=force)
        assert not self.is_king_position(move.final_position)

        if not force:
            self.next_turn()

        moving_piece = self.get(move.initial_position)
        self.occupied.pop(move.initial_position)

        if self.contains(move.final_position):
            self.remove(move.final_position)

        moving_piece.move(move)
        self.occupied[move.final_position] = moving_piece
        self.promote_if_available(move.final_position)

    def find(self, piece_data: "PieceData") -> tuple[IntegerVector, ...]:
        return tuple(
            piece.position
            for piece in self.pieces
            if piece.matches(piece_data)
        )

    def move_in_conflict(self, move: "Move", force: bool = True, validate_check: bool = True) -> bool:
        if (
            not self.in_bounds(move.initial_position)
            or not self.in_bounds(move.final_position)
            or not self.contains(move.initial_position)
        ):
            return True

        moving_piece = self.get(move.initial_position)
        return not (
            (
                not self.contains(move.final_position)
                or self.get(move.final_position).color != moving_piece.color
            )
            and (
                moving_piece.color == self.current_turn()
                or force
            )
            and (
                not validate_check
                or not self.assume_move(move, force=True).in_check(moving_piece.color)
            )
        )

    def assume_move(self, move: "Move", force: bool = False) -> "nBoard":
        new_board = self.copy()

        assert new_board.contains(move.initial_position)

        if not force:
            new_board.next_turn()

        moving_piece = new_board.get(move.initial_position)
        new_board.occupied.pop(move.initial_position)

        if new_board.contains(move.final_position):
            new_board.remove(move.final_position)

        moving_piece.move(move)
        new_board.occupied[move.final_position] = moving_piece
        new_board.promote_if_available(move.final_position)
        
        return new_board

    def in_check(self, color: Color) -> bool:
        kings_positions = tuple(
            piece.position
            for piece in self.pieces
            if piece.color == color and type(piece) is King
        )

        for piece in self.pieces:
            if piece.color == color:
                continue
            if any(
                king_position == move.final_position
                for king_position in kings_positions
                for move in piece.all_moves()
            ):
                return True

        return False

    def in_checkmate(self, color: Color) -> bool:
        if not self.in_check(color):
            return False

        for piece in self.pieces:
            if piece.color != color:
                continue

            for move in piece.moves():
                new_board = self.assume_move(move)
                if not new_board.in_check(color):
                    return False

        return True

    def in_stalemate(self, color: Color) -> bool:
        if self.in_check(color):
            return False

        return all(len(piece.moves()) == 0 for piece in self.pieces if piece.color == color)


# Imported after nBoard is defined because Piece imports nBoard for shared types.
from nChess.Piece import Piece, Move, PieceData
from nChess.Piece.King import King
