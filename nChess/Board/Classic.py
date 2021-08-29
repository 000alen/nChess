from nChess.Piece import Piece
from nChess.Board import Board, Color
from nChess.Piece.Bishop import Bishop
from nChess.Piece.King import King
from nChess.Piece.Knight import Knight
from nChess.Piece.Pawn import Pawn
from nChess.Piece.Queen import Queen
from nChess.Piece.Rook import Rook
from typing import Generic
from enum import Enum, auto
from copy import deepcopy


class ClassicColor(Generic[Color], Enum):
    white = auto()
    black = auto()


TurnOrder = (ClassicColor.white, ClassicColor.black)

WhitePawns = [Pawn((x, 1), ClassicColor.white) for x in range(8)]
WhiteRoyalty = [
    Rook((0, 0), ClassicColor.white),
    Knight((1, 0), ClassicColor.white),
    Bishop((2, 0), ClassicColor.white),
    King((3, 0), ClassicColor.white),
    Queen((4, 0), ClassicColor.white),
    Bishop((5, 0), ClassicColor.white),
    Knight((6, 0), ClassicColor.white),
    Rook((7, 0), ClassicColor.white)
]

BlackPawns = [Pawn((x, 6), ClassicColor.black) for x in range(8)]
BlackRoyalty = [
    Rook((0, 7), ClassicColor.black),
    Knight((1, 7), ClassicColor.black),
    Bishop((2, 7), ClassicColor.black),
    King((3, 7), ClassicColor.black),
    Queen((4, 7), ClassicColor.black),
    Bishop((5, 7), ClassicColor.black),
    Knight((6, 7), ClassicColor.black),
    Rook((7, 7), ClassicColor.black)
]

Pieces = [
    *WhitePawns,
    *WhiteRoyalty,
    *BlackPawns,
    *BlackRoyalty
]


class Classic(Board):
    def __init__(self):
        super().__init__(2, (8, 8), 0, TurnOrder, deepcopy(Pieces))
