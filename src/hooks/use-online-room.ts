"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { BoardConfig, PieceColor } from "@/lib/chess";
import type { OnlineRoom, RoomStatus } from "@/lib/game-room";
import type { PromotionKind } from "@/lib/game-mode";
import { apiGetRoom, apiJoinRoom, apiResignRoom, apiSubmitMove } from "@/lib/room-api";
import { loadOnlineSession, saveOnlineSession, type StoredOnlineSession } from "@/lib/online-session";
import type { Move } from "@/lib/chess";

const POLL_MS_ACTIVE = 1500;
const POLL_MS_HIDDEN = 5000;

export type OnlineRoomState = {
  room: OnlineRoom | null;
  myColor: PieceColor | null;
  token: string | null;
  playerId: string | null;
  status: RoomStatus | "loading" | "error";
  error: string | null;
  movePending: boolean;
  isPolling: boolean;
};

export function useOnlineRoom(roomId: string) {
  const [state, setState] = useState<OnlineRoomState>({
    room: null,
    myColor: null,
    token: null,
    playerId: null,
    status: "loading",
    error: null,
    movePending: false,
    isPolling: false,
  });
  const versionRef = useRef(0);
  const tokenRef = useRef<string | null>(null);
  tokenRef.current = state.token;

  const applySession = useCallback((session: StoredOnlineSession, room: OnlineRoom) => {
    saveOnlineSession(session);
    versionRef.current = room.version;
    setState((current) => ({
      ...current,
      room,
      myColor: session.myColor,
      token: session.token,
      playerId: session.playerId,
      status: room.status,
      error: null,
    }));
  }, []);

  const refresh = useCallback(async (token?: string | null) => {
    const activeToken = token ?? tokenRef.current;
    const snapshot = await apiGetRoom(roomId, {
      token: activeToken,
      sinceVersion: versionRef.current,
    });
    if (snapshot.unchanged) {
      return snapshot.room;
    }
    versionRef.current = snapshot.room.version;
    setState((current) => ({
      ...current,
      room: snapshot.room,
      status: snapshot.room.status,
    }));
    return snapshot.room;
  }, [roomId]);

  const join = useCallback(async (seat?: PieceColor) => {
    const playerId = crypto.randomUUID();
    const response = await apiJoinRoom(roomId, { seat, playerId });
    const session: StoredOnlineSession = {
      roomId,
      myColor: response.myColor,
      token: response.token,
      playerId: response.playerId,
    };
    applySession(session, response.room);
    return response;
  }, [applySession, roomId]);

  const connect = useCallback(async () => {
    setState((current) => ({ ...current, status: "loading", error: null }));
    try {
      const saved = loadOnlineSession(roomId);
      if (saved) {
        const snapshot = await apiGetRoom(roomId, { token: saved.token });
        applySession(saved, snapshot.room);
        return;
      }
      const snapshot = await apiGetRoom(roomId);
      setState((current) => ({
        ...current,
        room: snapshot.room,
        status: snapshot.room.status,
        error: null,
      }));
      versionRef.current = snapshot.room.version;
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        error: error instanceof Error ? error.message : "Failed to load room",
      }));
    }
  }, [applySession, roomId]);

  useEffect(() => {
    void connect();
  }, [connect]);

  useEffect(() => {
    if (!state.token || state.status === "error" || state.status === "loading") {
      return;
    }
    if (state.room?.status === "finished") {
      return;
    }

    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;

    async function poll() {
      if (cancelled) {
        return;
      }
      setState((current) => ({ ...current, isPolling: true }));
      try {
        await refresh(tokenRef.current);
      } catch (error) {
        if (!cancelled) {
          setState((current) => ({
            ...current,
            error: error instanceof Error ? error.message : "Polling failed",
          }));
        }
      } finally {
        if (!cancelled) {
          setState((current) => ({ ...current, isPolling: false }));
          const delay = document.hidden ? POLL_MS_HIDDEN : POLL_MS_ACTIVE;
          timer = setTimeout(() => {
            void poll();
          }, delay);
        }
      }
    }

    void poll();

    return () => {
      cancelled = true;
      if (timer) {
        clearTimeout(timer);
      }
    };
  }, [refresh, state.room?.status, state.status, state.token, state.room?.version]);

  const submitMove = useCallback(async (move: Move, promotion?: PromotionKind) => {
    if (!state.token || !state.room) {
      throw new Error("Not connected to room");
    }
    setState((current) => ({ ...current, movePending: true, error: null }));
    try {
      const response = await apiSubmitMove(state.room.id, state.token, {
        move,
        promotion,
        positionHash: state.room.board.hash ?? "",
      });
      versionRef.current = response.room.version;
      setState((current) => ({
        ...current,
        room: response.room,
        status: response.room.status,
        movePending: false,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        movePending: false,
        error: error instanceof Error ? error.message : "Move failed",
      }));
      throw error;
    }
  }, [state.room, state.token]);

  const resign = useCallback(async () => {
    if (!state.token) {
      return;
    }
    const response = await apiResignRoom(roomId, state.token);
    versionRef.current = response.room.version;
    setState((current) => ({
      ...current,
      room: response.room,
      status: response.room.status,
    }));
  }, [roomId, state.token]);

  return {
    ...state,
    join,
    refresh,
    submitMove,
    resign,
  };
}
