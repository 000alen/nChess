from unittest import TestCase

from Chess.Board import Board, Color
from Chess.Piece import Piece
from Chess.Piece.Queen import Queen


class TestBoard(TestCase):
    def test_add(self):
        board = Board(4, 2)

        for i in range(4):
            for j in range(4):
                board.add(Piece, (i, j), Color.BLACK if i % 2 else Color.WHITE)
        self.assertEqual(len(board.board), 16)

        for i in range(4):
            for j in range(4):
                self.assertTrue((i, j) in board.board)
                self.assertEqual(Color.BLACK if i % 2 else Color.WHITE, board.board[(i, j)][0])
                self.assertEqual(Piece, board.board[(i, j)][1])

    def test_contains(self):
        board = Board(4, 2)

        for i in range(4):
            for j in range(4):
                board.add(Piece, (i, j), Color.BLACK if i % 2 else Color.WHITE)

        for i in range(4):
            for j in range(4):
                self.assertTrue(board.contains((i, j)))

    def test_get(self):
        board = Board(4, 2)

        for i in range(4):
            for j in range(4):
                board.add(Piece, (i, j), Color.BLACK if i % 2 else Color.WHITE)

        for i in range(4):
            for j in range(4):
                self.assertEqual(Color.BLACK if i % 2 else Color.WHITE, board.get((i, j))[0])

    def test_move(self):
        board = Board(4, 2)

        board.add(Queen, (0, 0), Color.WHITE)
        board.add(Queen, (3, 3), Color.BLACK)

        self.assertEqual(2, len(board.board))

        board.move((0, 0), (3, 3))

        self.assertEqual(1, len(board.board))

    def test_remove(self):
        board = Board(4, 2)

        board.add(Queen, (0, 0), Color.WHITE)
        board.add(Queen, (3, 3), Color.BLACK)

        self.assertEqual(2, len(board.board))

        board.remove((3, 3))

        self.assertEqual(1, len(board.board))

    def test_in_bounds(self):
        board = Board(4, 2)

        for i in range(4):
            for j in range(4):
                self.assertTrue(board.in_bounds((i, j)))
