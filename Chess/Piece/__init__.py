from typing import Tuple, List


class Piece:
    """Baseclass for all Pieces."""

    @classmethod
    def valid_next(cls, board, initial_position: Tuple[int, ...], final_position: Tuple[int, ...], color):
        return final_position in cls.next(board, initial_position, color)

    @staticmethod
    def ad_nauseam(board, position: Tuple[int, ...], color, offsets: List[Tuple[int, ...]], maximum_magnitude: int):
        movements = []
        for offset in offsets:
            for magnitude in range(1, maximum_magnitude + 1):
                new_position = tuple(position[i] + (offset[i] * magnitude) for i in range(board.dimension))
                # noinspection PyTypeChecker
                if Piece.no_conflict(board, position, new_position, color):
                    movements.append(new_position)
        return movements

    @staticmethod
    def no_conflict(board, initial_position: Tuple[int, ...], final_position: Tuple[int, ...], color):
        return (
                board.in_bounds(final_position)
                and (
                        not board.contains(final_position)
                        or color != board.get(final_position)[0]
                )
        )

    @staticmethod
    def next(board, position: Tuple, color):
        raise NotImplementedError
