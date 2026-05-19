import { createInitialBoard, normalizeBoardConfig, pieceAt, type BoardState, type Move, type PieceColor } from "@/lib/chess";
import { getAppOrigin } from "@/lib/app-origin";
import type { GameStatus, PromotionKind } from "@/lib/game-mode";
import {
  RoomError,
  type CreateRoomRequest,
  type CreateRoomResponse,
  type JoinRoomRequest,
  type JoinRoomResponse,
  type OnlineRoom,
  type PublicRoom,
  type RoomMoveEntry,
  type RoomPlayer,
  type SubmitMoveRequest,
  type SubmitMoveResponse,
} from "@/lib/game-room";
import { getRoomStore, getRoomTtlSeconds, type SeatColor, type TokenBinding } from "@/lib/room-store";

const MAX_MOVES = 500;

function nowIso(): string {
  return new Date().toISOString();
}

function generateId(length = 10): string {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789";
  const bytes = crypto.getRandomValues(new Uint8Array(length));
  return Array.from(bytes, (byte) => alphabet[byte % alphabet.length]).join("");
}

function generateToken(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  return Buffer.from(bytes).toString("base64url");
}

function generatePlayerId(): string {
  return crypto.randomUUID();
}

function publicRoom(room: OnlineRoom): PublicRoom {
  return room;
}

function isExpired(room: OnlineRoom): boolean {
  return Date.now() > new Date(room.expiresAt).getTime();
}

async function loadRoom(roomId: string): Promise<OnlineRoom> {
  const room = await getRoomStore().getRoom(roomId);
  if (!room) {
    throw new RoomError("ROOM_NOT_FOUND", "Room does not exist or has expired", 404);
  }
  if (isExpired(room)) {
    throw new RoomError("ROOM_EXPIRED", "Room has expired", 410);
  }
  return room;
}

async function saveRoom(room: OnlineRoom): Promise<void> {
  room.updatedAt = nowIso();
  const ttl = Math.max(60, Math.floor((new Date(room.expiresAt).getTime() - Date.now()) / 1000));
  await getRoomStore().setRoom(room, ttl);
}

async function issueToken(roomId: string, color: SeatColor): Promise<string> {
  const token = generateToken();
  const ttl = getRoomTtlSeconds();
  await getRoomStore().setTokenBinding(token, { roomId, color }, ttl);
  return token;
}

export async function resolveToken(token: string | null): Promise<{ room: OnlineRoom; color: PieceColor }> {
  if (!token) {
    throw new RoomError("UNAUTHORIZED", "Missing room token", 401);
  }
  const binding = await getRoomStore().getTokenBinding(token);
  if (!binding) {
    throw new RoomError("UNAUTHORIZED", "Invalid or expired token", 401);
  }
  const room = await loadRoom(binding.roomId);
  return { room, color: binding.color };
}

function touchPlayer(room: OnlineRoom, color: PieceColor): void {
  const player = room.players[color];
  if (player) {
    player.lastSeenAt = nowIso();
  }
}

function activateIfReady(room: OnlineRoom): void {
  if (room.status === "waiting" && room.players.white && room.players.black) {
    room.status = "active";
  }
}

function openSeat(room: OnlineRoom, preferred?: PieceColor): PieceColor | null {
  if (preferred) {
    return room.players[preferred] ? null : preferred;
  }
  if (!room.players.white) {
    return "white";
  }
  if (!room.players.black) {
    return "black";
  }
  return null;
}

export async function createRoom(request: CreateRoomRequest, origin: string): Promise<CreateRoomResponse> {
  const boardConfig = normalizeBoardConfig(request.boardConfig);
  const seat = request.seat ?? "white";
  if (seat !== "white" && seat !== "black") {
    throw new RoomError("INVALID_REQUEST", "seat must be white or black", 400);
  }

  const playerId = request.playerId ?? generatePlayerId();
  const createdAt = nowIso();
  const ttl = getRoomTtlSeconds();
  const expiresAt = new Date(Date.now() + ttl * 1000).toISOString();
  const board = createInitialBoard(boardConfig);
  const roomId = generateId(10);

  const player: RoomPlayer = {
    playerId,
    joinedAt: createdAt,
    lastSeenAt: createdAt,
  };

  const room: OnlineRoom = {
    id: roomId,
    status: "waiting",
    version: 0,
    boardConfig,
    board,
    moves: [],
    winner: null,
    endReason: null,
    createdAt,
    updatedAt: createdAt,
    expiresAt,
    players: {
      white: seat === "white" ? player : null,
      black: seat === "black" ? player : null,
    },
    flags: { hintsAllowed: false },
  };

  await saveRoom(room);
  const token = await issueToken(roomId, seat);

  const invitePath = `/play/${roomId}`;
  const joinPath = `/play/${roomId}?join=${seat === "white" ? "black" : "white"}`;

  return {
    room: publicRoom(room),
    myColor: seat,
    token,
    playerId,
    inviteUrl: `${origin}${invitePath}`,
    joinUrl: `${origin}${joinPath}`,
  };
}

export async function joinRoom(
  roomId: string,
  request: JoinRoomRequest,
): Promise<JoinRoomResponse> {
  const room = await loadRoom(roomId);
  if (room.status === "finished") {
    throw new RoomError("GAME_NOT_ACTIVE", "Game has already finished", 400);
  }

  const seat = openSeat(room, request.seat);
  if (!seat) {
    throw new RoomError("SEAT_TAKEN", "No open seat available", 409);
  }

  const joinedAt = nowIso();
  const player: RoomPlayer = {
    playerId: request.playerId ?? generatePlayerId(),
    joinedAt,
    lastSeenAt: joinedAt,
  };
  room.players[seat] = player;
  activateIfReady(room);
  await saveRoom(room);

  const token = await issueToken(roomId, seat);
  return {
    room: publicRoom(room),
    myColor: seat,
    token,
    playerId: player.playerId,
  };
}

export async function getRoomSnapshot(
  roomId: string,
  token: string | null,
  sinceVersion?: number,
): Promise<{ room: PublicRoom; yourColor: PieceColor | null; unchanged?: boolean }> {
  const room = await loadRoom(roomId);
  let yourColor: PieceColor | null = null;

  if (token) {
    const binding = await getRoomStore().getTokenBinding(token);
    if (binding?.roomId === roomId) {
      yourColor = binding.color;
      touchPlayer(room, binding.color);
      await saveRoom(room);
    }
  }

  if (typeof sinceVersion === "number" && sinceVersion === room.version) {
    return { room: publicRoom(room), yourColor, unchanged: true };
  }

  return { room: publicRoom(room), yourColor };
}

type MoveApiResponse = {
  board?: BoardState;
  move?: Move;
  elapsedMs?: number;
  positionHash?: string;
  error?: { code?: string; message?: string } | string;
  detail?: string;
};

async function validateMoveOnEngine(
  board: BoardState,
  move: Move,
  promotion?: PromotionKind,
): Promise<{ board: BoardState; move: Move; elapsedMs?: number }> {
  const origin = getAppOrigin();
  const response = await fetch(`${origin}/api/move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ board, move, promotion }),
  });
  const payload = await response.json() as MoveApiResponse;
  if (!response.ok || !payload.board || !payload.move) {
    const message =
      typeof payload.error === "object" && payload.error?.message
        ? payload.error.message
        : typeof payload.error === "string"
          ? payload.error
          : payload.detail ?? "Move validation failed";
    throw new RoomError("ILLEGAL_MOVE", message, 422);
  }
  return { board: payload.board, move: payload.move, elapsedMs: payload.elapsedMs };
}

type EvaluateApiResponse = {
  status?: GameStatus;
};

async function fetchGameStatus(board: BoardState): Promise<GameStatus | null> {
  const origin = getAppOrigin();
  const response = await fetch(`${origin}/api/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      board,
      color: "white",
      searchDepth: 0,
      searchTimeMs: 0,
    }),
  });
  if (!response.ok) {
    return null;
  }
  const payload = await response.json() as EvaluateApiResponse;
  return payload.status ?? null;
}

function resolveGameEnd(
  status: GameStatus | null,
  sideToMove: PieceColor,
): { finished: boolean; winner: PieceColor | "draw" | null; endReason: OnlineRoom["endReason"] } {
  if (!status) {
    return { finished: false, winner: null, endReason: null };
  }
  const side = status[sideToMove];
  if (side.inCheckmate) {
    return {
      finished: true,
      winner: sideToMove === "white" ? "black" : "white",
      endReason: "checkmate",
    };
  }
  if (side.inStalemate) {
    return { finished: true, winner: "draw", endReason: "stalemate" };
  }
  return { finished: false, winner: null, endReason: null };
}

export async function submitRoomMove(
  roomId: string,
  token: string | null,
  body: SubmitMoveRequest,
): Promise<SubmitMoveResponse> {
  const { room, color: myColor } = await resolveToken(token);
  if (room.id !== roomId) {
    throw new RoomError("UNAUTHORIZED", "Token does not match room", 401);
  }
  if (room.status !== "active") {
    throw new RoomError("GAME_NOT_ACTIVE", "Game is not active", 400);
  }
  if (room.board.turn !== myColor) {
    throw new RoomError("NOT_YOUR_TURN", "It is not your turn", 403);
  }
  if (room.moves.length >= MAX_MOVES) {
    throw new RoomError("GAME_NOT_ACTIVE", "Move limit reached", 400);
  }

  const expectedHash = room.board.hash;
  if (body.positionHash && expectedHash && body.positionHash !== expectedHash) {
    throw new RoomError("STALE_POSITION", "Board changed; refresh and try again", 409);
  }

  const promotion =
    pieceAt(room.board, body.move.from)?.kind === "pawn" ? body.promotion ?? "queen" : undefined;

  const applied = await validateMoveOnEngine(room.board, body.move, promotion);
  const positionHashBefore = expectedHash ?? body.positionHash ?? "";
  const ply = room.moves.length + 1;
  const entry: RoomMoveEntry = {
    ply,
    side: myColor,
    move: applied.move,
    promotion,
    positionHashBefore,
    boardAfter: applied.board,
    timeMs: applied.elapsedMs,
    appliedAt: nowIso(),
  };

  room.board = applied.board;
  room.moves.push(entry);
  room.version += 1;
  touchPlayer(room, myColor);

  const status = await fetchGameStatus(room.board);
  const end = resolveGameEnd(status, room.board.turn);
  if (end.finished) {
    room.status = "finished";
    room.winner = end.winner;
    room.endReason = end.endReason;
  }

  await saveRoom(room);
  return {
    room: publicRoom(room),
    move: applied.move,
    elapsedMs: applied.elapsedMs,
  };
}

export async function resignRoom(roomId: string, token: string | null): Promise<PublicRoom> {
  const { room, color: myColor } = await resolveToken(token);
  if (room.id !== roomId) {
    throw new RoomError("UNAUTHORIZED", "Token does not match room", 401);
  }
  if (room.status === "finished") {
    return publicRoom(room);
  }
  room.status = "finished";
  room.winner = myColor === "white" ? "black" : "white";
  room.endReason = "resign";
  room.version += 1;
  touchPlayer(room, myColor);
  await saveRoom(room);
  return publicRoom(room);
}

export function parseBearerToken(header: string | null): string | null {
  if (!header) {
    return null;
  }
  const match = /^Bearer\s+(.+)$/i.exec(header);
  return match?.[1] ?? null;
}
