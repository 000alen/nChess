"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

import { OnlineChessBoard } from "@/components/online-chess-board";
import { useOnlineRoom } from "@/hooks/use-online-room";
import type { PieceColor } from "@/lib/chess";

export function PlayRoomClient({ roomId }: { roomId: string }) {
  const searchParams = useSearchParams();
  const preferredSeat = useMemo(() => {
    const join = searchParams.get("join");
    return join === "white" || join === "black" ? join : undefined;
  }, [searchParams]);

  const online = useOnlineRoom(roomId);
  const [joining, setJoining] = useState(false);

  async function handleJoin(seat?: PieceColor) {
    setJoining(true);
    try {
      await online.join(seat ?? preferredSeat);
    } finally {
      setJoining(false);
    }
  }

  if (online.status === "loading") {
    return (
      <main className="play-page">
        <p>Loading room…</p>
      </main>
    );
  }

  if (online.status === "error" || !online.room) {
    return (
      <main className="play-page">
        <p className="bot-error">{online.error ?? "Room not found"}</p>
        <Link className="play-back-link" href="/play/new">
          Create a new game
        </Link>
      </main>
    );
  }

  if (!online.myColor || !online.token) {
    const openSeat =
      !online.room.players.white ? "white" : !online.room.players.black ? "black" : null;
    return (
      <main className="play-page">
        <header className="play-page-header">
          <h1>Join game {roomId}</h1>
          <p>
            {online.room.status === "waiting"
              ? "Pick a seat to join this game."
              : "This room has no open seats for your session."}
          </p>
        </header>
        {openSeat ? (
          <button
            className="primary-button"
            type="button"
            disabled={joining}
            onClick={() => void handleJoin(openSeat)}
          >
            {joining ? "Joining…" : `Join as ${openSeat}`}
          </button>
        ) : (
          <p className="bot-error">Both seats are taken. Ask the host for a new invite.</p>
        )}
        <Link className="play-back-link" href="/">
          ← Local play
        </Link>
      </main>
    );
  }

  if (online.room.status === "waiting") {
    return (
      <main className="play-page">
        <header className="play-page-header">
          <h1>Waiting for opponent</h1>
          <p>
            Share this link:
            <code className="play-invite-code">
              {typeof window !== "undefined" ? window.location.href.split("?")[0] : `/play/${roomId}`}
            </code>
          </p>
        </header>
        <p>Seat: {online.myColor}. Game starts when the other player joins.</p>
        <Link className="play-back-link" href="/">
          ← Local play
        </Link>
      </main>
    );
  }

  return (
    <>
      <div className="play-room-toolbar">
        <Link className="play-back-link" href="/">
          ← Local play
        </Link>
        <span className="play-room-id">Room {roomId}</span>
      </div>
      <OnlineChessBoard
        room={online.room}
        myColor={online.myColor}
        movePending={online.movePending}
        error={online.error}
        onMove={online.submitMove}
        onResign={online.resign}
      />
    </>
  );
}
