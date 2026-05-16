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
  to: Position;
};

export type BoardState = {
  dimension: number;
  size: Position;
  pieces: Piece[];
  turn: PieceColor;
};

export const TURN_ORDER: readonly PieceColor[] = ["white", "black"];

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

export function inBounds(board: BoardState, position: Position): boolean {
  return (
    position.length === board.dimension
    && position.every((coordinate, axis) => coordinate >= 0 && coordinate < board.size[axis])
  );
}

export function legalMovesForPiece(board: BoardState, piece: Piece): Move[] {
  return pseudoMovesForPiece(board, piece).filter((move) => {
    const target = pieceAt(board, move.to);
    if (target?.kind === "king") {
      return false;
    }
    return !isInCheck(applyMove(board, move, { advanceTurn: false }), piece.color);
  });
}

export function legalMovesForColor(board: BoardState, color: PieceColor): Move[] {
  return board.pieces
    .filter((piece) => piece.color === color)
    .flatMap((piece) => legalMovesForPiece(board, piece));
}

export function evaluateBoard(board: BoardState): number {
  return board.pieces.reduce((score, piece) => {
    const signedValue = piece.color === "white" ? PIECE_VALUES[piece.kind] : -PIECE_VALUES[piece.kind];
    return score + signedValue;
  }, 0);
}

export function applyMove(
  board: BoardState,
  move: Move,
  options: { advanceTurn?: boolean } = {},
): BoardState {
  const movingPiece = pieceAt(board, move.from);
  if (!movingPiece) {
    throw new Error(`No piece at ${positionKey(move.from)}`);
  }

  const nextPieces = board.pieces
    .filter((piece) => !positionsEqual(piece.position, move.to))
    .map((piece) => {
      if (!positionsEqual(piece.position, move.from)) {
        return piece;
      }

      const movedPiece: Piece = {
        ...piece,
        kind: promotesOnMove(board, piece, move.to) ? "queen" : piece.kind,
        position: move.to,
        hasMoved: true,
      };
      return movedPiece;
    });

  return {
    ...board,
    pieces: nextPieces,
    turn: options.advanceTurn === false ? board.turn : nextTurn(board.turn),
  };
}

export function isInCheck(board: BoardState, color: PieceColor): boolean {
  const king = board.pieces.find((piece) => piece.kind === "king" && piece.color === color);
  if (!king) {
    return true;
  }

  return board.pieces
    .filter((piece) => piece.color !== color)
    .some((piece) => pseudoMovesForPiece(board, piece).some((move) => positionsEqual(move.to, king.position)));
}

export function pseudoMovesForPiece(board: BoardState, piece: Piece): Move[] {
  switch (piece.kind) {
    case "king":
      return slidingMoves(board, piece, [...cardinals(board.dimension), ...diagonals(board.dimension)], 1);
    case "queen":
      return slidingMoves(
        board,
        piece,
        [...cardinals(board.dimension), ...diagonals(board.dimension)],
        Math.max(...board.size) - 1,
      );
    case "rook":
      return slidingMoves(board, piece, cardinals(board.dimension), Math.max(...board.size) - 1);
    case "bishop":
      return slidingMoves(board, piece, diagonals(board.dimension), Math.max(...board.size) - 1);
    case "knight":
      return knightMoves(board, piece);
    case "pawn":
      return pawnMoves(board, piece);
    default: {
      const exhaustive: never = piece.kind;
      return exhaustive;
    }
  }
}

function slidingMoves(
  board: BoardState,
  piece: Piece,
  offsets: Position[],
  maxMagnitude: number,
): Move[] {
  const moves: Move[] = [];
  for (const offset of offsets) {
    for (let magnitude = 1; magnitude <= maxMagnitude; magnitude += 1) {
      const to = piece.position.map((coordinate, axis) => coordinate + offset[axis] * magnitude);
      if (!inBounds(board, to)) {
        break;
      }

      const target = pieceAt(board, to);
      if (target?.color === piece.color) {
        break;
      }

      moves.push({ from: piece.position, to });
      if (target) {
        break;
      }
    }
  }
  return moves;
}

function knightMoves(board: BoardState, piece: Piece): Move[] {
  return lOffsets(board.dimension)
    .map((offset) => ({
      from: piece.position,
      to: piece.position.map((coordinate, axis) => coordinate + offset[axis]),
    }))
    .filter((move) => {
      const target = pieceAt(board, move.to);
      return inBounds(board, move.to) && target?.color !== piece.color;
    });
}

function pawnMoves(board: BoardState, piece: Piece): Move[] {
  const captureAxis = 0;
  const direction = piece.color === "white" ? 1 : -1;
  const moves: Move[] = [];

  for (let axis = 0; axis < board.dimension; axis += 1) {
    if (axis === captureAxis) {
      continue;
    }

    const oneStep = piece.position.map((coordinate, index) => (
      index === axis ? coordinate + direction : coordinate
    ));
    if (inBounds(board, oneStep) && !pieceAt(board, oneStep)) {
      moves.push({ from: piece.position, to: oneStep });

      const twoStep = piece.position.map((coordinate, index) => (
        index === axis ? coordinate + direction * 2 : coordinate
      ));
      if (!piece.hasMoved && inBounds(board, twoStep) && !pieceAt(board, twoStep)) {
        moves.push({ from: piece.position, to: twoStep });
      }
    }
  }

  for (const fileDirection of [-1, 1]) {
    for (let axis = 0; axis < board.dimension; axis += 1) {
      if (axis === captureAxis) {
        continue;
      }

      const to = piece.position.map((coordinate, index) => {
        if (index === captureAxis) {
          return coordinate + fileDirection;
        }
        return index === axis ? coordinate + direction : coordinate;
      });
      const target = pieceAt(board, to);
      if (inBounds(board, to) && target && target.color !== piece.color) {
        moves.push({ from: piece.position, to });
      }
    }
  }

  return moves;
}

function promotesOnMove(board: BoardState, piece: Piece, to: Position): boolean {
  if (piece.kind !== "pawn") {
    return false;
  }

  const direction = piece.color === "white" ? 1 : -1;
  return to.slice(1).every((coordinate, index) => {
    const axis = index + 1;
    return coordinate === (direction === 1 ? board.size[axis] - 1 : 0);
  });
}

function cardinals(dimension: number): Position[] {
  const offsets: Position[] = [];
  for (const direction of [-1, 1]) {
    for (let axis = 0; axis < dimension; axis += 1) {
      offsets.push(Array.from({ length: dimension }, (_, index) => (index === axis ? direction : 0)));
    }
  }
  return offsets;
}

function diagonals(dimension: number): Position[] {
  const offsets: Position[] = [];
  for (let count = 2; count <= dimension; count += 1) {
    for (const axes of combinations([...Array(dimension).keys()], count)) {
      for (const signs of signPermutations(count)) {
        offsets.push(Array.from({ length: dimension }, (_, axis) => {
          const selectedIndex = axes.indexOf(axis);
          return selectedIndex === -1 ? 0 : signs[selectedIndex];
        }));
      }
    }
  }
  return offsets;
}

function lOffsets(dimension: number): Position[] {
  const offsets: Position[] = [];
  for (let longAxis = 0; longAxis < dimension; longAxis += 1) {
    for (let shortAxis = 0; shortAxis < dimension; shortAxis += 1) {
      if (longAxis === shortAxis) {
        continue;
      }
      for (const longDirection of [-1, 1]) {
        for (const shortDirection of [-1, 1]) {
          offsets.push(Array.from({ length: dimension }, (_, axis) => {
            if (axis === longAxis) {
              return 2 * longDirection;
            }
            return axis === shortAxis ? shortDirection : 0;
          }));
        }
      }
    }
  }
  return offsets;
}

function combinations<T>(items: readonly T[], count: number): T[][] {
  if (count === 0) {
    return [[]];
  }
  if (items.length < count) {
    return [];
  }

  const [head, ...tail] = items;
  return [
    ...combinations(tail, count - 1).map((combination) => [head, ...combination]),
    ...combinations(tail, count),
  ];
}

function signPermutations(length: number): number[][] {
  if (length === 0) {
    return [[]];
  }
  return signPermutations(length - 1).flatMap((rest) => [
    [-1, ...rest],
    [1, ...rest],
  ]);
}
