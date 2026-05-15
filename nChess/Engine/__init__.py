from nChess.nBoard import nBoard, Color
from nChess.nBoard.Board import Board, ClassicColor
from nChess.Piece import PieceData
from nChess.Piece.Bishop import Bishop
from nChess.Piece.King import King
from nChess.Piece.Knight import Knight
from nChess.Piece.Pawn import Pawn
from nChess.Piece.Queen import Queen
from nChess.Piece.Rook import Rook


def pawns(board: nBoard, color: Color) -> tuple[Pawn, ...]:
    return tuple(
        piece
        for piece in board.pieces
        if piece.color == color and type(piece) is Pawn
    )


def doubled_pawns(board: nBoard, color: Color) -> int:
    x = 0
    for i, i_position in enumerate(board.find(PieceData(color, Pawn))):
        for j, j_position in enumerate(board.find(PieceData(color, Pawn))):
            if i == j:
                continue
            x += 1 if any(i_position[k] == j_position[k] for k in range(1, board.dimension)) else 0
    return x


def blocked_pawns(board: nBoard, color: Color) -> int:
    x = 0
    for pawn in pawns(board, color):
        for axis in range(board.dimension):
            if axis == pawn.capture_axis:
                continue
            new_position = tuple(
                pawn.position[i] + (pawn.direction if i == axis else 0)
                for i in range(board.dimension)
            )
            x += 1 if board.contains(new_position) else 0

    return x


def isolated_pawns(board: nBoard, color: Color) -> int:
    x = 0
    friendly_pawns = pawns(board, color)
    for i, pawn in enumerate(friendly_pawns):
        if all(
            abs(other.position[pawn.capture_axis] - pawn.position[pawn.capture_axis]) != 1
            for j, other in enumerate(friendly_pawns)
            if i != j
        ):
            x += 1
    return x

def delta_material(board: nBoard, piece_type, color: Color, rival_color: Color) -> int:
    return len(board.find(PieceData(color, piece_type))) - len(board.find(PieceData(rival_color, piece_type)))


def mobility(board, color) -> int:
    return sum(len(piece.moves()) for piece in board.pieces if piece.color == color)


def classic_evaluate(board: Board, color: ClassicColor) -> float:
    rival_color = ClassicColor.black if color is ClassicColor.white else ClassicColor.white

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
