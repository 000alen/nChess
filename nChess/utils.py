from nChess.Board.Classic import Classic, ClassicColor
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

PNG = {
    (ClassicColor.white, King): "assets/white_king.png",
    (ClassicColor.white, Queen): "assets/white_queen.png",
    (ClassicColor.white, Rook): "assets/white_rook.png",
    (ClassicColor.white, Bishop): "assets/white_bishop.png",
    (ClassicColor.white, Knight): "assets/white_knight.png",
    (ClassicColor.white, Pawn): "assets/white_pawn.png",
    (ClassicColor.black, King): "assets/black_king.png",
    (ClassicColor.black, Queen): "assets/black_queen.png",
    (ClassicColor.black, Rook): "assets/black_rook.png",
    (ClassicColor.black, Bishop): "assets/black_bishop.png",
    (ClassicColor.black, Knight): "assets/black_knight.png",
    (ClassicColor.black, Pawn): "assets/black_pawn.png"
}

WhiteKing = (ClassicColor.white, King)
WhiteQueen = (ClassicColor.white, Queen)
WhiteRook = (ClassicColor.white, Rook)
WhiteBishop = (ClassicColor.white, Bishop)
WhiteKnight = (ClassicColor.white, Knight)
WhitePawn = (ClassicColor.white, Pawn)

BlackKing = (ClassicColor.black, King)
BlackQueen = (ClassicColor.black, Queen)
BlackRook = (ClassicColor.black, Rook)
BlackBishop = (ClassicColor.black, Bishop)
BlackKnight = (ClassicColor.black, Knight)
BlackPawn = (ClassicColor.black, Pawn)


def to_ASCII(piece: Piece) -> str:
    return ASCII[(piece.color, type(piece))]


def to_char(piece: Piece) -> str:
    return CHAR[(piece.color, type(piece))]


def to_PNG(piece: Piece) -> str:
    return PNG[(piece.color, type(piece))]
