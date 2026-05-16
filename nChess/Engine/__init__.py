"""Evaluation and shallow search helpers for nChess boards."""

from dataclasses import dataclass
from math import inf
from time import perf_counter
from typing import Callable

from nChess.nBoard import nBoard, Color
from nChess.nBoard.Board import Board, ClassicColor
from nChess.Piece import Move, Piece, PieceData
from nChess.Piece.Bishop import Bishop
from nChess.Piece.King import King
from nChess.Piece.Knight import Knight
from nChess.Piece.Pawn import Pawn
from nChess.Piece.Queen import Queen
from nChess.Piece.Rook import Rook

Evaluator = Callable[[nBoard, Color], float]

PIECE_VALUES = {
    King: 200,
    Queen: 9,
    Rook: 5,
    Bishop: 3,
    Knight: 3,
    Pawn: 1,
}

MATE_SCORE = 1_000_000
DRAW_SCORE = 0


@dataclass(frozen=True)
class SearchResult:
    move: Move | None
    score: float
    depth: int
    nodes: int
    elapsed_ms: float = 0


@dataclass
class SearchContext:
    started_at: float
    deadline_ms: int | None = None
    transpositions: dict[tuple[tuple, Color, int], tuple[float, Move | None]] = None

    def __post_init__(self):
        if self.transpositions is None:
            self.transpositions = {}


class SearchTimeout(Exception):
    pass


def pawns(board: nBoard, color: Color) -> tuple[Pawn, ...]:
    return tuple(
        piece
        for piece in board.pieces
        if piece.color == color and type(piece) is Pawn
    )


def doubled_pawns(board: nBoard, color: Color) -> int:
    files = {}
    for pawn in pawns(board, color):
        files[pawn.position[pawn.capture_axis]] = files.get(pawn.position[pawn.capture_axis], 0) + 1
    return sum(count - 1 for count in files.values() if count > 1)


def blocked_pawns(board: nBoard, color: Color) -> int:
    x = 0
    for pawn in pawns(board, color):
        for axis in range(board.dimension):
            if axis == pawn.capture_axis:
                continue
            new_position = tuple(
                pawn.position[i] + (pawn.direction if i == axis else 0)
                for i in range(board.dimension)
            )
            x += 1 if board.contains(new_position) else 0

    return x


def isolated_pawns(board: nBoard, color: Color) -> int:
    x = 0
    friendly_pawns = pawns(board, color)
    for i, pawn in enumerate(friendly_pawns):
        if all(
            abs(other.position[pawn.capture_axis] - pawn.position[pawn.capture_axis]) != 1
            for j, other in enumerate(friendly_pawns)
            if i != j
        ):
            x += 1
    return x


def piece_value(piece: Piece) -> float:
    return PIECE_VALUES.get(type(piece), 0)


def delta_material(board: nBoard, piece_type, color: Color, rival_color: Color) -> int:
    return len(board.find(PieceData(color, piece_type))) - len(
        board.find(PieceData(rival_color, piece_type))
    )


def material(board: nBoard, color: Color, rival_color: Color = None) -> float:
    if rival_color is None:
        rival_color = opponent_color(board, color)
    return sum(
        piece_value(piece) if piece.color == color
        else -piece_value(piece) if piece.color == rival_color
        else 0
        for piece in board.pieces
    )


def mobility(board, color) -> int:
    return sum(len(piece.moves()) for piece in board.pieces if piece.color == color)


def pseudo_mobility(board, color) -> int:
    return sum(len(piece.all_moves()) for piece in board.pieces if piece.color == color)


def colors(board: nBoard) -> tuple[Color, ...]:
    seen = []
    for piece in board.pieces:
        if piece.color not in seen:
            seen.append(piece.color)
    return tuple(seen)


def opponent_color(board: nBoard, color: Color) -> Color:
    if len(board.turn_order) == 2:
        return board.turn_order[1] if color == board.turn_order[0] else board.turn_order[0]

    for piece_color in colors(board):
        if piece_color != color:
            return piece_color
    raise ValueError("engine search requires at least two colors")


def evaluate_position(board: nBoard, color: Color) -> float:
    rival_color = opponent_color(board, color)
    color_activity, color_pressure = activity_metrics(board, color)
    rival_activity, rival_pressure = activity_metrics(board, rival_color)

    return (
        material(board, color, rival_color)
        - 0.5 * (doubled_pawns(board, color) - doubled_pawns(board, rival_color))
        - 0.5 * (blocked_pawns(board, color) - blocked_pawns(board, rival_color))
        - 0.5 * (isolated_pawns(board, color) - isolated_pawns(board, rival_color))
        + 0.04 * (color_activity - rival_activity)
        + 0.3 * (pawn_advancement(board, color) - pawn_advancement(board, rival_color))
        + 0.08 * (centrality(board, color) - centrality(board, rival_color))
        + 0.06 * (color_pressure - rival_pressure)
        + king_safety(board, color, rival_color)
    )


def classic_evaluate(board: Board, color: ClassicColor) -> float:
    return evaluate_position(board, color)


def pawn_advancement(board: nBoard, color: Color) -> float:
    score = 0
    for pawn in pawns(board, color):
        for axis in range(board.dimension):
            if axis == pawn.capture_axis or board.size[axis] <= 1:
                continue

            if pawn.direction == 1:
                score += pawn.position[axis] / (board.size[axis] - 1)
            else:
                score += (board.size[axis] - 1 - pawn.position[axis]) / (board.size[axis] - 1)
    return score


def centrality(board: nBoard, color: Color) -> float:
    score = 0
    for piece in board.pieces:
        if piece.color != color:
            continue

        for axis, coordinate in enumerate(piece.position):
            if board.size[axis] <= 1:
                continue

            center = (board.size[axis] - 1) / 2
            score += 1 - (abs(coordinate - center) / max(center, 1))
    return score


def attack_pressure(board: nBoard, color: Color) -> float:
    return activity_metrics(board, color)[1]


def activity_metrics(board: nBoard, color: Color) -> tuple[int, float]:
    moves = [
        move
        for piece in board.pieces
        if piece.color == color
        for move in piece.all_moves()
    ]
    attacked_positions = {move.final_position for move in moves}

    pressure = sum(
        piece_value(piece)
        for piece in board.pieces
        if piece.color != color and type(piece) is not King and piece.position in attacked_positions
    )
    return len(moves), pressure


def king_safety(board: nBoard, color: Color, rival_color: Color) -> float:
    score = 0
    if board.in_check(color):
        score -= 1.5
    if board.in_check(rival_color):
        score += 1.5
    return score


def current_or_requested_color(board: nBoard, color: Color = None) -> Color:
    if color is not None:
        return color

    current_turn = board.current_turn()
    if current_turn is None:
        raise ValueError("color is required when board has no turn order")
    return current_turn


def legal_moves(board: nBoard, color: Color = None) -> tuple[Move, ...]:
    color = current_or_requested_color(board, color)
    return tuple(
        move
        for piece in board.pieces
        if piece.color == color
        for move in piece.moves()
    )


def promotes_after_move(board: nBoard, move: Move) -> bool:
    moving_piece = board.get(move.initial_position)
    if len(getattr(moving_piece, "promotions", ())) == 0:
        return False
    if not hasattr(moving_piece, "capture_axis") or not hasattr(moving_piece, "direction"):
        return False

    return all(
        move.final_position[axis] == (
            board.size[axis] - 1 if moving_piece.direction == 1 else 0
        )
        for axis in range(board.dimension)
        if axis != moving_piece.capture_axis
    )


def move_sort_key(board: nBoard, move: Move) -> tuple[float, float]:
    capture_value = (
        piece_value(board.get(move.final_position))
        if board.contains(move.final_position)
        else 0
    )
    moving_piece = board.get(move.initial_position)
    promotion_value = max(
        (PIECE_VALUES.get(promotion, 0) for promotion in getattr(moving_piece, "promotions", ())),
        default=0,
    ) if promotes_after_move(board, move) else 0
    return capture_value, promotion_value


def ordered_legal_moves(board: nBoard, color: Color = None) -> tuple[Move, ...]:
    return tuple(
        sorted(
            legal_moves(board, color),
            key=lambda move: move_sort_key(board, move),
            reverse=True,
        )
    )


def tactical_moves(board: nBoard, color: Color = None) -> tuple[Move, ...]:
    return tuple(
        move
        for move in ordered_legal_moves(board, color)
        if board.contains(move.final_position) or promotes_after_move(board, move)
    )


def assume_engine_move(board: nBoard, move: Move) -> nBoard:
    return board.assume_move(move, force=board.current_turn() is None)


def next_search_color(board: nBoard, previous_color: Color) -> Color:
    current_turn = board.current_turn()
    if current_turn is not None:
        return current_turn
    return opponent_color(board, previous_color)


def negamax(
    board: nBoard,
    depth: int,
    color: Color,
    evaluator: Evaluator = evaluate_position,
    alpha: float = -inf,
    beta: float = inf,
    ply: int = 0,
    context: SearchContext = None,
) -> tuple[float, int]:
    check_deadline(context)
    if board.in_checkmate(color):
        return -MATE_SCORE + ply, 1
    if board.in_stalemate(color):
        return DRAW_SCORE, 1
    if depth == 0:
        if board.dimension > 2:
            return evaluator(board, color), 1
        return quiescence(board, color, evaluator, alpha, beta, 2, context)

    cache_key = (position_key(board), color, depth)
    if context is not None and cache_key in context.transpositions:
        cached_score, _cached_move = context.transpositions[cache_key]
        return cached_score, 1

    moves = ordered_legal_moves(board, color)
    if len(moves) == 0:
        return DRAW_SCORE, 1

    nodes = 1
    best_score = -inf
    for move in moves:
        child = assume_engine_move(board, move)
        child_color = next_search_color(child, color)
        score, child_nodes = negamax(
            child,
            depth - 1,
            child_color,
            evaluator,
            -beta,
            -alpha,
            ply + 1,
            context,
        )
        score = -score
        nodes += child_nodes

        if score > best_score:
            best_score = score
        alpha = max(alpha, score)
        if alpha >= beta:
            break

    if context is not None:
        context.transpositions[cache_key] = (best_score, None)
    return best_score, nodes


def quiescence(
    board: nBoard,
    color: Color,
    evaluator: Evaluator,
    alpha: float,
    beta: float,
    depth: int,
    context: SearchContext = None,
) -> tuple[float, int]:
    check_deadline(context)
    stand_pat = evaluator(board, color)
    nodes = 1

    if depth == 0:
        return stand_pat, nodes
    if stand_pat >= beta:
        return beta, nodes
    alpha = max(alpha, stand_pat)

    for move in tactical_moves(board, color):
        child = assume_engine_move(board, move)
        child_color = next_search_color(child, color)
        score, child_nodes = quiescence(child, child_color, evaluator, -beta, -alpha, depth - 1, context)
        score = -score
        nodes += child_nodes
        if score >= beta:
            return beta, nodes
        alpha = max(alpha, score)

    return alpha, nodes


def find_best_move(
    board: nBoard,
    depth: int = 2,
    color: Color = None,
    evaluator: Evaluator = evaluate_position,
    context: SearchContext = None,
) -> SearchResult:
    if depth < 1:
        raise ValueError("depth must be at least 1")

    color = current_or_requested_color(board, color)
    moves = ordered_legal_moves(board, color)
    if len(moves) == 0:
        score = -MATE_SCORE if board.in_checkmate(color) else DRAW_SCORE
        return SearchResult(None, score, depth, 1)

    nodes = 1
    best_move = None
    best_score = -inf
    alpha = -inf
    beta = inf

    for move in moves:
        check_deadline(context)
        child = assume_engine_move(board, move)
        child_color = next_search_color(child, color)
        try:
            score, child_nodes = negamax(
                child,
                depth - 1,
                child_color,
                evaluator,
                -beta,
                -alpha,
                1,
                context,
            )
        except SearchTimeout:
            if best_move is not None:
                return SearchResult(best_move, best_score, depth, nodes, elapsed_ms(context.started_at))
            raise
        score = -score
        nodes += child_nodes

        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, score)

    return SearchResult(best_move, best_score, depth, nodes)


def iterative_deepening(
    board: nBoard,
    max_depth: int = 2,
    color: Color = None,
    evaluator: Evaluator = evaluate_position,
    time_limit_ms: int = 750,
) -> SearchResult:
    start = perf_counter()
    context = SearchContext(start, time_limit_ms)
    max_depth = max(1, max_depth)
    best_result = None

    for depth in range(1, max_depth + 1):
        if elapsed_ms(start) >= time_limit_ms and best_result is not None:
            break

        try:
            result = find_best_move(board, depth, color, evaluator, context)
        except SearchTimeout:
            if best_result is None:
                fallback_color = current_or_requested_color(board, color)
                moves = ordered_legal_moves(board, fallback_color)
                return SearchResult(
                    moves[0] if len(moves) else None,
                    evaluator(board, fallback_color) if len(moves) else DRAW_SCORE,
                    0,
                    1,
                    elapsed_ms(start),
                )
            break
        best_result = SearchResult(
            result.move,
            result.score,
            result.depth,
            result.nodes if best_result is None else best_result.nodes + result.nodes,
            elapsed_ms(start),
        )

    if best_result is None:
        return SearchResult(None, DRAW_SCORE, 0, 0, elapsed_ms(start))
    return best_result


def best_move(
    board: nBoard,
    depth: int = 2,
    color: Color = None,
    evaluator: Evaluator = evaluate_position,
) -> Move | None:
    return find_best_move(board, depth, color, evaluator).move


def elapsed_ms(start):
    return round((perf_counter() - start) * 1000, 2)


def check_deadline(context: SearchContext | None):
    if context is None or context.deadline_ms is None:
        return
    if elapsed_ms(context.started_at) >= context.deadline_ms:
        raise SearchTimeout()


def position_key(board: nBoard) -> tuple:
    return (
        board.dimension,
        board.size,
        board.current_turn(),
        tuple(sorted(
            (
                type(piece).__name__,
                piece.color,
                piece.position,
                piece.has_moved,
                getattr(piece, "capture_axis", None),
            )
            for piece in board.pieces
        )),
    )
