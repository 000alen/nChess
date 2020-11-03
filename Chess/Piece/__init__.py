from abc import ABC, abstractmethod
from typing import Tuple, Type, TypeVar

_Piece = Type["Piece"]
_Color = TypeVar("_Color")
_Position = Tuple[int, ...]


class Piece(ABC):
    """Baseclass for all Pieces."""

    promotions: Tuple[_Piece]

    @classmethod
    def valid_next(
            cls,
            board,
            initial_position: _Position,
            final_position: _Position
    ):
        """Checks if a given position is a valid movement."""
        return final_position in cls.next(board, initial_position)

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
                new_position = tuple(position[i] + (offset[i] * magnitude) for i in range(board.dimension))
                if Piece.no_conflict(board, position, new_position):
                    movements.append(new_position)
                else:
                    break
        return movements

    @staticmethod
    def no_conflict(
            board,
            initial_position: _Position,
            final_position: _Position
    ):
        """Checks if a given position doesn't cause a conflict."""
        return (
                board.in_bounds(final_position)
                and (
                        not board.contains(final_position)
                        or board.get(initial_position).color != board.get(final_position).color
                )
        )

    @staticmethod
    def is_promotion_available(
            board,
            position: _Position
    ):
        """Checks if promotion is available."""
        return False

    @staticmethod
    @abstractmethod
    def next(
            board,
            position: _Position
    ):
        """Returns all the possible movements."""
        raise NotImplementedError
