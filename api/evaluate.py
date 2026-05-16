import json
from time import perf_counter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

from api.chess_api import COLORS, build_board
from nChess.Engine import evaluate_position
from nChess.nBoard.Board import ClassicColor


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            request = self.read_json()
            response = evaluate_request(request)
            self.write_json(HTTPStatus.OK, response)
        except ValueError as exc:
            self.write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except Exception as exc:
            self.write_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "evaluation failed", "detail": str(exc)})

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


def evaluate_request(request):
    start = perf_counter()
    board_payload = request.get("board")
    if not isinstance(board_payload, dict):
        raise ValueError("board is required")

    color_name = request.get("color", "white")
    if color_name not in COLORS:
        raise ValueError("color must be 'white' or 'black'")

    board = build_board(board_payload)
    color = COLORS[color_name]
    score = evaluate_position(board, color)

    return {
        "color": color_name,
        "score": score,
        "whiteScore": score if color is ClassicColor.white else -score,
        "status": {
            "white": board_status(board, ClassicColor.white),
            "black": board_status(board, ClassicColor.black),
        },
        "elapsedMs": elapsed_ms(start),
    }


def board_status(board, color):
    return {
        "inCheck": board.in_check(color),
        "inCheckmate": board.in_checkmate(color),
        "inStalemate": board.in_stalemate(color),
    }


def elapsed_ms(start):
    return round((perf_counter() - start) * 1000, 2)
