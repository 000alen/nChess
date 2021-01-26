from typing import Tuple

_Position = Tuple[int, ...]


class InvalidBoardSize(ValueError):
    def __init__(self, invalid_size: int):
        self.message = f"Invalid Board size ({invalid_size}). Board size must be at least 1."
        super().__init__(self.message)


class InvalidBoardDimension(ValueError):
    def __init__(self, invalid_dimension: int):
        self.message = f"Invalid Board dimension ({invalid_dimension}). Board dimension must be at least 1."
        super().__init__(self.message)


class InvalidBoardTurnOrder(ValueError):
    def __init__(self, invalid_turn_order):
        self.message = f"Invalid Board turn order (length {len(invalid_turn_order)}). Board turn order length must be" \
                       f" at least 1."
        super().__init__(self.message)


class InvalidPosition(ValueError):
    def __init__(self, invalid_position: _Position, expected_size: int, expected_dimension: int):
        self.message = f"Unexpected position of dimension {len(invalid_position)}. Expected dimension: " \
                       f"{expected_dimension}. Expected component range: [0, {expected_size}]"
        super().__init__(self.message)


class SelectionOverlapping(Exception):
    def __init__(self, original_position: _Position, overlapping_position: _Position, from_dimension: int, to_dimension: int):
        self.message = f"Cannot perform selection from {from_dimension} to {to_dimension} dimensions. Overlapping " \
                       f"pieces at {overlapping_position} (original: {original_position})."
        super().__init__(self.message)
