from Chess.Piece.King import King
from Chess.Piece.Queen import Queen
from Chess.Board import Board, Color
from Chess.Piece.Pawn import Pawn
from Chess.Utility import print_2d_board

board = Board(4, 2)
board.add(Queen, (2, 0), Color.WHITE)
board.add(Queen, (3, 0), Color.WHITE)
board.add(King, (3, 3), Color.BLACK)

print_2d_board(board)
print(f"in check: {board.in_check(Color.BLACK)}")
print(f"in checkmate: {board.in_checkmate(Color.BLACK)}")
print(f"in stalemate: {board.in_stalemate(Color.BLACK)}")
print(f"movements for Black King: {King.movements(board, (3, 3))}")
