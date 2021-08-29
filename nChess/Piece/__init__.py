from abc import ABC
from dataclasses import dataclass
from typing import Type
from abc import ABC


@dataclass(frozen=True)
class Move:
    initial_position: "IntegerVector"
    final_position: "IntegerVector"


@dataclass(frozen=True)
class PieceData:
    color: "Color"
    piece_type: Type["Piece"]
    position: "IntegerVector" = None
    has_moved: bool = None


class Piece(ABC):
    promotions: tuple[Type["Piece"]]

    def __init__(self, position, color, has_moved=False, board=None) -> None:
        super().__init__()
        self.position = position
        self.color = color
        self.has_moved = has_moved
        self.board = board

    def set_board(self, board):
        self.board = board

    def move(self, move: "Move") -> None:
        assert self.position == move.initial_position
        self.position = move.final_position

    def matches(self, piece_data: "PieceData") -> bool:
        return (
            self.color == piece_data.color
            and type(self) is piece_data.piece_type
            and (
                piece_data.position is not None
                and self.position == piece_data.position
            )
            and (
                piece_data.has_moved is not None
                and self.has_moved == piece_data.has_moved
            )
        )

    def is_promotable(self) -> bool:
        raise NotImplementedError

    def ad_nauseam(self, offsets: tuple["IntegerVector"], maximum_magnitude: int) -> tuple["Move", ...]:
        moves = []
        for offset in offsets:
            for magnitude in range(1, maximum_magnitude + 1):
                move = Move(
                    self.position, 
                    tuple(self.position[i] + (offset[i] * magnitude) for i in range(self.board.dimension))
                )
                if not self.board.move_in_conflict(move):
                    moves.append(move)
                else:
                    break
        return moves

    def all_moves(self) -> tuple["Move", ...]:
        raise NotImplementedError

    def legal_moves(self) -> tuple["Move", ...]:
        return tuple(
            move
            for move in self.all_moves()
            if not self.board.assume_move(move).in_check(self.color)
        )

    def moves(self) -> tuple["Move", ...]:
        return self.legal_moves()


# XXX
from nChess.Board import Board, IntegerVector, Color
