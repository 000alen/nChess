import type {
  CreateRoomRequest,
  CreateRoomResponse,
  GetRoomResponse,
  JoinRoomRequest,
  JoinRoomResponse,
  RoomApiError,
  SubmitMoveRequest,
  SubmitMoveResponse,
} from "@/lib/game-room";

function authHeaders(token?: string | null): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

async function parseRoomResponse<T>(response: Response): Promise<T> {
  const payload = await response.json() as T | RoomApiError;
  if (!response.ok) {
    const errorPayload = payload as RoomApiError;
    throw new Error(errorPayload.error?.message ?? "Room request failed");
  }
  return payload as T;
}

export async function apiCreateRoom(body: CreateRoomRequest): Promise<CreateRoomResponse> {
  const response = await fetch("/api/rooms", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body),
  });
  return parseRoomResponse<CreateRoomResponse>(response);
}

export async function apiJoinRoom(roomId: string, body: JoinRoomRequest): Promise<JoinRoomResponse> {
  const response = await fetch(`/api/rooms/${roomId}/join`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body),
  });
  return parseRoomResponse<JoinRoomResponse>(response);
}

export async function apiGetRoom(
  roomId: string,
  options?: { token?: string | null; sinceVersion?: number },
): Promise<GetRoomResponse> {
  const params = new URLSearchParams();
  if (typeof options?.sinceVersion === "number") {
    params.set("sinceVersion", String(options.sinceVersion));
  }
  const query = params.toString();
  const response = await fetch(`/api/rooms/${roomId}${query ? `?${query}` : ""}`, {
    headers: authHeaders(options?.token),
  });
  return parseRoomResponse<GetRoomResponse>(response);
}

export async function apiSubmitMove(
  roomId: string,
  token: string,
  body: SubmitMoveRequest,
): Promise<SubmitMoveResponse> {
  const response = await fetch(`/api/rooms/${roomId}/move`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(body),
  });
  return parseRoomResponse<SubmitMoveResponse>(response);
}

export async function apiResignRoom(roomId: string, token: string): Promise<{ room: GetRoomResponse["room"] }> {
  const response = await fetch(`/api/rooms/${roomId}/resign`, {
    method: "POST",
    headers: authHeaders(token),
  });
  return parseRoomResponse<{ room: GetRoomResponse["room"] }>(response);
}
