from nChess.Piece import Move
from nChess.Piece.Bishop import Bishop
from nChess.Piece.King import King
from nChess.Piece.Knight import Knight
from nChess.Piece.Pawn import Pawn
from nChess.Piece.Queen import Queen
from nChess.Piece.Rook import Rook
from nChess.nBoard import nBoard
from nChess.nBoard.Board import ClassicColor, TurnOrder

PIECE_TYPES = {
    "bishop": Bishop,
    "king": King,
    "knight": Knight,
    "pawn": Pawn,
    "queen": Queen,
    "rook": Rook,
}

KIND_BY_TYPE = {
    Bishop: "bishop",
    King: "king",
    Knight: "knight",
    Pawn: "pawn",
    Queen: "queen",
    Rook: "rook",
}

COLORS = {
    "white": ClassicColor.white,
    "black": ClassicColor.black,
}

COLOR_NAMES = {
    ClassicColor.white: "white",
    ClassicColor.black: "black",
}


def build_board(payload):
    dimension = int(payload.get("dimension", 0))
    size = payload.get("size")
    pieces = payload.get("pieces")
    turn = payload.get("turn")

    if dimension < 2:
        raise ValueError("board.dimension must be at least 2")
    if not isinstance(size, list) or len(size) != dimension:
        raise ValueError("board.size must match board.dimension")
    if not isinstance(pieces, list):
        raise ValueError("board.pieces must be a list")

    turn_number = 1 if turn == "black" else 0
    board = nBoard(dimension, tuple(int(value) for value in size), turn_number, TurnOrder)

    for piece in pieces:
        add_piece(board, piece, dimension)

    return board


def add_piece(board, piece, dimension):
    kind = piece.get("kind")
    color_name = piece.get("color")
    position = piece.get("position")

    if kind not in PIECE_TYPES:
        raise ValueError(f"unsupported piece kind: {kind}")
    if color_name not in COLORS:
        raise ValueError(f"unsupported piece color: {color_name}")
    if not isinstance(position, list) or len(position) != dimension:
        raise ValueError("piece.position must match board.dimension")

    board.add(
        PIECE_TYPES[kind],
        tuple(int(value) for value in position),
        COLORS[color_name],
        has_moved=bool(piece.get("hasMoved", False)),
    )


def deserialize_move(payload, dimension):
    if not isinstance(payload, dict):
        raise ValueError("move is required")
    initial_position = payload.get("from")
    final_position = payload.get("to")
    if not isinstance(initial_position, list) or len(initial_position) != dimension:
        raise ValueError("move.from must match board.dimension")
    if not isinstance(final_position, list) or len(final_position) != dimension:
        raise ValueError("move.to must match board.dimension")
    return Move(
        tuple(int(value) for value in initial_position),
        tuple(int(value) for value in final_position),
    )


def serialize_board(board):
    return {
        "dimension": board.dimension,
        "size": list(board.size),
        "turn": COLOR_NAMES[board.current_turn()],
        "pieces": [serialize_piece(piece) for piece in board.pieces],
    }


def serialize_piece(piece):
    color = COLOR_NAMES[piece.color]
    kind = KIND_BY_TYPE[type(piece)]
    return {
        "id": f"{color}-{kind}-{serialize_position(piece.position)}",
        "kind": kind,
        "color": color,
        "position": list(piece.position),
        "hasMoved": piece.has_moved,
    }


def serialize_move(move):
    if move is None:
        return None

    return {
        "from": list(move.initial_position),
        "to": list(move.final_position),
    }


def serialize_position(position):
    return ",".join(str(value) for value in position)
