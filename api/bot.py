import json
from time import perf_counter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

from api.chess_api import COLORS, build_board, cached_get, cached_set, handle_api_error, make_cache, new_request_id, position_hash, serialize_board, serialize_move, write_json_response
from nChess.Engine import evaluate_position, iterative_deepening

BOT_CACHE = make_cache()
MIN_DEPTH = 1
MAX_DEPTH = 6
DEFAULT_DEPTH = 2
MIN_TIME_MS = 100
MAX_TIME_MS = 10_000
DEFAULT_TIME_MS = 750


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        request_id = new_request_id()
        try:
            request = self.read_json()
            if bool(request.get("stream")):
                stream_bot_move(self, request, request_id)
                return
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
        return json.loads(self.rfile.read(content_length))

    def write_json(self, status, payload):
        write_json_response(self, status, payload)


def parse_request(request):
    board_payload = request.get("board")
    if not isinstance(board_payload, dict):
        raise ValueError("board is required")
    color_name = request.get("color", board_payload.get("turn"))
    if color_name not in COLORS:
        raise ValueError("color must be 'white' or 'black'")
    depth = max(MIN_DEPTH, min(int(request.get("depth", DEFAULT_DEPTH)), MAX_DEPTH))
    time_limit_ms = max(MIN_TIME_MS, min(int(request.get("timeLimitMs", DEFAULT_TIME_MS)), MAX_TIME_MS))
    return board_payload, color_name, depth, time_limit_ms


def choose_bot_move(request, request_id=None):
    start = perf_counter()
    board_payload, color_name, depth, time_limit_ms = parse_request(request)

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


def stream_bot_move(handler_self, request, request_id):
    """Run iterative deepening, flushing one JSON line per completed depth.

    The frontend opens a single fetch and parses NDJSON line-by-line, so the
    user sees the principal variation refine in place as deeper plies finish
    instead of issuing a separate fetch per depth.
    """
    start = perf_counter()
    board_payload, color_name, depth, time_limit_ms = parse_request(request)
    board = build_board(board_payload)
    board_hash = position_hash(board)

    handler_self.send_response(HTTPStatus.OK)
    handler_self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
    handler_self.send_header("Cache-Control", "no-cache, no-transform")
    handler_self.send_header("X-Accel-Buffering", "no")
    handler_self.end_headers()

    def write_line(payload):
        handler_self.wfile.write((json.dumps(payload) + "\n").encode("utf-8"))
        try:
            handler_self.wfile.flush()
        except (BrokenPipeError, OSError):
            pass

    write_line({
        "type": "started",
        "requestId": request_id,
        "positionHash": board_hash,
        "color": color_name,
        "maxDepth": depth,
        "timeLimitMs": time_limit_ms,
    })

    def on_depth_complete(result):
        write_line({
            "type": "depth",
            "requestId": request_id,
            "depth": result.depth,
            "score": result.score,
            "nodes": result.nodes,
            "elapsedMs": result.elapsed_ms,
            "move": serialize_move(result.move),
            "positionHash": board_hash,
        })

    final = iterative_deepening(
        board,
        max_depth=depth,
        color=COLORS[color_name],
        evaluator=evaluate_position,
        time_limit_ms=time_limit_ms,
        on_depth_complete=on_depth_complete,
    )

    if final.move is not None:
        board.move(final.move)

    write_line({
        "type": "final",
        "requestId": request_id,
        "depth": final.depth,
        "score": final.score,
        "nodes": final.nodes,
        "searchElapsedMs": final.elapsed_ms,
        "elapsedMs": elapsed_ms(start),
        "move": serialize_move(final.move),
        "board": serialize_board(board),
        "positionHash": board_hash,
    })


def elapsed_ms(start):
    return round((perf_counter() - start) * 1000, 2)
