from Chess.Board import Board, Color
from Chess.Board.TurnBoard import TurnBoard
from Chess.Board.ClassicBoard import ClassicBoard
from Chess.Piece.Bishop import Bishop
from Chess.Piece.King import King
from Chess.Piece.Knight import Knight
from Chess.Piece.Pawn import Pawn
from Chess.Piece.Queen import Queen
from Chess.Piece.Rook import Rook
from Chess.Utility import SymbolRepresentation, LetterRepresentation, print_2d_board

board = Board(5, 2)

pawn_position = (0, 0)
board.add(Pawn, pawn_position, Color.WHITE)

while True:
    print_2d_board(
        board,
        focus_position=pawn_position
    )

    i, j = (int(_) for _ in input().split())
    p, q = (int(_) for _ in input().split())

    board.move((i, j), (p, q))
    pawn_position = (p, q)
