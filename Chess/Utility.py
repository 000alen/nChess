from typing import Tuple

from Chess.Board import Board, Color
from Chess.Piece.Bishop import Bishop
from Chess.Piece.King import King
from Chess.Piece.Knight import Knight
from Chess.Piece.Pawn import Pawn
from Chess.Piece.Queen import Queen
from Chess.Piece.Rook import Rook

SymbolRepresentation = {
    (Color.WHITE, Bishop): "♗",
    (Color.WHITE, King): "♔",
    (Color.WHITE, Knight): "♘",
    (Color.WHITE, Pawn): "♙",
    (Color.WHITE, Queen): "♕",
    (Color.WHITE, Rook): "♖",

    (Color.BLACK, Bishop): "♝",
    (Color.BLACK, King): "♚",
    (Color.BLACK, Knight): "♞",
    (Color.BLACK, Pawn): "♟",
    (Color.BLACK, Queen): "♛",
    (Color.BLACK, Rook): "♜"
}

LetterRepresentation = {
    (Color.WHITE, Bishop): "B",
    (Color.WHITE, King): "K",
    (Color.WHITE, Knight): "N",
    (Color.WHITE, Pawn): "P",
    (Color.WHITE, Queen): "Q",
    (Color.WHITE, Rook): "R",

    (Color.BLACK, Bishop): "b",
    (Color.BLACK, King): "k",
    (Color.BLACK, Knight): "n",
    (Color.BLACK, Pawn): "p",
    (Color.BLACK, Queen): "q",
    (Color.BLACK, Rook): "r"
}


def print_2d_board(
        board: Board,
        width: int = 1,
        empty: str = ".",
        focus: str = "x",
        representation=None,
        focus_position: Tuple[int, ...] = None
):
    assert board.dimension == 2
    representation = LetterRepresentation if representation is None else representation

    if focus_position is not None:
        assert board.contains(focus_position)
        focus_color, focus_piece = board.get(focus_position)
        focus_next = focus_piece.next(board, focus_position, focus_color, board.is_first_movement(focus_position))
    else:
        focus_next = []

    for i in range(board.size):
        for j in range(board.size):
            print(
                "{0:{width}}".format(
                    focus if (i, j) in focus_next
                    else representation[board.get((i, j))] if board.contains((i, j))
                    else empty,
                    width=width
                ),
                end=" "
            )
        print()
