from typing import Tuple

from Chess.Board import Board, Color


class TurnBoard(Board):
    turn: Color

    def __init__(self, size: int = 8, dimension: int = 2, turn: Color = Color.WHITE):
        super().__init__(size, dimension)
        self.turn = turn

    def move(self, initial_position: Tuple[int, ...], final_position: Tuple[int, ...]):
        assert self.contains(initial_position)
        color, piece = self.get(initial_position)
        assert color == self.turn
        self.turn = Color.BLACK if self.turn is Color.WHITE else Color.WHITE
        super().move(initial_position, final_position)
