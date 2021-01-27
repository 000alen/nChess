from Chess.Piece.King import King
from Chess.Piece.Queen import Queen
from Chess.Board import Board, Color
from Chess.Piece.Pawn import Pawn
from Chess.Utility import print_2d_board

board = Board(4, 2)
board.add(Pawn, (0, 0), Color.WHITE)
board.add(Pawn, (1, 1), Color.BLACK)

print_2d_board(board)
print(f"White Pawn movements: {Pawn.movements(board, (0, 0))}")
print(f"Black Pawn movements: {Pawn.movements(board, (1, 1))}")
