from time import perf_counter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

from api.chess_api import COLORS, build_board, cached_get, cached_set, handle_api_error, make_cache, new_request_id, position_hash, write_json_response
from nChess.Engine import evaluate_position
from nChess.nBoard.Board import ClassicColor

EVALUATE_CACHE = make_cache()


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        request_id = new_request_id()
        try:
            request = self.read_json()
            response = evaluate_request(request, request_id)
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


def evaluate_request(request, request_id=None):
    start = perf_counter()
    board_payload = request.get("board")
    if not isinstance(board_payload, dict):
        raise ValueError("board is required")

    color_name = request.get("color", "white")
    if color_name not in COLORS:
        raise ValueError("color must be 'white' or 'black'")

    board = build_board(board_payload)
    color = COLORS[color_name]
    board_hash = position_hash(board)
    cache_key = (board_hash, color_name)
    cached = cached_get(EVALUATE_CACHE, cache_key)
    if cached is not None:
        return {**cached, "requestId": request_id, "cached": True, "elapsedMs": elapsed_ms(start)}

    score = evaluate_position(board, color)

    payload = {
        "requestId": request_id,
        "color": color_name,
        "positionHash": board_hash,
        "score": score,
        "whiteScore": score if color is ClassicColor.white else -score,
        "status": {
            "white": board_status(board, ClassicColor.white),
            "black": board_status(board, ClassicColor.black),
        },
        "cached": False,
        "elapsedMs": elapsed_ms(start),
    }
    cached_set(EVALUATE_CACHE, cache_key, {key: value for key, value in payload.items() if key not in {"requestId", "elapsedMs", "cached"}})
    return payload


def board_status(board, color):
    return {
        "inCheck": board.in_check(color),
        "inCheckmate": board.in_checkmate(color),
        "inStalemate": board.in_stalemate(color),
    }


def elapsed_ms(start):
    return round((perf_counter() - start) * 1000, 2)
