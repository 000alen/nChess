from abc import ABC, abstractmethod
from typing import Tuple, Type, TypeVar

_Piece = Type["Piece"]
_Color = TypeVar("_Color")
_Position = Tuple[int, ...]


class Piece(ABC):
    """Baseclass for all Pieces."""

    promotions: Tuple[_Piece]

    @staticmethod
    def is_promotion_available(
            board,
            position: _Position
    ):
        """Checks if promotion is available."""
        raise NotImplementedError

    @staticmethod
    def ad_nauseam(
            board,
            position: _Position,
            offsets: Tuple[_Position],
            maximum_magnitude: int
    ):
        """Helper function for adding the offset to the position."""
        movements = []
        for offset in offsets:
            for magnitude in range(1, maximum_magnitude + 1):
                new_position = tuple(
                    position[i] + (offset[i] * magnitude) for i in range(board.dimension))
                if board.no_conflict(position, new_position):
                    movements.append(new_position)
                else:
                    break
        return movements

    @staticmethod
    @abstractmethod
    def _unfiltered_movements(
        board,
        position: _Position
    ):
        raise NotImplementedError

    @classmethod
    def _filtered_movements(
        cls,
        board,
        position: _Position
    ):
        unfiltered_movements = cls._unfiltered_movements(board, position)
        color, _ = board.get(position)
        filtered_movements = []
        for unfiltered_movement in unfiltered_movements:
            assumption_board = board.assumption_movement(position, unfiltered_movement)
            if not assumption_board.in_check(color):
                filtered_movements.append(unfiltered_movement)
        return filtered_movements


    @classmethod
    def movements(
            cls,
            board,
            position: _Position
    ):
        return cls._filtered_movements(board, position)
