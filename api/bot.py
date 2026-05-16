import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

from nChess.Engine import blocked_pawns, doubled_pawns, find_best_move, isolated_pawns, material, opponent_color
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

COLORS = {
    "white": ClassicColor.white,
    "black": ClassicColor.black,
}


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            request = self.read_json()
            response = choose_bot_move(request)
            self.write_json(HTTPStatus.OK, response)
        except ValueError as exc:
            self.write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except Exception as exc:
            self.write_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "bot failed", "detail": str(exc)})

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def read_json(self):
        content_length = int(self.headers.get("content-length", 0))
        if content_length == 0:
            raise ValueError("request body is required")
        return json.loads(self.rfile.read(content_length))

    def write_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def choose_bot_move(request):
    board_payload = request.get("board")
    if not isinstance(board_payload, dict):
        raise ValueError("board is required")

    color_name = request.get("color", board_payload.get("turn"))
    if color_name not in COLORS:
        raise ValueError("color must be 'white' or 'black'")

    depth = int(request.get("depth", 1))
    depth = max(1, min(depth, 2))

    board = build_board(board_payload)
    result = find_best_move(board, depth=depth, color=COLORS[color_name], evaluator=bot_evaluate)

    return {
        "move": serialize_move(result.move),
        "score": result.score,
        "depth": result.depth,
        "nodes": result.nodes,
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


def serialize_move(move):
    if move is None:
        return None

    return {
        "from": list(move.initial_position),
        "to": list(move.final_position),
    }


def bot_evaluate(board, color):
    rival_color = opponent_color(board, color)
    return (
        material(board, color, rival_color)
        - 0.25 * (doubled_pawns(board, color) - doubled_pawns(board, rival_color))
        - 0.25 * (blocked_pawns(board, color) - blocked_pawns(board, rival_color))
        - 0.25 * (isolated_pawns(board, color) - isolated_pawns(board, rival_color))
    )
