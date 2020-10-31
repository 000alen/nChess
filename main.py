from Chess.Board import Board, Color
from Chess.Piece.Bishop import Bishop
from Chess.Piece.King import King
from Chess.Piece.Knight import Knight
from Chess.Piece.Pawn import Pawn
from Chess.Piece.Queen import Queen
from Chess.Piece.Rook import Rook

board = Board(4, 2)
board.add(Pawn, (3, 3), Color.WHITE)

print(board.board)

board.promote((3, 3), Queen)

print(board.board)
