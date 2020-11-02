from Chess.Board import Board, Color
from Chess.Piece.Bishop import Bishop
from Chess.Piece.King import King
from Chess.Piece.Knight import Knight
from Chess.Piece.Pawn import Pawn
from Chess.Piece.Queen import Queen
from Chess.Piece.Rook import Rook

Representation = {
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


def print_2d_board(board: Board, width: int = 1, empty: str = "x"):
    assert board.dimension == 2
    for i in range(board.size):
        for j in range(board.size):
            print(
                "{0:{width}}".format(
                    Representation[board.get((i, j))]
                    if board.contains((i, j))
                    else empty,
                    width=width
                ),
                end=" "
            )
        print()
