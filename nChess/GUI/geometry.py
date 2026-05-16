"""Pure coordinate helpers for mapping n-dimensional board positions to widgets.

Within each 2D layer, model coordinates are `(x, y)` while Kivy grid storage is
`[row][column]`, so these helpers keep the conversion centralized and testable.
"""

from nChess.nBoard import IntegerVector


def position_padding(position: IntegerVector, minimum_dimension: int = 4) -> IntegerVector:
    if len(position) >= minimum_dimension:
        return position
    return (*position, *((0,) * (minimum_dimension - len(position))))


def board_grid_size(dimension: int, board_size: IntegerVector) -> tuple[int, int]:
    if dimension == 2:
        return 1, 1
    if dimension == 3:
        return 1, board_size[2]
    if dimension == 4:
        return board_size[2], board_size[3]
    raise ValueError("nBoardWidget supports dimensions from 2 to 4")


def layer_dimensions(board_size: IntegerVector) -> tuple[int, int]:
    return board_size[1], board_size[0]


def cell_indices_for_position(position: IntegerVector) -> tuple[int, int]:
    return position[1], position[0]


def position_for_cell_indices(row: int, column: int) -> IntegerVector:
    return column, row


def board_indices_for_position(
    position: IntegerVector,
    dimension: int,
    board_grid_rows: int,
) -> tuple[int, int]:
    position = position_padding(position)
    if dimension == 2:
        return 0, 0
    if dimension == 3:
        return 0, position[2]
    if dimension == 4:
        return board_grid_rows - position[2] - 1, position[3]
    raise ValueError("nBoardWidget supports dimensions from 2 to 4")


def board_coordinates_for_indices(
    row: int,
    column: int,
    dimension: int,
    board_grid_rows: int,
) -> IntegerVector:
    if dimension == 2:
        return 0, 0
    if dimension == 3:
        return column, 0
    if dimension == 4:
        return board_grid_rows - row - 1, column
    raise ValueError("nBoardWidget supports dimensions from 2 to 4")
