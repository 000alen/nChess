from nChess.nBoard import nBoard
from nChess.nBoard.Classic import ClassicColor
from nChess.Piece.Pawn import Pawn
from nChess.GUI.nChessApp import nChessApp
from kivy.core.window import Window

Window.size = (600, 600)

n_board = nBoard(4, (4, 4, 4, 4))    
n_board.add(Pawn, (0, 1, 0, 0), ClassicColor.white)
n_board.add(Pawn, (1, 1, 0, 0), ClassicColor.white)
n_board.add(Pawn, (2, 1, 0, 0), ClassicColor.white)
n_board.add(Pawn, (3, 1, 0, 0), ClassicColor.white)

# n_board.add(Rook, (0, 0, 0, 0), ClassicColor.white)
# n_board.add(Queen, (1, 0, 0, 0), ClassicColor.white)
# n_board.add(King, (2, 0, 0, 0), ClassicColor.white)
# n_board.add(Rook, (3, 0, 0, 0), ClassicColor.white)
# n_board.add(Pawn, (0, 2, 0, 0), ClassicColor.black)
# n_board.add(Pawn, (1, 2, 0, 0), ClassicColor.black)
# n_board.add(Pawn, (2, 2, 0, 0), ClassicColor.black)
# n_board.add(Pawn, (3, 2, 0, 0), ClassicColor.black)
# n_board.add(Rook, (0, 3, 0, 0), ClassicColor.black)
# n_board.add(King, (1, 3, 0, 0), ClassicColor.black)
# n_board.add(Queen, (2, 3, 0, 0), ClassicColor.black)
# n_board.add(Rook, (3, 3, 0, 0), ClassicColor.black)

n_chess_app = nChessApp(n_board=n_board)
n_chess_app.run()
