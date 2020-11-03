from typing import Tuple, Type, TypeVar

from Chess.Piece import Piece

_Piece = Type[Piece]
_Position = Tuple[int, ...]
_Color = TypeVar("_Color")


class Knight(Piece):
    """Implements the Knight piece and its generalization to higher dimensions."""

    @staticmethod
    def next(
            board,
            position: _Position
    ):
        movements = []
        for offset in board.L:
            final_position = tuple(position[i] + offset[i] for i in range(board.dimension))
            if not Knight.no_conflict(board, position, final_position):
                continue
            x, y = (i for i, j in enumerate(offset) if j)
            partial_pieces = 0
            for i in range(0, offset[x] + (1 if offset[x] > 0 else -1), 1 if offset[x] > 0 else -1):
                for j in range(0, offset[y] + (1 if offset[x] > 0 else -1), 1 if offset[y] > 0 else -1):
                    if (i == 0 and j == 0) or (i == offset[x] and j == offset[y]):
                        continue
                    partial_position = tuple(
                        position[k] + i if k == x
                        else position[k] + j if k == y
                        else position[k]
                        for k in range(board.dimension)
                    )
                    if board.contains(partial_position):
                        partial_pieces += 1
            if partial_pieces < 3:
                movements.append(final_position)
        return movements
