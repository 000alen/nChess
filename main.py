from Chess.Board import Board, Color
from Chess.Board.TurnBoard import TurnBoard
from Chess.Board.ClassicBoard import ClassicBoard
from Chess.Piece.Bishop import Bishop
from Chess.Piece.King import King
from Chess.Piece.Knight import Knight
from Chess.Piece.Pawn import Pawn
from Chess.Piece.Queen import Queen
from Chess.Piece.Rook import Rook
from Chess.Utility import Representation, print_2d_board

board = ClassicBoard()
print_2d_board(board)
