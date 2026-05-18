import unittest
import importlib.util
from pathlib import Path

from api.bot import choose_bot_move, stream_bot_move
from api.evaluate import evaluate_request
from api.move import move_request
from nChess.Engine import (
    EXACT,
    LOWER,
    MATE_SCORE,
    MATE_THRESHOLD,
    SearchContext,
    TTEntry,
    UPPER,
    activity_metrics,
    best_move,
    centrality,
    classic_evaluate,
    doubled_pawns,
    endgame_factor,
    evaluate_position,
    find_best_move,
    iterative_deepening,
    king_safety,
    legal_moves,
    mate_distance,
    mate_in_moves,
    negamax,
    position_key,
)
from api.chess_api import signed_mate_in_for_white
from nChess.GUI.geometry import (
    board_coordinates_for_indices,
    board_grid_size,
    board_indices_for_position,
    cell_indices_for_position,
    position_for_cell_indices,
    position_padding,
)
from nChess.nBoard import nBoard
from nChess.nBoard.Board import Board, ClassicColor
from nChess.Piece import Move, PieceData
from nChess.Piece.Bishop import Bishop
from nChess.Piece.King import King
from nChess.Piece.Knight import Knight
from nChess.Piece.Pawn import Pawn
from nChess.Piece.Queen import Queen
from nChess.Piece.Rook import Rook
from nChess.utils import to_PNG

LEGAL_MOVES_SPEC = importlib.util.spec_from_file_location(
    "legal_moves_api",
    Path(__file__).parents[1] / "api" / "legal-moves.py",
)
legal_moves_api = importlib.util.module_from_spec(LEGAL_MOVES_SPEC)
LEGAL_MOVES_SPEC.loader.exec_module(legal_moves_api)


class BoardRuleTests(unittest.TestCase):
    def test_piece_data_filters_are_optional(self):
        board = Board()

        self.assertEqual(board.find(PieceData(ClassicColor.white, King)), ((3, 0),))
        self.assertEqual(
            board.find(PieceData(ClassicColor.white, King, (3, 0), False)),
            ((3, 0),),
        )

    def test_rook_attack_puts_king_in_check(self):
        board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black))
        board.add(King, (0, 0), ClassicColor.white)
        board.add(Rook, (0, 7), ClassicColor.black)

        self.assertTrue(board.in_check(ClassicColor.white))

    def test_stalemate_helper_uses_piece_move_signature(self):
        self.assertFalse(Board().in_stalemate(ClassicColor.white))

    def test_sliding_piece_stops_after_capture(self):
        board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black))
        board.add(King, (7, 7), ClassicColor.white)
        board.add(King, (7, 0), ClassicColor.black)
        board.add(Rook, (0, 0), ClassicColor.white)
        board.add(Pawn, (0, 1), ClassicColor.black)

        rook_moves = {move.final_position for move in board.get((0, 0)).moves()}

        self.assertIn((0, 1), rook_moves)
        self.assertNotIn((0, 2), rook_moves)

    def test_legal_moves_do_not_capture_kings(self):
        board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black))
        board.add(King, (7, 7), ClassicColor.white)
        board.add(King, (7, 0), ClassicColor.black)
        board.add(Rook, (0, 0), ClassicColor.white)

        self.assertNotIn((7, 0), {move.final_position for move in board.get((0, 0)).moves()})
        with self.assertRaises(AssertionError):
            board.move(Move((0, 0), (7, 0)))

    def test_piece_move_marks_piece_as_moved_and_pawn_cannot_double_step_again(self):
        board = Board()
        board.move(Move((0, 1), (0, 3)))
        pawn = board.get((0, 3))

        self.assertTrue(pawn.has_moved)
        self.assertNotIn((0, 5), {move.final_position for move in pawn.moves()})

    def test_pawn_promotion_uses_axis_indices(self):
        board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black))
        board.add(Pawn, (0, 7), ClassicColor.white)

        self.assertTrue(board.get((0, 7)).is_promotable())

    def test_pawn_promotes_to_queen_on_move(self):
        board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black))
        board.add(King, (7, 7), ClassicColor.white)
        board.add(King, (7, 0), ClassicColor.black)
        board.add(Pawn, (0, 6), ClassicColor.white)

        board.move(Move((0, 6), (0, 7)))

        self.assertIs(type(board.get((0, 7))), Queen)
        self.assertTrue(board.get((0, 7)).has_moved)

    def test_knight_leaps_over_intervening_pieces(self):
        board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black))
        board.add(King, (7, 7), ClassicColor.white)
        board.add(King, (7, 0), ClassicColor.black)
        board.add(Knight, (3, 3), ClassicColor.white)
        for position in ((4, 3), (4, 4), (5, 3)):
            board.add(Pawn, position, ClassicColor.white)

        knight_moves = {move.final_position for move in board.get((3, 3)).moves()}

        self.assertIn((5, 4), knight_moves)

    def test_diagonals_include_all_axis_combinations(self):
        diagonals = nBoard.compute_diagonals(3)

        self.assertIn((1, 0, 1), diagonals)
        self.assertIn((-1, 0, 1), diagonals)


class IntegrationSmokeTests(unittest.TestCase):
    def test_engine_evaluates_classic_board(self):
        self.assertEqual(classic_evaluate(Board(), ClassicColor.white), 0)

    def test_rich_evaluation_rewards_activity(self):
        board = Board()
        before = evaluate_position(board, ClassicColor.white)

        board.move(Move((0, 1), (0, 3)))

        self.assertNotEqual(evaluate_position(board, ClassicColor.white), before)

    def test_doubled_pawns_count_extra_pawns_on_same_file(self):
        board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black))
        board.add(Pawn, (0, 1), ClassicColor.white)
        board.add(Pawn, (0, 3), ClassicColor.white)
        board.add(Pawn, (2, 1), ClassicColor.white)

        self.assertEqual(doubled_pawns(board, ClassicColor.white), 1)

    def test_piece_png_path_points_to_tracked_asset(self):
        board = Board()

        self.assertTrue(Path(to_PNG(board.get((3, 0)))).is_file())

    def test_stream_bot_emits_started_depths_and_final(self):
        import io
        import json as json_module

        class FakeHandler:
            def __init__(self):
                self.wfile = io.BytesIO()
                self.headers = {}
                self.status = None

            def send_response(self, status):
                self.status = status

            def send_header(self, key, value):
                self.headers[key] = value

            def end_headers(self):
                pass

        payload = {
            "board": {
                "dimension": 2,
                "size": [8, 8],
                "turn": "white",
                "pieces": [
                    {"kind": "king", "color": "white", "position": [7, 7], "hasMoved": False},
                    {"kind": "king", "color": "black", "position": [7, 0], "hasMoved": False},
                    {"kind": "rook", "color": "white", "position": [0, 0], "hasMoved": False},
                    {"kind": "queen", "color": "black", "position": [0, 5], "hasMoved": False},
                ],
            },
            "color": "white",
            "depth": 2,
            "timeLimitMs": 1500,
        }
        handler_obj = FakeHandler()

        stream_bot_move(handler_obj, payload, request_id="req-1")

        self.assertEqual(handler_obj.status, 200)
        self.assertEqual(handler_obj.headers["Content-Type"], "application/x-ndjson; charset=utf-8")
        lines = [
            json_module.loads(line)
            for line in handler_obj.wfile.getvalue().decode().splitlines()
            if line
        ]
        types = [event["type"] for event in lines]
        self.assertEqual(types[0], "started")
        self.assertEqual(types[-1], "final")
        depth_events = [event for event in lines if event["type"] == "depth"]
        self.assertGreaterEqual(len(depth_events), 1)
        self.assertEqual([event["depth"] for event in depth_events], sorted({event["depth"] for event in depth_events}))
        for event in depth_events:
            self.assertIn("mateIn", event)
        final = lines[-1]
        self.assertIn("mateIn", final)
        self.assertEqual(final["move"], {"from": [0, 0], "to": [0, 5]})
        self.assertEqual(final["board"]["turn"], "black")

    def test_bot_api_returns_engine_move(self):
        payload = {
            "board": {
                "dimension": 2,
                "size": [8, 8],
                "turn": "white",
                "pieces": [
                    {"kind": "king", "color": "white", "position": [7, 7], "hasMoved": False},
                    {"kind": "king", "color": "black", "position": [7, 0], "hasMoved": False},
                    {"kind": "rook", "color": "white", "position": [0, 0], "hasMoved": False},
                    {"kind": "queen", "color": "black", "position": [0, 5], "hasMoved": False},
                ],
            },
            "color": "white",
            "depth": 1,
        }

        response = choose_bot_move(payload)

        self.assertEqual(response["move"], {"from": [0, 0], "to": [0, 5]})
        self.assertEqual(response["board"]["turn"], "black")

    def test_legal_moves_api_returns_python_moves(self):
        payload = {
            "board": {
                "dimension": 2,
                "size": [8, 8],
                "turn": "white",
                "pieces": [
                    {"kind": "king", "color": "white", "position": [4, 0], "hasMoved": False},
                    {"kind": "rook", "color": "white", "position": [0, 0], "hasMoved": False},
                    {"kind": "king", "color": "black", "position": [4, 7], "hasMoved": False},
                ],
            },
            "position": [0, 0],
        }

        response = legal_moves_api.legal_moves_request(payload)

        self.assertIn({"from": [0, 0], "to": [0, 1]}, response["moves"])

    def test_move_api_applies_python_move(self):
        payload = {
            "board": {
                "dimension": 2,
                "size": [8, 8],
                "turn": "white",
                "pieces": [
                    {"kind": "king", "color": "white", "position": [4, 0], "hasMoved": False},
                    {"kind": "rook", "color": "white", "position": [0, 0], "hasMoved": False},
                    {"kind": "king", "color": "black", "position": [4, 7], "hasMoved": False},
                ],
            },
            "move": {"from": [0, 0], "to": [0, 1]},
        }

        response = move_request(payload)

        self.assertEqual(response["board"]["turn"], "black")
        self.assertIn(
            {"id": "white-rook-0,1", "kind": "rook", "color": "white", "position": [0, 1], "hasMoved": True},
            response["board"]["pieces"],
        )

    def test_evaluate_api_returns_white_score(self):
        payload = {
            "board": {
                "dimension": 2,
                "size": [8, 8],
                "turn": "white",
                "pieces": [
                    {"kind": "king", "color": "white", "position": [7, 7], "hasMoved": False},
                    {"kind": "king", "color": "black", "position": [7, 0], "hasMoved": False},
                    {"kind": "rook", "color": "white", "position": [0, 0], "hasMoved": False},
                    {"kind": "queen", "color": "black", "position": [0, 5], "hasMoved": False},
                ],
            },
            "color": "white",
            "searchDepth": 0,
        }

        response = evaluate_request(payload)

        self.assertIn("whiteScore", response)
        self.assertIsInstance(response["whiteScore"], float)
        self.assertIn("mateIn", response)
        self.assertIsNone(response["mateIn"])

    def test_evaluate_api_reports_mate_in_one(self):
        payload = {
            "board": {
                "dimension": 2,
                "size": [8, 8],
                "turn": "white",
                "pieces": [
                    {"kind": "king", "color": "white", "position": [4, 0], "hasMoved": False},
                    {"kind": "rook", "color": "white", "position": [0, 6], "hasMoved": False},
                    {"kind": "rook", "color": "white", "position": [1, 7], "hasMoved": False},
                    {"kind": "king", "color": "black", "position": [4, 7], "hasMoved": False},
                ],
            },
            "color": "white",
            "searchDepth": 2,
            "searchTimeMs": 1500,
        }

        response = evaluate_request(payload)

        self.assertEqual(response["mateIn"], 1)
        self.assertGreater(response["searchScore"], MATE_THRESHOLD)

    def test_bot_api_returns_mate_in_field(self):
        payload = {
            "board": {
                "dimension": 2,
                "size": [8, 8],
                "turn": "white",
                "pieces": [
                    {"kind": "king", "color": "white", "position": [4, 0], "hasMoved": False},
                    {"kind": "rook", "color": "white", "position": [0, 6], "hasMoved": False},
                    {"kind": "rook", "color": "white", "position": [1, 7], "hasMoved": False},
                    {"kind": "king", "color": "black", "position": [4, 7], "hasMoved": False},
                ],
            },
            "color": "white",
            "depth": 1,
        }

        response = choose_bot_move(payload)

        self.assertIn("mateIn", response)
        self.assertEqual(response["mateIn"], 1)


class EngineSearchTests(unittest.TestCase):
    def tactical_board(self):
        board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black))
        board.add(King, (7, 7), ClassicColor.white)
        board.add(King, (7, 0), ClassicColor.black)
        board.add(Rook, (0, 0), ClassicColor.white)
        board.add(Queen, (0, 5), ClassicColor.black)
        return board

    def test_legal_moves_default_to_current_turn(self):
        board = self.tactical_board()

        self.assertTrue(all(board.get(move.initial_position).color == ClassicColor.white for move in legal_moves(board)))

    def test_find_best_move_prefers_capturing_hanging_queen(self):
        result = find_best_move(self.tactical_board(), depth=1)

        self.assertEqual(result.move, Move((0, 0), (0, 5)))
        self.assertGreater(result.score, 0)
        self.assertGreater(result.nodes, 1)

    def test_best_move_supports_no_turn_board_when_color_is_supplied(self):
        board = nBoard(2, (8, 8))
        board.add(King, (7, 7), ClassicColor.white)
        board.add(King, (7, 0), ClassicColor.black)
        board.add(Rook, (0, 0), ClassicColor.white)
        board.add(Queen, (0, 5), ClassicColor.black)

        with self.assertRaises(ValueError):
            best_move(board, depth=1)

        self.assertEqual(best_move(board, depth=1, color=ClassicColor.white), Move((0, 0), (0, 5)))

    def test_engine_does_not_walk_king_out_in_middlegame(self):
        # A quiet middlegame-ish position where the king has a legal move to
        # the next rank. Before the king-safety eval fix, the engine
        # preferred King (3,0)->(3,1) at depth 3 because centrality and
        # activity_metrics each rewarded the king for becoming "central"
        # and "mobile". The fix removes the king from centrality, removes
        # king moves from activity, and adds a king-displacement penalty
        # scaled by remaining material.
        board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black))
        board.add(King, (3, 0), ClassicColor.white)
        board.add(Rook, (0, 0), ClassicColor.white)
        board.add(Rook, (7, 0), ClassicColor.white)
        board.add(Bishop, (5, 1), ClassicColor.white)
        board.add(Knight, (6, 0), ClassicColor.white)
        for f in (0, 1, 2, 4, 6, 7):
            board.add(Pawn, (f, 1), ClassicColor.white)
        board.add(Pawn, (3, 3), ClassicColor.white)
        board.add(King, (3, 7), ClassicColor.black)
        board.add(Rook, (0, 7), ClassicColor.black)
        board.add(Rook, (7, 7), ClassicColor.black)
        board.add(Bishop, (5, 6), ClassicColor.black)
        board.add(Knight, (6, 7), ClassicColor.black)
        for f in (0, 1, 2, 4, 6, 7):
            board.add(Pawn, (f, 6), ClassicColor.black)
        board.add(Pawn, (3, 4), ClassicColor.black)

        for depth in (1, 2, 3):
            result = find_best_move(board, depth=depth, color=ClassicColor.white)
            moving_piece_type = type(board.get(result.move.initial_position))
            self.assertIsNot(
                moving_piece_type,
                King,
                msg=f"Engine walked the king at depth {depth}: {result.move}",
            )

    def test_engine_finds_back_rank_mate_in_one(self):
        board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black))
        board.add(King, (4, 0), ClassicColor.white)
        board.add(Rook, (0, 6), ClassicColor.white)
        board.add(Rook, (1, 7), ClassicColor.white)
        board.add(King, (4, 7), ClassicColor.black)

        result = find_best_move(board, depth=1, color=ClassicColor.white)
        new_board = board.assume_move(result.move)
        self.assertTrue(new_board.in_checkmate(ClassicColor.black))

    def test_iterative_deepening_streams_each_depth(self):
        board = self.tactical_board()
        snapshots = []
        iterative_deepening(
            board,
            max_depth=3,
            color=ClassicColor.white,
            evaluator=evaluate_position,
            time_limit_ms=10_000,
            on_depth_complete=lambda result: snapshots.append(result.depth),
        )

        self.assertEqual(snapshots, [1, 2, 3])

    def test_transposition_table_short_circuits_repeat_searches(self):
        board = self.tactical_board()
        context = SearchContext(0.0, deadline_ms=None)

        first_score, first_nodes = negamax(
            board,
            depth=2,
            color=ClassicColor.white,
            evaluator=evaluate_position,
            context=context,
        )
        second_score, second_nodes = negamax(
            board,
            depth=2,
            color=ClassicColor.white,
            evaluator=evaluate_position,
            context=context,
        )

        self.assertEqual(first_score, second_score)
        self.assertEqual(second_nodes, 1)

    def test_transposition_entries_have_bound_metadata(self):
        board = self.tactical_board()
        context = SearchContext(0.0, deadline_ms=None)

        negamax(
            board,
            depth=2,
            color=ClassicColor.white,
            evaluator=evaluate_position,
            context=context,
        )

        entry = context.transpositions[(position_key(board), ClassicColor.white)]
        self.assertIsInstance(entry, TTEntry)
        self.assertIn(entry.bound, {EXACT, LOWER, UPPER})
        self.assertIsNotNone(entry.best_move)


class EvaluationKingSafetyTests(unittest.TestCase):
    def _two_king_board(self, white_king_position):
        # The only piece that differs between calls is the white king's
        # square, so any change in centrality / activity must come from
        # the king itself.
        board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black))
        board.add(King, white_king_position, ClassicColor.white)
        board.add(King, (3, 7), ClassicColor.black)
        return board

    def test_centrality_excludes_king(self):
        # The king should not influence centrality at all — only non-king
        # pieces are central candidates.
        home = self._two_king_board((3, 0))
        walked = self._two_king_board((3, 4))

        self.assertEqual(
            centrality(home, ClassicColor.white),
            centrality(walked, ClassicColor.white),
        )

    def test_activity_metrics_excludes_king_moves(self):
        # Same board with the king on a more open square yields the same
        # activity count, because king mobility no longer contributes.
        boxed = self._two_king_board((3, 0))
        open_square = self._two_king_board((3, 4))

        boxed_moves, _ = activity_metrics(boxed, ClassicColor.white)
        open_moves, _ = activity_metrics(open_square, ClassicColor.white)
        self.assertEqual(boxed_moves, open_moves)

    def test_endgame_factor_full_board_is_zero(self):
        board = Board()
        self.assertAlmostEqual(endgame_factor(board, ClassicColor.white, ClassicColor.black), 0.0, places=5)

    def test_endgame_factor_bare_kings_is_one(self):
        board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black))
        board.add(King, (3, 0), ClassicColor.white)
        board.add(King, (3, 7), ClassicColor.black)
        self.assertAlmostEqual(endgame_factor(board, ClassicColor.white, ClassicColor.black), 1.0, places=5)

    def test_king_safety_penalises_displaced_king_in_middlegame(self):
        # Need real material on the board so endgame_factor < 1; otherwise
        # the displacement penalty is fully dampened.
        def position_with_king_on(rank):
            board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black))
            board.add(King, (3, rank), ClassicColor.white)
            board.add(King, (3, 7), ClassicColor.black)
            board.add(Queen, (4, 0), ClassicColor.white)
            board.add(Rook, (0, 0), ClassicColor.white)
            board.add(Rook, (7, 0), ClassicColor.white)
            board.add(Queen, (4, 7), ClassicColor.black)
            board.add(Rook, (0, 7), ClassicColor.black)
            board.add(Rook, (7, 7), ClassicColor.black)
            for f in range(8):
                board.add(Pawn, (f, 6), ClassicColor.black)
            for f in (0, 1, 2, 4, 5, 6, 7):
                board.add(Pawn, (f, 2), ClassicColor.white)
            return board

        home = position_with_king_on(0)
        walked = position_with_king_on(3)

        home_score = king_safety(home, ClassicColor.white, ClassicColor.black)
        walked_score = king_safety(walked, ClassicColor.white, ClassicColor.black)
        self.assertLess(walked_score, home_score)


class MateScoreTests(unittest.TestCase):
    def test_mate_distance_returns_none_for_normal_scores(self):
        self.assertIsNone(mate_distance(0))
        self.assertIsNone(mate_distance(12.5))
        self.assertIsNone(mate_distance(-9.0))

    def test_mate_distance_recovers_plies_to_mate(self):
        # MATE_SCORE - p == score, so mate_distance(score) should round-trip p.
        self.assertEqual(mate_distance(MATE_SCORE - 1), 1)
        self.assertEqual(mate_distance(MATE_SCORE - 3), 3)
        self.assertEqual(mate_distance(-(MATE_SCORE - 4)), 4)

    def test_mate_in_moves_uses_ceil_of_plies_over_two(self):
        # The mating side moves N times for an N-move mate (2N-1 plies); the
        # mated side endures (2N-1) plies as well. ``ceil(plies/2)`` is N
        # in either case.
        self.assertEqual(mate_in_moves(MATE_SCORE - 1), 1)
        self.assertEqual(mate_in_moves(MATE_SCORE - 2), 1)
        self.assertEqual(mate_in_moves(MATE_SCORE - 3), 2)
        self.assertEqual(mate_in_moves(MATE_SCORE - 4), 2)
        self.assertEqual(mate_in_moves(MATE_SCORE - 5), 3)

    def test_signed_mate_in_for_white_flips_with_search_color(self):
        # White-to-move, mate-in-1 from white's POV.
        self.assertEqual(signed_mate_in_for_white(MATE_SCORE - 1, "white"), 1)
        # Black-to-move, mate-in-1 from black's POV — i.e. -1 from white's.
        self.assertEqual(signed_mate_in_for_white(MATE_SCORE - 1, "black"), -1)
        # White-to-move, getting mated in 2 — i.e. -2 from white's.
        self.assertEqual(signed_mate_in_for_white(-(MATE_SCORE - 4), "white"), -2)
        self.assertIsNone(signed_mate_in_for_white(0.5, "white"))

    def test_engine_returns_mate_score_for_provable_mate_in_one(self):
        board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black))
        board.add(King, (4, 0), ClassicColor.white)
        board.add(Rook, (0, 6), ClassicColor.white)
        board.add(Rook, (1, 7), ClassicColor.white)
        board.add(King, (4, 7), ClassicColor.black)

        result = find_best_move(board, depth=1, color=ClassicColor.white)

        self.assertGreater(result.score, MATE_THRESHOLD)
        self.assertEqual(mate_in_moves(result.score), 1)


class CheckmateAndStalemateTests(unittest.TestCase):
    def test_back_rank_checkmate_detected(self):
        board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black), turn_number=1)
        board.add(King, (4, 0), ClassicColor.white)
        board.add(Rook, (0, 6), ClassicColor.white)
        board.add(Rook, (0, 7), ClassicColor.white)
        board.add(King, (4, 7), ClassicColor.black)

        self.assertTrue(board.in_check(ClassicColor.black))
        self.assertTrue(board.in_checkmate(ClassicColor.black))
        self.assertFalse(board.in_stalemate(ClassicColor.black))

    def test_corner_stalemate_detected(self):
        board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black), turn_number=1)
        board.add(King, (5, 5), ClassicColor.white)
        board.add(Queen, (6, 5), ClassicColor.white)
        board.add(King, (7, 7), ClassicColor.black)

        self.assertFalse(board.in_check(ClassicColor.black))
        self.assertFalse(board.in_checkmate(ClassicColor.black))
        self.assertTrue(board.in_stalemate(ClassicColor.black))

    def test_in_check_detects_pawn_capture_threat(self):
        board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black))
        board.add(King, (3, 3), ClassicColor.white)
        board.add(Pawn, (2, 4), ClassicColor.black)
        board.add(King, (7, 7), ClassicColor.black)

        # Pawn at (2,4) is black, captures along axis 0; one of its capture
        # squares is (3,3) — the white king's square.
        self.assertTrue(board.in_check(ClassicColor.white))


class MultiDimensionalEngineTests(unittest.TestCase):
    def test_three_d_pawn_promotion_requires_corner(self):
        # Documents current behaviour: in higher dimensions, Pawn.is_promotable
        # only fires when the pawn reaches the far edge in *every* non-capture
        # axis (i.e., a corner of the forward subspace), not when it reaches
        # the far edge in any single forward axis.
        board = nBoard(3, (5, 5, 4), turn_order=(ClassicColor.white, ClassicColor.black))
        board.add(Pawn, (2, 4, 0), ClassicColor.white)
        self.assertFalse(board.get((2, 4, 0)).is_promotable())

        board = nBoard(3, (5, 5, 4), turn_order=(ClassicColor.white, ClassicColor.black))
        board.add(Pawn, (2, 4, 3), ClassicColor.white)
        self.assertTrue(board.get((2, 4, 3)).is_promotable())

    def test_four_d_queen_at_corner_has_many_legal_moves(self):
        board = nBoard(4, (4, 4, 4, 4), turn_order=(ClassicColor.white, ClassicColor.black))
        board.add(Queen, (0, 0, 0, 0), ClassicColor.white)
        board.add(King, (3, 3, 3, 3), ClassicColor.white)
        board.add(King, (3, 3, 0, 0), ClassicColor.black)

        moves = board.get((0, 0, 0, 0)).moves()
        self.assertGreater(len(moves), 30)

    def test_four_d_check_detection(self):
        # Queen on the same 1D ray attacking the king should produce check
        # regardless of dimension.
        board = nBoard(4, (4, 4, 4, 4), turn_order=(ClassicColor.white, ClassicColor.black))
        board.add(King, (0, 0, 0, 0), ClassicColor.white)
        board.add(Queen, (3, 0, 0, 0), ClassicColor.black)
        board.add(King, (3, 3, 3, 3), ClassicColor.black)

        self.assertTrue(board.in_check(ClassicColor.white))


class GuiGeometryTests(unittest.TestCase):
    def test_position_padding_extends_to_four_dimensions(self):
        self.assertEqual(position_padding((1, 2)), (1, 2, 0, 0))
        self.assertEqual(position_padding((1, 2, 3, 4)), (1, 2, 3, 4))

    def test_cell_indices_and_positions_are_inverse(self):
        position = (2, 3)

        row, column = cell_indices_for_position(position)

        self.assertEqual((row, column), (3, 2))
        self.assertEqual(position_for_cell_indices(row, column), position)

    def test_four_dimensional_board_indices_are_inverse(self):
        board_size = (4, 4, 4, 4)
        grid_rows, _ = board_grid_size(4, board_size)
        position = (1, 2, 3, 1)

        row, column = board_indices_for_position(position, 4, grid_rows)
        k, h = board_coordinates_for_indices(row, column, 4, grid_rows)

        self.assertEqual((k, h), position[2:])

    def test_three_dimensional_board_indices_are_inverse(self):
        board_size = (4, 4, 3)
        grid_rows, _ = board_grid_size(3, board_size)
        position = (1, 2, 2)

        row, column = board_indices_for_position(position, 3, grid_rows)
        k, _ = board_coordinates_for_indices(row, column, 3, grid_rows)

        self.assertEqual(k, position[2])


if __name__ == "__main__":
    unittest.main()
