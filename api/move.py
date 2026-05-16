from time import perf_counter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

from api.chess_api import PIECE_TYPES, build_board, deserialize_move, handle_api_error, new_request_id, position_hash, serialize_board, serialize_move, write_json_response
from nChess.Piece.Pawn import Pawn


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        request_id = new_request_id()
        try:
            request = self.read_json()
            response = move_request(request, request_id)
            self.write_json(HTTPStatus.OK, response)
        except Exception as exc:
            handle_api_error(self, request_id, exc)

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def read_json(self):
        content_length = int(self.headers.get("content-length", 0))
        if content_length == 0:
            raise ValueError("request body is required")
        import json
        return json.loads(self.rfile.read(content_length))

    def write_json(self, status, payload):
        write_json_response(self, status, payload)


def move_request(request, request_id=None):
    start = perf_counter()
    board_payload = request.get("board")
    if not isinstance(board_payload, dict):
        raise ValueError("board is required")

    board = build_board(board_payload)
    before_hash = position_hash(board)
    move_payload = request.get("move")
    move = deserialize_move(move_payload, board.dimension)
    initial_piece = board.get(move.initial_position)
    if move not in initial_piece.moves():
        raise ValueError("move is not legal")

    board.move(move)
    apply_promotion_choice(board, initial_piece, move, request.get("promotion") or move_payload.get("promotion"))

    return {
        "requestId": request_id,
        "move": serialize_move(move),
        "board": serialize_board(board),
        "positionHash": before_hash,
        "elapsedMs": elapsed_ms(start),
    }


def elapsed_ms(start):
    return round((perf_counter() - start) * 1000, 2)


def apply_promotion_choice(board, initial_piece, move, promotion):
    if promotion is None or type(initial_piece) is not Pawn:
        return
    if promotion not in {"bishop", "knight", "queen", "rook"}:
        raise ValueError("promotion must be bishop, knight, queen, or rook")
    promoted_piece = board.get(move.final_position)
    if type(promoted_piece).__name__ != "Queen":
        return

    promotion_type = PIECE_TYPES[promotion]
    replacement = promotion_type(
        promoted_piece.position,
        promoted_piece.color,
        has_moved=True,
        board=board,
    )
    board.pieces[board.pieces.index(promoted_piece)] = replacement
    board.occupied[move.final_position] = replacement
