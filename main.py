from Chess.Board import Board, Color
from Chess.Piece.Pawn import Pawn
from Chess.Utility import print_2d_board

board = Board(4, 3)
board.add(Pawn, (0, 0, 0), Color.WHITE)
board.add(Pawn, (1, 0, 1), Color.WHITE)
board.add(Pawn, (2, 0, 2), Color.WHITE)
board.add(Pawn, (3, 0, 3), Color.WHITE)

board.add(Pawn, (0, 3, 0), Color.BLACK)
board.add(Pawn, (1, 3, 1), Color.BLACK)
board.add(Pawn, (2, 3, 2), Color.BLACK)
board.add(Pawn, (3, 3, 3), Color.BLACK)

print_2d_board(
    Board.reduce_dimensionality(board[:, :, :2], (True, True, False))
)
