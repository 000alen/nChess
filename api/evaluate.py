from time import perf_counter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

from api.chess_api import (
    COLORS,
    build_board,
    cached_get,
    cached_set,
    handle_api_error,
    make_cache,
    new_request_id,
    position_hash,
    signed_mate_in_for_white,
    write_json_response,
)
from nChess.Engine import evaluate_position, iterative_deepening
from nChess.nBoard.Board import ClassicColor

EVALUATE_CACHE = make_cache()
DEFAULT_SEARCH_DEPTH = 4
MAX_SEARCH_DEPTH = 6
DEFAULT_SEARCH_TIME_MS = 250
MIN_SEARCH_TIME_MS = 0
MAX_SEARCH_TIME_MS = 3_000


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

    search_depth = clamp_int(request.get("searchDepth", DEFAULT_SEARCH_DEPTH), 0, MAX_SEARCH_DEPTH)
    search_time_ms = clamp_int(
        request.get("searchTimeMs", DEFAULT_SEARCH_TIME_MS),
        MIN_SEARCH_TIME_MS,
        MAX_SEARCH_TIME_MS,
    )

    board = build_board(board_payload)
    color = COLORS[color_name]
    board_hash = position_hash(board)
    cache_key = (board_hash, color_name, search_depth, search_time_ms)
    cached = cached_get(EVALUATE_CACHE, cache_key)
    if cached is not None:
        return {**cached, "requestId": request_id, "cached": True, "elapsedMs": elapsed_ms(start)}

    score = evaluate_position(board, color)
    white_static_score = score if color is ClassicColor.white else -score

    mate_in = None
    search_score = None
    search_depth_reached = 0
    search_nodes = 0
    if search_depth > 0 and search_time_ms > 0:
        # Bounded iterative deepening only fires when the request opted into a
        # search budget. The score it returns is whatever depth was actually
        # completed; we never extrapolate. If the result is a mate score, the
        # ``MATE_SCORE - |score|`` convention recovers the *proved* mate
        # distance.
        result = iterative_deepening(
            board,
            max_depth=search_depth,
            color=color,
            evaluator=evaluate_position,
            time_limit_ms=search_time_ms,
        )
        search_score = result.score
        search_depth_reached = result.depth
        search_nodes = result.nodes
        mate_in = signed_mate_in_for_white(result.score, color_name)

    payload = {
        "requestId": request_id,
        "color": color_name,
        "positionHash": board_hash,
        "score": score,
        "whiteScore": white_static_score,
        "mateIn": mate_in,
        "searchScore": search_score,
        "searchDepthReached": search_depth_reached,
        "searchNodes": search_nodes,
        "status": {
            "white": board_status(board, ClassicColor.white),
            "black": board_status(board, ClassicColor.black),
        },
        "cached": False,
        "elapsedMs": elapsed_ms(start),
    }
    cached_set(EVALUATE_CACHE, cache_key, {key: value for key, value in payload.items() if key not in {"requestId", "elapsedMs", "cached"}})
    return payload


def clamp_int(value, low, high):
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = low
    return max(low, min(n, high))


def board_status(board, color):
    return {
        "inCheck": board.in_check(color),
        "inCheckmate": board.in_checkmate(color),
        "inStalemate": board.in_stalemate(color),
    }


def elapsed_ms(start):
    return round((perf_counter() - start) * 1000, 2)
