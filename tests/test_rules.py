import unittest
from pathlib import Path

from nChess.Engine import classic_evaluate
from nChess.nBoard import nBoard
from nChess.nBoard.Board import Board, ClassicColor
from nChess.Piece import Move, PieceData
from nChess.Piece.King import King
from nChess.Piece.Pawn import Pawn
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

    def test_diagonals_include_all_axis_combinations(self):
        diagonals = nBoard.compute_diagonals(3)

        self.assertIn((1, 0, 1), diagonals)
        self.assertIn((-1, 0, 1), diagonals)


class IntegrationSmokeTests(unittest.TestCase):
    def test_engine_evaluates_classic_board(self):
        self.assertEqual(classic_evaluate(Board(), ClassicColor.white), 0)

    def test_piece_png_path_points_to_tracked_asset(self):
        board = Board()

        self.assertTrue(Path(to_PNG(board.get((3, 0)))).is_file())


if __name__ == "__main__":
    unittest.main()
