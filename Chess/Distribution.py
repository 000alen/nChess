from Chess.Annotation import Color
from Chess.Piece.Bishop import Bishop
from Chess.Piece.King import King
from Chess.Piece.Knight import Knight
from Chess.Piece.Pawn import Pawn
from Chess.Piece.Queen import Queen
from Chess.Piece.Rook import Rook

__all__ = (
    "PawnsRow",
    "RoyaltyRow",
    "Classic"
)

PawnsRow = {
    (i, 0): Pawn
    for i in range(8)
}

RoyaltyRow = {
    (i, 0): piece
    for i, piece in enumerate(
        (Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook)
    )
}

Classic = {
    Color.WHITE: {
        **{
            (i, 1): piece for (i, _), piece in PawnsRow.items()
        },
        **RoyaltyRow
    },
    Color.BLACK: {
        **{
            (i, 1): piece for (i, _), piece in PawnsRow.items()
        },
        **RoyaltyRow
    }
}
