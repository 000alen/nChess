import json
from time import perf_counter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

from api.chess_api import COLORS, build_board, serialize_board, serialize_move
from nChess.Engine import evaluate_position, iterative_deepening


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
    start = perf_counter()
    board_payload = request.get("board")
    if not isinstance(board_payload, dict):
        raise ValueError("board is required")

    color_name = request.get("color", board_payload.get("turn"))
    if color_name not in COLORS:
        raise ValueError("color must be 'white' or 'black'")

    depth = int(request.get("depth", 2))
    depth = max(1, min(depth, 3))
    time_limit_ms = int(request.get("timeLimitMs", 750))
    time_limit_ms = max(100, min(time_limit_ms, 3000))

    board = build_board(board_payload)
    result = iterative_deepening(
        board,
        max_depth=depth,
        color=COLORS[color_name],
        evaluator=evaluate_position,
        time_limit_ms=time_limit_ms,
    )
    if result.move is not None:
        board.move(result.move)

    return {
        "move": serialize_move(result.move),
        "board": serialize_board(board),
        "score": result.score,
        "depth": result.depth,
        "nodes": result.nodes,
        "elapsedMs": elapsed_ms(start),
        "searchElapsedMs": result.elapsed_ms,
    }


def elapsed_ms(start):
    return round((perf_counter() - start) * 1000, 2)
