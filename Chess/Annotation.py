from enum import Enum, auto
from typing import Tuple, Dict, List

__all__ = (
    "Color",
    "PositionType",
    "BoardType",
    "DistributionType",
    "RepresentationType"
)


class Color(Enum):
    WHITE = auto()
    BLACK = auto()


PositionType = Tuple[int, ...]
BoardType = List["Piece"]
DistributionType = Dict[Color, Dict[PositionType, "Piece"]]
RepresentationType = Dict[Color, str]
