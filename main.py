from nChess.Board import *
from nChess.Board.Classic import *
from nChess.Piece import *
from nChess.Piece.Bishop import *
from nChess.Piece.King import *
from nChess.Piece.Knight import *
from nChess.Piece.Pawn import *
from nChess.Piece.Queen import *
from nChess.Piece.Rook import *
from nChess.Engine import *
from nChess.utils import *

def print_2d_board(board: Classic):
    for i in range(board.size[0]):
        for j in range(board.size[1]):
            if board.contains((i, j)):
                print(to_char(board.get((i, j))))

# board = Classic()
# board.move(Move((0, 1), (0, 2)))


board = Board(2, (4, 4))
board.add(Queen, (0, 0), ClassicColor.white)
board.add(Pawn, (3, 3), ClassicColor.black)

for piece in board.pieces:
    print(piece)
    
print(len(board.find(PieceData(ClassicColor.white, Queen))), len(board.find(PieceData(ClassicColor.black, Queen))))


print(delta_material(board, Queen, ClassicColor.white, ClassicColor.white))
