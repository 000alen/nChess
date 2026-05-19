import type { OnlineRoom } from "@/lib/game-room";

export type SeatColor = "white" | "black";

export type TokenBinding = {
  roomId: string;
  color: SeatColor;
};

export interface RoomStore {
  getRoom(roomId: string): Promise<OnlineRoom | null>;
  setRoom(room: OnlineRoom, ttlSeconds: number): Promise<void>;
  deleteRoom(roomId: string): Promise<void>;
  getTokenBinding(token: string): Promise<TokenBinding | null>;
  setTokenBinding(token: string, binding: TokenBinding, ttlSeconds: number): Promise<void>;
  deleteToken(token: string): Promise<void>;
}

type MemoryEntry = {
  value: string;
  expiresAt: number;
};

const memoryRooms = new Map<string, MemoryEntry>();
const memoryTokens = new Map<string, MemoryEntry>();

function memoryGet(map: Map<string, MemoryEntry>, key: string): string | null {
  const entry = map.get(key);
  if (!entry) {
    return null;
  }
  if (Date.now() > entry.expiresAt) {
    map.delete(key);
    return null;
  }
  return entry.value;
}

function memorySet(map: Map<string, MemoryEntry>, key: string, value: string, ttlSeconds: number): void {
  map.set(key, { value, expiresAt: Date.now() + ttlSeconds * 1000 });
}

class MemoryRoomStore implements RoomStore {
  async getRoom(roomId: string): Promise<OnlineRoom | null> {
    const raw = memoryGet(memoryRooms, `room:${roomId}`);
    return raw ? JSON.parse(raw) as OnlineRoom : null;
  }

  async setRoom(room: OnlineRoom, ttlSeconds: number): Promise<void> {
    memorySet(memoryRooms, `room:${room.id}`, JSON.stringify(room), ttlSeconds);
  }

  async deleteRoom(roomId: string): Promise<void> {
    memoryRooms.delete(`room:${roomId}`);
  }

  async getTokenBinding(token: string): Promise<TokenBinding | null> {
    const raw = memoryGet(memoryTokens, `token:${token}`);
    return raw ? JSON.parse(raw) as TokenBinding : null;
  }

  async setTokenBinding(token: string, binding: TokenBinding, ttlSeconds: number): Promise<void> {
    memorySet(memoryTokens, `token:${token}`, JSON.stringify(binding), ttlSeconds);
  }

  async deleteToken(token: string): Promise<void> {
    memoryTokens.delete(`token:${token}`);
  }
}

class UpstashRoomStore implements RoomStore {
  private readonly url: string;
  private readonly token: string;

  constructor(url: string, token: string) {
    this.url = url;
    this.token = token;
  }

  private async command<T>(parts: (string | number)[]): Promise<T> {
    const response = await fetch(this.url, {
      method: "POST",
      headers: { Authorization: `Bearer ${this.token}` },
      body: JSON.stringify(parts),
    });
    if (!response.ok) {
      throw new Error(`Upstash command failed: ${response.status}`);
    }
    const payload = await response.json() as { result: T };
    return payload.result;
  }

  async getRoom(roomId: string): Promise<OnlineRoom | null> {
    const raw = await this.command<string | null>(["GET", `room:${roomId}`]);
    return raw ? JSON.parse(raw) as OnlineRoom : null;
  }

  async setRoom(room: OnlineRoom, ttlSeconds: number): Promise<void> {
    await this.command(["SET", `room:${room.id}`, JSON.stringify(room), "EX", ttlSeconds]);
  }

  async deleteRoom(roomId: string): Promise<void> {
    await this.command(["DEL", `room:${roomId}`]);
  }

  async getTokenBinding(token: string): Promise<TokenBinding | null> {
    const raw = await this.command<string | null>(["GET", `token:${token}`]);
    return raw ? JSON.parse(raw) as TokenBinding : null;
  }

  async setTokenBinding(token: string, binding: TokenBinding, ttlSeconds: number): Promise<void> {
    await this.command(["SET", `token:${token}`, JSON.stringify(binding), "EX", ttlSeconds]);
  }

  async deleteToken(token: string): Promise<void> {
    await this.command(["DEL", `token:${token}`]);
  }
}

let storeSingleton: RoomStore | null = null;

export function getRoomStore(): RoomStore {
  if (storeSingleton) {
    return storeSingleton;
  }

  const url = process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN;
  if (url && token) {
    storeSingleton = new UpstashRoomStore(url, token);
    return storeSingleton;
  }

  storeSingleton = new MemoryRoomStore();
  return storeSingleton;
}

export function getRoomTtlSeconds(): number {
  const raw = Number(process.env.ROOM_TTL_SECONDS ?? 604800);
  return Number.isFinite(raw) && raw > 60 ? raw : 604800;
}
