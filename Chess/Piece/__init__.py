from typing import Tuple, List, Type


class Piece:
    """Baseclass for all Pieces."""

    promotions: List[Type["Piece"]]

    @classmethod
    def valid_next(cls, board, initial_position: Tuple[int, ...], final_position: Tuple[int, ...], color):
        """Checks if a given position is a valid movement."""
        return final_position in cls.next(board, initial_position, color)

    @staticmethod
    def ad_nauseam(board, position: Tuple[int, ...], color, offsets: List[Tuple[int, ...]], maximum_magnitude: int):
        """Helper function for adding the offset to the position."""
        movements = []
        for offset in offsets:
            for magnitude in range(1, maximum_magnitude + 1):
                new_position = tuple(position[i] + (offset[i] * magnitude) for i in range(board.dimension))
                # noinspection PyTypeChecker
                if Piece.no_conflict(board, position, new_position, color):
                    movements.append(new_position)
                else:
                    break
        return movements

    @staticmethod
    def no_conflict(board, initial_position: Tuple[int, ...], final_position: Tuple[int, ...], color):
        """Checks if a given position doesn't cause a conflict."""
        return (
                board.in_bounds(final_position)
                and (
                        not board.contains(final_position)
                        or color != board.get(final_position)[0]
                )
        )

    @staticmethod
    def is_promotion_available(board, position: Tuple[int, ...], color):
        """Checks if promotion is available."""
        return False

    @staticmethod
    def next(board, position: Tuple, color):
        """Returns all the possible movements."""
        raise NotImplementedError
