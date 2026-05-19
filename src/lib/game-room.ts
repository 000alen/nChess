import type { BoardConfig, BoardState, Move, PieceColor } from "@/lib/chess";
import type { PromotionKind } from "@/lib/game-mode";

export type RoomStatus = "waiting" | "active" | "finished";

export type RoomEndReason = "checkmate" | "stalemate" | "resign" | null;

export type RoomPlayer = {
  playerId: string;
  joinedAt: string;
  lastSeenAt: string;
};

export type RoomMoveEntry = {
  ply: number;
  side: PieceColor;
  move: Move;
  promotion?: PromotionKind;
  positionHashBefore: string;
  boardAfter: BoardState;
  timeMs?: number;
  appliedAt: string;
};

export type OnlineRoom = {
  id: string;
  status: RoomStatus;
  version: number;
  boardConfig: BoardConfig;
  board: BoardState;
  moves: RoomMoveEntry[];
  winner: PieceColor | "draw" | null;
  endReason: RoomEndReason;
  createdAt: string;
  updatedAt: string;
  expiresAt: string;
  players: {
    white: RoomPlayer | null;
    black: RoomPlayer | null;
  };
  flags: {
    hintsAllowed: false;
  };
};

export type PublicRoom = Omit<OnlineRoom, never>;

export type RoomErrorCode =
  | "ROOM_NOT_FOUND"
  | "ROOM_EXPIRED"
  | "SEAT_TAKEN"
  | "SEAT_UNAVAILABLE"
  | "NOT_YOUR_TURN"
  | "STALE_POSITION"
  | "ILLEGAL_MOVE"
  | "GAME_NOT_ACTIVE"
  | "UNAUTHORIZED"
  | "INVALID_REQUEST"
  | "MOVE_FAILED";

export class RoomError extends Error {
  readonly code: RoomErrorCode;
  readonly status: number;

  constructor(code: RoomErrorCode, message: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

export type CreateRoomRequest = {
  boardConfig: BoardConfig;
  seat?: PieceColor;
  playerId?: string;
};

export type CreateRoomResponse = {
  room: PublicRoom;
  myColor: PieceColor;
  token: string;
  playerId: string;
  inviteUrl: string;
  joinUrl: string;
};

export type JoinRoomRequest = {
  seat?: PieceColor;
  playerId?: string;
};

export type JoinRoomResponse = {
  room: PublicRoom;
  myColor: PieceColor;
  token: string;
  playerId: string;
};

export type GetRoomResponse = {
  room: PublicRoom;
  yourColor: PieceColor | null;
  unchanged?: boolean;
};

export type SubmitMoveRequest = {
  move: Move;
  promotion?: PromotionKind;
  positionHash: string;
};

export type SubmitMoveResponse = {
  room: PublicRoom;
  move: Move;
  elapsedMs?: number;
};

export type RoomApiError = {
  error: {
    code: RoomErrorCode;
    message: string;
  };
};
