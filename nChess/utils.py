from nChess.Board.Classic import ClassicColor
from nChess.Piece import Piece
from nChess.Piece.Bishop import Bishop
from nChess.Piece.King import King
from nChess.Piece.Knight import Knight
from nChess.Piece.Pawn import Pawn
from nChess.Piece.Queen import Queen
from nChess.Piece.Rook import Rook


ASCII = {
    (ClassicColor.white, King): "♔",
    (ClassicColor.white, Queen): "♕",
    (ClassicColor.white, Rook): "♖",
    (ClassicColor.white, Bishop): "♗",
    (ClassicColor.white, Knight): "♘",
    (ClassicColor.white, Pawn): "♙",
    (ClassicColor.black, King): "♚",
    (ClassicColor.black, Queen): "♛",
    (ClassicColor.black, Rook): "♜",
    (ClassicColor.black, Bishop): "♝",
    (ClassicColor.black, Knight): "♞",
    (ClassicColor.black, Pawn): "♟︎",
}

CHAR = {
    (ClassicColor.white, King): "K",
    (ClassicColor.white, Queen): "Q",
    (ClassicColor.white, Rook): "R",
    (ClassicColor.white, Bishop): "B",
    (ClassicColor.white, Knight): "N",
    (ClassicColor.white, Pawn): "P",
    (ClassicColor.black, King): "k",
    (ClassicColor.black, Queen): "q",
    (ClassicColor.black, Rook): "r",
    (ClassicColor.black, Bishop): "b",
    (ClassicColor.black, Knight): "n",
    (ClassicColor.black, Pawn): "p",
}


def to_ASCII(piece: Piece) -> str:
    return ASCII[(piece.color, type(piece))]


def to_char(piece: Piece) -> str:
    return CHAR[(piece.color, type(piece))]
