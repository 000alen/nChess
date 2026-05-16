from time import perf_counter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

from api.chess_api import COLORS, build_board, cached_get, cached_set, handle_api_error, make_cache, new_request_id, position_hash, serialize_board, serialize_move, write_json_response
from nChess.Engine import evaluate_position, iterative_deepening

BOT_CACHE = make_cache()


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        request_id = new_request_id()
        try:
            request = self.read_json()
            response = choose_bot_move(request, request_id)
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


def choose_bot_move(request, request_id=None):
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
    board_hash = position_hash(board)
    cache_key = (board_hash, color_name, depth, time_limit_ms)
    cached = cached_get(BOT_CACHE, cache_key)
    if cached is not None:
        return {**cached, "requestId": request_id, "cached": True, "elapsedMs": elapsed_ms(start)}

    result = iterative_deepening(
        board,
        max_depth=depth,
        color=COLORS[color_name],
        evaluator=evaluate_position,
        time_limit_ms=time_limit_ms,
    )
    if result.move is not None:
        board.move(result.move)

    payload = {
        "requestId": request_id,
        "move": serialize_move(result.move),
        "board": serialize_board(board),
        "positionHash": board_hash,
        "score": result.score,
        "depth": result.depth,
        "nodes": result.nodes,
        "cached": False,
        "elapsedMs": elapsed_ms(start),
        "searchElapsedMs": result.elapsed_ms,
    }
    cached_set(BOT_CACHE, cache_key, {key: value for key, value in payload.items() if key not in {"requestId", "elapsedMs", "cached"}})
    return payload


def elapsed_ms(start):
    return round((perf_counter() - start) * 1000, 2)
