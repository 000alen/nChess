export type PieceColor = "white" | "black";
export type PieceKind = "king" | "queen" | "rook" | "bishop" | "knight" | "pawn";
export type Position = readonly number[];
export type BoardDimension = 2 | 3 | 4;

export type BoardConfig = {
  dimension: BoardDimension;
  size: Position;
};

export type Piece = {
  id: string;
  kind: PieceKind;
  color: PieceColor;
  position: Position;
  hasMoved: boolean;
};

export type Move = {
  from: Position;
  promotion?: Exclude<PieceKind, "king" | "pawn">;
  to: Position;
};

export type BoardState = {
  dimension: number;
  hash?: string;
  size: Position;
  pieces: Piece[];
  turn: PieceColor;
};

export const DEFAULT_BOARD_CONFIG: BoardConfig = {
  dimension: 4,
  size: [4, 4, 4, 4],
};

export const PIECE_VALUES: Record<PieceKind, number> = {
  king: 200,
  queen: 9,
  rook: 5,
  bishop: 3,
  knight: 3,
  pawn: 1,
};

export const PIECE_SYMBOLS: Record<PieceColor, Record<PieceKind, string>> = {
  white: {
    king: "♔",
    queen: "♕",
    rook: "♖",
    bishop: "♗",
    knight: "♘",
    pawn: "♙",
  },
  black: {
    king: "♚",
    queen: "♛",
    rook: "♜",
    bishop: "♝",
    knight: "♞",
    pawn: "♟",
  },
};

export function createInitialBoard(config: BoardConfig = DEFAULT_BOARD_CONFIG): BoardState {
  const normalizedConfig = normalizeBoardConfig(config);
  const pieces: Piece[] = [];
  const { dimension, size } = normalizedConfig;
  const blackBackRank = backRankKinds(size[0]);
  const whiteBackRank = backRankKinds(size[0]);

  for (let x = 0; x < size[0]; x += 1) {
    pieces.push(createPiece("pawn", "white", positionForSetup(size, x, 1, "white")));
  }
  for (let x = 0; x < size[0]; x += 1) {
    pieces.push(createPiece(whiteBackRank[x], "white", positionForSetup(size, x, 0, "white")));
  }

  for (let x = 0; x < size[0]; x += 1) {
    pieces.push(createPiece("pawn", "black", positionForSetup(size, x, size[1] - 2, "black")));
  }
  for (let x = 0; x < size[0]; x += 1) {
    pieces.push(createPiece(blackBackRank[x], "black", positionForSetup(size, x, size[1] - 1, "black")));
  }

  return {
    dimension,
    size,
    pieces,
    turn: "white",
  };
}

export function normalizeBoardConfig(config: BoardConfig): BoardConfig {
  const dimension = clampInteger(config.dimension, 2, 4) as BoardDimension;
  const size = Array.from({ length: dimension }, (_, axis) => (
    clampInteger(config.size[axis] ?? 4, 4, 12)
  ));

  return { dimension, size };
}

function positionForSetup(size: Position, x: number, y: number, color: PieceColor): Position {
  return size.map((axisSize, axis) => {
    if (axis === 0) {
      return x;
    }
    if (axis === 1) {
      return y;
    }
    return color === "white" ? 0 : axisSize - 1;
  });
}

function backRankKinds(width: number): PieceKind[] {
  const kinds: PieceKind[] = Array.from({ length: width }, (_, index) => (
    index % 2 === 0 ? "bishop" : "knight"
  ));
  kinds[0] = "rook";
  kinds[width - 1] = "rook";

  const kingFile = Math.max(1, Math.floor((width - 2) / 2));
  const queenFile = Math.min(width - 2, kingFile + 1);
  kinds[kingFile] = "king";
  kinds[queenFile] = "queen";

  return kinds;
}

function clampInteger(value: number, min: number, max: number): number {
  if (!Number.isFinite(value)) {
    return min;
  }
  return Math.max(min, Math.min(max, Math.trunc(value)));
}

export function createPiece(kind: PieceKind, color: PieceColor, position: Position): Piece {
  return {
    id: `${color}-${kind}-${positionKey(position)}`,
    kind,
    color,
    position,
    hasMoved: false,
  };
}

export function positionKey(position: Position): string {
  return position.join(",");
}

export function positionsEqual(left: Position, right: Position): boolean {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

export function nextTurn(color: PieceColor): PieceColor {
  return color === "white" ? "black" : "white";
}

export function pieceAt(board: BoardState, position: Position): Piece | undefined {
  return board.pieces.find((piece) => positionsEqual(piece.position, position));
}

export function evaluateBoard(board: BoardState): number {
  return board.pieces.reduce((score, piece) => {
    const signedValue = piece.color === "white" ? PIECE_VALUES[piece.kind] : -PIECE_VALUES[piece.kind];
    return score + signedValue;
  }, 0);
}

export const MATE_SCORE = 1_000_000;
export const MATE_THRESHOLD = MATE_SCORE - 1_000;

export type EvaluationView = {
  /** Human-readable label for the eval bar — `+1.5`, `-0.4`, `M2`, `-M2`, `1–0`, `0–1`. */
  label: string;
  /** True when a forced mate is on the board. */
  isMate: boolean;
  /** Signed mate distance from white's perspective: `+N` white mates, `-N` white gets mated, `0` already final. */
  mateIn: number | null;
  /** White's territory on a 0-100 vertical fill. Mate pegs to 0 or 100. */
  fillPercent: number;
};

/**
 * Pure score-to-label conversion. The label is *analytical*: an `M{N}` is only
 * emitted when an engine search returned a mate-distance score (or the API
 * passed a non-null `mateIn`). No heuristic fallback ever claims a mate.
 *
 * `whiteScore` is signed in white's favour: positive means white better.
 */
export function describeEvaluation(
  whiteScore: number,
  mateIn: number | null = null,
): EvaluationView {
  if (mateIn !== null) {
    if (mateIn === 0) {
      const winnerScore = whiteScore !== 0 ? whiteScore : 1;
      return {
        label: winnerScore > 0 ? "1–0" : "0–1",
        isMate: true,
        mateIn: 0,
        fillPercent: winnerScore > 0 ? 100 : 0,
      };
    }
    return {
      label: mateIn > 0 ? `M${Math.abs(mateIn)}` : `-M${Math.abs(mateIn)}`,
      isMate: true,
      mateIn,
      fillPercent: mateIn > 0 ? 100 : 0,
    };
  }

  if (Math.abs(whiteScore) >= MATE_THRESHOLD) {
    const plies = MATE_SCORE - Math.abs(whiteScore);
    if (plies <= 0) {
      return {
        label: whiteScore > 0 ? "1–0" : "0–1",
        isMate: true,
        mateIn: 0,
        fillPercent: whiteScore > 0 ? 100 : 0,
      };
    }
    const movesToMate = Math.ceil(plies / 2);
    const sign = whiteScore > 0 ? 1 : -1;
    return {
      label: sign > 0 ? `M${movesToMate}` : `-M${movesToMate}`,
      isMate: true,
      mateIn: sign * movesToMate,
      fillPercent: sign > 0 ? 100 : 0,
    };
  }

  const fill = Math.max(4, Math.min(96, 50 + whiteScore * 4));
  const signed = `${whiteScore >= 0 ? "+" : ""}${whiteScore.toFixed(1)}`;
  return { label: signed, isMate: false, mateIn: null, fillPercent: fill };
}
