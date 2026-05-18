import hashlib
import json
from collections import OrderedDict
from http import HTTPStatus
from uuid import uuid4

from nChess.Engine import MATE_THRESHOLD, mate_in_moves
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

MAX_DIMENSION = 4
MIN_AXIS_SIZE = 4
MAX_AXIS_SIZE = 12
MAX_BOARD_VOLUME = 4096
MAX_PIECES = 256
MAX_CACHE_ITEMS = 128


class ApiError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def build_board(payload):
    dimension = int(payload.get("dimension", 0))
    size = payload.get("size")
    pieces = payload.get("pieces")
    turn = payload.get("turn")

    if dimension < 2 or dimension > MAX_DIMENSION:
        raise ApiError("INVALID_DIMENSION", "board.dimension must be between 2 and 4")
    if not isinstance(size, list) or len(size) != dimension:
        raise ApiError("INVALID_SIZE", "board.size must match board.dimension")
    if not isinstance(pieces, list):
        raise ApiError("INVALID_PIECES", "board.pieces must be a list")
    if len(pieces) > MAX_PIECES:
        raise ApiError("TOO_MANY_PIECES", f"board.pieces cannot exceed {MAX_PIECES}")

    normalized_size = tuple(int(value) for value in size)
    if any(value < MIN_AXIS_SIZE or value > MAX_AXIS_SIZE for value in normalized_size):
        raise ApiError("INVALID_SIZE", f"board.size axes must be between {MIN_AXIS_SIZE} and {MAX_AXIS_SIZE}")
    if volume(normalized_size) > MAX_BOARD_VOLUME:
        raise ApiError("BOARD_TOO_LARGE", f"board volume cannot exceed {MAX_BOARD_VOLUME}")

    turn_number = 1 if turn == "black" else 0
    board = nBoard(dimension, normalized_size, turn_number, TurnOrder)

    for piece in pieces:
        add_piece(board, piece, dimension)

    return board


def add_piece(board, piece, dimension):
    kind = piece.get("kind")
    color_name = piece.get("color")
    position = piece.get("position")

    if kind not in PIECE_TYPES:
        raise ApiError("INVALID_PIECE_KIND", f"unsupported piece kind: {kind}")
    if color_name not in COLORS:
        raise ApiError("INVALID_COLOR", f"unsupported piece color: {color_name}")
    if not isinstance(position, list) or len(position) != dimension:
        raise ApiError("INVALID_POSITION", "piece.position must match board.dimension")

    board.add(
        PIECE_TYPES[kind],
        tuple(int(value) for value in position),
        COLORS[color_name],
        has_moved=bool(piece.get("hasMoved", False)),
    )


def deserialize_move(payload, dimension):
    if not isinstance(payload, dict):
        raise ApiError("INVALID_MOVE", "move is required")
    initial_position = payload.get("from")
    final_position = payload.get("to")
    if not isinstance(initial_position, list) or len(initial_position) != dimension:
        raise ApiError("INVALID_MOVE", "move.from must match board.dimension")
    if not isinstance(final_position, list) or len(final_position) != dimension:
        raise ApiError("INVALID_MOVE", "move.to must match board.dimension")
    return Move(
        tuple(int(value) for value in initial_position),
        tuple(int(value) for value in final_position),
    )


def serialize_board(board):
    return {
        "dimension": board.dimension,
        "hash": position_hash(board),
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


def signed_mate_in_for_white(score, color_name):
    """White-perspective signed mate distance, in moves, or ``None``.

    Returns ``+N`` if white is mating in N moves, ``-N`` if white is being
    mated in N moves, ``0`` if the position is already final, and ``None``
    if the score is not a forced-mate score.

    ``score`` is interpreted as the value reported by the engine when
    searching from ``color_name``'s perspective.
    """
    if abs(score) < MATE_THRESHOLD:
        return None
    moves = mate_in_moves(score)
    if moves is None:
        return None
    sign = 1 if score >= 0 else -1
    if color_name == "black":
        sign = -sign
    if moves == 0:
        return 0
    return sign * moves


def volume(size):
    result = 1
    for value in size:
        result *= value
    return result


def position_hash(board):
    payload = {
        "dimension": board.dimension,
        "size": list(board.size),
        "turn": COLOR_NAMES[board.current_turn()],
        "pieces": sorted(
            (
                KIND_BY_TYPE[type(piece)],
                COLOR_NAMES[piece.color],
                list(piece.position),
                piece.has_moved,
            )
            for piece in board.pieces
        ),
    }
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:24]


def new_request_id():
    return uuid4().hex[:12]


def cached_get(cache, key):
    if key not in cache:
        return None
    value = cache.pop(key)
    cache[key] = value
    return value


def cached_set(cache, key, value):
    cache[key] = value
    while len(cache) > MAX_CACHE_ITEMS:
        cache.popitem(last=False)
    return value


def make_cache():
    return OrderedDict()


def error_payload(request_id, code, message):
    return {
        "requestId": request_id,
        "error": {
            "code": code,
            "message": message,
        },
    }


def write_json_response(handler, status, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def handle_api_error(handler, request_id, exc):
    if isinstance(exc, ApiError):
        write_json_response(handler, HTTPStatus.BAD_REQUEST, error_payload(request_id, exc.code, exc.message))
        return
    if isinstance(exc, ValueError):
        write_json_response(handler, HTTPStatus.BAD_REQUEST, error_payload(request_id, "BAD_REQUEST", str(exc)))
        return
    write_json_response(handler, HTTPStatus.INTERNAL_SERVER_ERROR, error_payload(request_id, "INTERNAL_ERROR", str(exc)))
