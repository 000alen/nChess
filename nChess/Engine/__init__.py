from nChess.Board import Board, Color
from nChess.Board.Classic import Classic, ClassicColor
from nChess.Piece import PieceData
from nChess.Piece.Bishop import Bishop
from nChess.Piece.King import King
from nChess.Piece.Knight import Knight
from nChess.Piece.Pawn import Pawn
from nChess.Piece.Queen import Queen
from nChess.Piece.Rook import Rook


def doubled_pawns(board: Board, color: Color) -> int:
    x = 0
    for i, i_position in enumerate(board.find(PieceData(color, Pawn))):
        for j, j_position in enumerate(board.find(PieceData(color, Pawn))):
            if i == j:
                continue
            x += 1 if any(i_position[k] == j_position[k] for k in range(1, board.dimension)) else 0
    return x


def blocked_pawns(board: Board, color: Color) -> int:
    x = 0
    for position in board.find(PieceData(color, Pawn)):
        for j in range(1, board.dimension):
            new_position = tuple(position[i] + (1 if i == j else 0) for i in range(board.dimension))
            x += 1 if board.contains(new_position) else 0

    return x


def isolated_pawns(board: Board, color: Color) -> int:
    x = 0
    for i, i_position in enumerate(board.find(PieceData(color, Pawn))):
        for j, j_position in enumerate(board.find(PieceData(color, Pawn))):
            if i == j:
                continue
            x += 1 if j_position[0] != i_position[0] + 1 or j_position[0] != i_position[0] - 1  else 0
    return x

def delta_material(board: Board, piece_type, color: Color, rival_color: Color) -> int:
    return len(board.find(PieceData(color, piece_type))) - len(board.find(PieceData(rival_color, piece_type)))


def mobility(board, color) -> int:
    return sum(len(piece.moves()) for piece in board.pieces if piece.color is color)


def classic_evaluate(board: Classic, color: ClassicColor) -> float:
    rival_color = ClassicColor.black if color is ClassicColor.white else ClassicColor.black

    return (
        200 * delta_material(board, King, color, rival_color)
        + 9 * delta_material(board, Queen, color, rival_color)
        + 5 * delta_material(board, Rook, color, rival_color)
        + 3 * delta_material(board, Bishop, color, rival_color)
        + 3 * delta_material(board, Knight, color, rival_color)
        + 1 * delta_material(board, Pawn, color, rival_color)
        - 0.5 * (doubled_pawns(board, color) - doubled_pawns(board, rival_color))
        - 0.5 * (blocked_pawns(board, color) - blocked_pawns(board, rival_color))
        - 0.5 * (isolated_pawns(board, color) - isolated_pawns(board, rival_color))
        + 0.1 * (mobility(board, color) - mobility(board, rival_color))
    )
