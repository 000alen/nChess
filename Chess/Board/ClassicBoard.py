from Chess.Board import Color
from Chess.Board.TurnBoard import TurnBoard
from Chess.Piece.Bishop import Bishop
from Chess.Piece.King import King
from Chess.Piece.Knight import Knight
from Chess.Piece.Pawn import Pawn
from Chess.Piece.Queen import Queen
from Chess.Piece.Rook import Rook

Pawns = (Pawn for _ in range(8))
Royalty = (Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook)


class ClassicBoard(TurnBoard):
    def __init__(self):
        super().__init__(8, 2)

        for j, piece in enumerate(Pawns):
            self.add(piece, (1, j), Color.WHITE)
            self.add(piece, (6, j), Color.BLACK)

        for j, piece in enumerate(Royalty):
            self.add(piece, (0, j), Color.WHITE)

        for j, piece in enumerate(reversed(Royalty)):
            self.add(piece, (7, j), Color.BLACK)
