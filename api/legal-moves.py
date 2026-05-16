from time import perf_counter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

from api.chess_api import build_board, cached_get, cached_set, handle_api_error, make_cache, new_request_id, position_hash, serialize_move, write_json_response

LEGAL_MOVES_CACHE = make_cache()


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        request_id = new_request_id()
        try:
            request = self.read_json()
            response = legal_moves_request(request, request_id)
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


def legal_moves_request(request, request_id=None):
    start = perf_counter()
    board_payload = request.get("board")
    position = request.get("position")
    if not isinstance(board_payload, dict):
        raise ValueError("board is required")

    board = build_board(board_payload)
    board_hash = position_hash(board)
    if not isinstance(position, list) or len(position) != board.dimension:
        raise ValueError("position must match board.dimension")

    normalized_position = tuple(int(value) for value in position)
    cache_key = (board_hash, normalized_position)
    cached = cached_get(LEGAL_MOVES_CACHE, cache_key)
    if cached is not None:
        return {**cached, "requestId": request_id, "cached": True, "elapsedMs": elapsed_ms(start)}

    if not board.contains(normalized_position):
        return {"requestId": request_id, "positionHash": board_hash, "moves": [], "cached": False, "elapsedMs": elapsed_ms(start)}

    piece = board.get(normalized_position)
    if piece.color != board.current_turn():
        return {"requestId": request_id, "positionHash": board_hash, "moves": [], "cached": False, "elapsedMs": elapsed_ms(start)}

    payload = {
        "requestId": request_id,
        "positionHash": board_hash,
        "moves": [serialize_move(move) for move in piece.moves()],
        "cached": False,
        "elapsedMs": elapsed_ms(start),
    }
    cached_set(LEGAL_MOVES_CACHE, cache_key, {key: value for key, value in payload.items() if key not in {"requestId", "elapsedMs", "cached"}})
    return payload


def elapsed_ms(start):
    return round((perf_counter() - start) * 1000, 2)
