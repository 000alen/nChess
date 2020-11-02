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

board.add(Knight, (2, 2), Color.WHITE)

board.add(Pawn, (1, 2), Color.BLACK)
board.add(Pawn, (0, 2), Color.BLACK)
board.add(Pawn, (2, 1), Color.BLACK)

print_2d_board(
    board,
    focus_position=(2, 2)
)
