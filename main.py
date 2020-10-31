from Chess.Board import Board, Color
from Chess.Piece.Bishop import Bishop
from Chess.Piece.King import King
from Chess.Piece.Knight import Knight
from Chess.Piece.Pawn import Pawn
from Chess.Piece.Queen import Queen
from Chess.Piece.Rook import Rook

board = Board(4, 3)
board.add(Queen, (0, 0, 0), Color.WHITE)
board.add(Queen, (3, 3, 3), Color.BLACK)

print(board.board)

board.move((0, 0, 0), (3, 3, 3))

print(board.board)
