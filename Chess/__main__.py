from Chess.Annotation import Color
from Chess.Board import Board


def show_board(_board):
    print(" " + "".join(str(i + 1) for i in range(_board.size)))
    for i in range(8):
        for j in range(8):
            if j == 0:
                print(i + 1, end="")
            print(str(_board.get((i, j))) if _board.contains((i, j)) else " ", end="")
        print()


board = Board()
while True:
    print(board.turn)
    show_board(board)
    start, end = tuple(
        tuple(
            int(i) - 1
            for i in position
        )
        for position in input("> ").split()
    )

    target = board.get(start) if board.contains(start) else None
    if target is not None:
        print(target.available_next())
        if target.color is board.turn and target.is_valid_next(end):
            board.move(start, end)
            if board.is_check(Color.WHITE):
                pass
            if board.is_check(Color.BLACK):
                pass
            # board.next_turn()
