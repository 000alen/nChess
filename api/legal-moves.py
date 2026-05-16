import json
from time import perf_counter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

from api.chess_api import build_board, serialize_move


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            request = self.read_json()
            response = legal_moves_request(request)
            self.write_json(HTTPStatus.OK, response)
        except ValueError as exc:
            self.write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except Exception as exc:
            self.write_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "legal moves failed", "detail": str(exc)})

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


def legal_moves_request(request):
    start = perf_counter()
    board_payload = request.get("board")
    position = request.get("position")
    if not isinstance(board_payload, dict):
        raise ValueError("board is required")

    board = build_board(board_payload)
    if not isinstance(position, list) or len(position) != board.dimension:
        raise ValueError("position must match board.dimension")

    normalized_position = tuple(int(value) for value in position)
    if not board.contains(normalized_position):
        return {"moves": [], "elapsedMs": elapsed_ms(start)}

    piece = board.get(normalized_position)
    if piece.color != board.current_turn():
        return {"moves": [], "elapsedMs": elapsed_ms(start)}

    return {
        "moves": [serialize_move(move) for move in piece.moves()],
        "elapsedMs": elapsed_ms(start),
    }


def elapsed_ms(start):
    return round((perf_counter() - start) * 1000, 2)
