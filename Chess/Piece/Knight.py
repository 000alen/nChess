from typing import Tuple, Type, TypeVar

from Chess.Piece import Piece

_Piece = Type[Piece]
_Position = Tuple[int, ...]
_Color = TypeVar("_Color")


class Knight(Piece):
    """Implements the Knight piece and its generalization to higher dimensions."""

    is_promotion_available = staticmethod(lambda board, position: False)

    # TODO: Possible implementation using Board.slice
    @staticmethod
    def _unfiltered_movements(
            board,
            position: _Position
    ):
        movements = []
        for offset in board.L:
            final_position = tuple(position[i] + offset[i] for i in range(board.dimension))
            if not board.no_conflict(position, final_position):
                continue
            x_axis, y_axis = (axis for axis, j in enumerate(offset) if j)
            x_direction = 1 if offset[x_axis] > 0 else -1
            y_direction = 1 if offset[y_axis] > 0 else -1
            partial_pieces = 0
            for i in range(0, offset[x_axis] + x_direction, x_direction):
                for j in range(0, offset[y_axis] + y_direction, y_direction):
                    if (i == 0 and j == 0) or (i == offset[x_axis] and j == offset[y_axis]):
                        continue
                    partial_position = tuple(
                        position[k] + i if k == x_axis
                        else position[k] + j if k == y_axis
                        else position[k]
                        for k in range(board.dimension)
                    )
                    if board.contains(partial_position):
                        partial_pieces += 1
            if partial_pieces < 3:
                movements.append(final_position)
        return movements
