import unittest
from pathlib import Path

from api.bot import choose_bot_move
from nChess.Engine import best_move, classic_evaluate, doubled_pawns, find_best_move, legal_moves
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
from nChess.Piece.King import King
from nChess.Piece.Knight import Knight
from nChess.Piece.Pawn import Pawn
from nChess.Piece.Queen import Queen
from nChess.Piece.Rook import Rook
from nChess.utils import to_PNG


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

    def test_doubled_pawns_count_extra_pawns_on_same_file(self):
        board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black))
        board.add(Pawn, (0, 1), ClassicColor.white)
        board.add(Pawn, (0, 3), ClassicColor.white)
        board.add(Pawn, (2, 1), ClassicColor.white)

        self.assertEqual(doubled_pawns(board, ClassicColor.white), 1)

    def test_piece_png_path_points_to_tracked_asset(self):
        board = Board()

        self.assertTrue(Path(to_PNG(board.get((3, 0)))).is_file())

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
