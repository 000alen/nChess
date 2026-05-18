"""Engine performance / capability audit harness.

Runs cProfile on a representative search, microbenchmarks the hottest
primitives, exercises a small tactical suite at various depths, and
reports per-dimension search costs.
"""
import argparse
import cProfile
import pstats
import sys
from io import StringIO
from time import perf_counter

from nChess.nBoard import nBoard
from nChess.nBoard.Board import Board, ClassicColor
from nChess.Piece import Move
from nChess.Piece.Bishop import Bishop
from nChess.Piece.King import King
from nChess.Piece.Knight import Knight
from nChess.Piece.Pawn import Pawn
from nChess.Piece.Queen import Queen
from nChess.Piece.Rook import Rook
from nChess.Engine import (
    SearchContext,
    activity_metrics,
    evaluate_position,
    find_best_move,
    iterative_deepening,
    legal_moves,
)


def section(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def time_call(func, repeats=1):
    start = perf_counter()
    for _ in range(repeats):
        result = func()
    elapsed = (perf_counter() - start) * 1000
    return result, elapsed


def benchmark_primitives():
    section("1. Primitive microbenchmarks (classic 8x8 starting position)")
    board = Board()

    _, t = time_call(lambda: legal_moves(board), repeats=20)
    print(f"  legal_moves(white)               x20 -> {t:7.1f} ms total | {t/20:6.2f} ms/call")

    _, t = time_call(lambda: board.in_check(ClassicColor.white), repeats=200)
    print(f"  board.in_check(white)            x200 -> {t:7.1f} ms total | {t/200:6.3f} ms/call")

    _, t = time_call(lambda: board.in_checkmate(ClassicColor.white), repeats=20)
    print(f"  board.in_checkmate(white)        x20 -> {t:7.1f} ms total | {t/20:6.2f} ms/call")

    move = Move((0, 1), (0, 3))
    _, t = time_call(lambda: board.assume_move(move), repeats=2000)
    print(f"  board.assume_move (a-pawn x2)    x2000 -> {t:7.1f} ms total | {t/2000:6.3f} ms/call")

    _, t = time_call(lambda: evaluate_position(board, ClassicColor.white), repeats=50)
    print(f"  evaluate_position(white)         x50 -> {t:7.1f} ms total | {t/50:6.2f} ms/call")

    _, t = time_call(lambda: activity_metrics(board, ClassicColor.white), repeats=200)
    print(f"  activity_metrics(white)          x200 -> {t:7.1f} ms total | {t/200:6.3f} ms/call")


def profile_search():
    section("2. cProfile of iterative_deepening depth=3 on classic 8x8")
    board = Board()
    profiler = cProfile.Profile()
    profiler.enable()
    result = iterative_deepening(
        board,
        max_depth=3,
        color=ClassicColor.white,
        evaluator=evaluate_position,
        time_limit_ms=10_000,
    )
    profiler.disable()
    print(
        f"  -> reached depth {result.depth}, score {result.score:.3f}, "
        f"nodes {result.nodes}, search {result.elapsed_ms:.0f} ms"
    )
    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream).sort_stats("cumulative")
    stats.print_stats(18)
    print(stream.getvalue())


def tactical_board(): 
    board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black))
    board.add(King, (7, 7), ClassicColor.white)
    board.add(King, (7, 0), ClassicColor.black)
    board.add(Rook, (0, 0), ClassicColor.white)
    board.add(Queen, (0, 5), ClassicColor.black)
    return board


def back_rank_mate_in_one():
    board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black))
    board.add(King, (4, 0), ClassicColor.white)
    board.add(Rook, (0, 6), ClassicColor.white)
    board.add(Rook, (1, 7), ClassicColor.white)
    board.add(King, (4, 7), ClassicColor.black)
    return board, Move((1, 7), (4, 7)) is None  # accept any mating move


def fork_mate_in_two():
    board = nBoard(2, (8, 8), turn_order=(ClassicColor.white, ClassicColor.black))
    board.add(King, (6, 0), ClassicColor.white)
    board.add(Queen, (4, 4), ClassicColor.white)
    board.add(Rook, (0, 6), ClassicColor.white)
    board.add(King, (4, 7), ClassicColor.black)
    return board


def tactical_suite():
    section("3. Tactical capability — depths 1..3 on small positions")
    cases = [
        ("HangingQueen 8x8 (capture wins)", tactical_board()),
        ("BackRankMate 8x8 (mate-in-1)", back_rank_mate_in_one()[0]),
        ("FreeRoaming 8x8 (no win)", fork_mate_in_two()),
    ]
    for name, board in cases:
        for depth in (1, 2, 3):
            t0 = perf_counter()
            result = find_best_move(board, depth=depth, color=ClassicColor.white)
            elapsed = (perf_counter() - t0) * 1000
            move = "—" if result.move is None else (
                f"{result.move.initial_position}->{result.move.final_position}"
            )
            new_board = board.assume_move(result.move) if result.move else board
            mate = new_board.in_checkmate(ClassicColor.black) if result.move else False
            print(
                f"  {name:38s} d={depth} t={elapsed:7.1f}ms "
                f"score={result.score:7.2f} nodes={result.nodes:5d} "
                f"move={move:20s} mate?={mate}"
            )


def dimension_perf():
    section("4. Multi-dimensional search cost")
    boards = []

    classic = Board()
    boards.append(("classic 2D 8x8 (start)", classic))

    b3d = nBoard(3, (5, 5, 4), turn_order=(ClassicColor.white, ClassicColor.black))
    b3d.add(King, (4, 4, 3), ClassicColor.white)
    b3d.add(King, (0, 0, 0), ClassicColor.black)
    b3d.add(Pawn, (1, 1, 0), ClassicColor.white)
    b3d.add(Pawn, (1, 2, 1), ClassicColor.black)
    b3d.add(Queen, (3, 3, 1), ClassicColor.white)
    boards.append(("3D 5x5x4 sparse", b3d))

    b4d = nBoard(4, (4, 4, 4, 4), turn_order=(ClassicColor.white, ClassicColor.black))
    b4d.add(King, (3, 3, 3, 3), ClassicColor.white)
    b4d.add(King, (0, 0, 0, 0), ClassicColor.black)
    b4d.add(Queen, (1, 1, 1, 1), ClassicColor.white)
    b4d.add(Bishop, (2, 2, 2, 2), ClassicColor.black)
    b4d.add(Knight, (0, 2, 0, 2), ClassicColor.white)
    b4d.add(Rook, (3, 0, 0, 0), ClassicColor.black)
    boards.append(("4D 4^4 sparse", b4d))

    for name, board in boards:
        for depth in (1, 2, 3):
            t0 = perf_counter()
            result = find_best_move(board, depth=depth, color=ClassicColor.white)
            elapsed = (perf_counter() - t0) * 1000
            print(
                f"  {name:25s} depth={depth} t={elapsed:8.1f}ms nodes={result.nodes:6d}"
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-profile", action="store_true")
    args = parser.parse_args()
    benchmark_primitives()
    if not args.skip_profile:
        profile_search()
    tactical_suite()
    dimension_perf()


if __name__ == "__main__":
    main()
