import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

from api.chess_api import build_board, deserialize_move, serialize_board, serialize_move


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            request = self.read_json()
            response = move_request(request)
            self.write_json(HTTPStatus.OK, response)
        except ValueError as exc:
            self.write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except Exception as exc:
            self.write_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "move failed", "detail": str(exc)})

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


def move_request(request):
    board_payload = request.get("board")
    if not isinstance(board_payload, dict):
        raise ValueError("board is required")

    board = build_board(board_payload)
    move = deserialize_move(request.get("move"), board.dimension)
    initial_piece = board.get(move.initial_position)
    if move not in initial_piece.moves():
        raise ValueError("move is not legal")

    board.move(move)

    return {
        "move": serialize_move(move),
        "board": serialize_board(board),
    }
