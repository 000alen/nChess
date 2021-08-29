from nChess.Board import Board, IntegerVector, Move
from nChess.Piece import Piece


class Knight(Piece):
    """Implements the Knight piece and its generalization to higher dimensions."""

    is_promotable = staticmethod(lambda: False)

    # TODO: Possible implementation using Board.slice
    def all_moves(self) -> tuple["Move", ...]:
        moves = []
        for offset in self.board.L:
            move = Move(self.position, tuple(self.position[i] + offset[i] for i in range(self.board.dimension)))
            if self.board.move_in_conflict(move):
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
                        self.position[k] + i if k == x_axis
                        else self.position[k] + j if k == y_axis
                        else self.position[k]
                        for k in range(self.board.dimension)
                    )
                    if self.board.contains(partial_position):
                        partial_pieces += 1
            if partial_pieces < 3:
                moves.append(move)
        return moves
