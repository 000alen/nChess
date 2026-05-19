import type { PieceColor } from "@/lib/chess";

export type StoredOnlineSession = {
  roomId: string;
  myColor: PieceColor;
  token: string;
  playerId: string;
};

function storageKey(roomId: string): string {
  return `nchess-room-${roomId}`;
}

export function loadOnlineSession(roomId: string): StoredOnlineSession | null {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = window.sessionStorage.getItem(storageKey(roomId));
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as StoredOnlineSession;
    if (parsed.roomId !== roomId || !parsed.token || !parsed.myColor) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function saveOnlineSession(session: StoredOnlineSession): void {
  if (typeof window === "undefined") {
    return;
  }
  window.sessionStorage.setItem(storageKey(session.roomId), JSON.stringify(session));
}

export function clearOnlineSession(roomId: string): void {
  if (typeof window === "undefined") {
    return;
  }
  window.sessionStorage.removeItem(storageKey(roomId));
}
