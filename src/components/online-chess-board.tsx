"use client";

import { useMemo } from "react";

import { NChessBoard } from "@/components/nchess-board";
import type { Move, PieceColor } from "@/lib/chess";
import type { OnlineRoom } from "@/lib/game-room";
import type { PromotionKind } from "@/lib/game-mode";

export type OnlineChessBoardProps = {
  room: OnlineRoom;
  myColor: PieceColor;
  movePending: boolean;
  error: string | null;
  onMove: (move: Move, promotion?: PromotionKind) => Promise<void>;
  onResign: () => Promise<void>;
};

export function OnlineChessBoard({
  room,
  myColor,
  movePending,
  error,
  onMove,
  onResign,
}: OnlineChessBoardProps) {
  const banner = useMemo(() => {
    if (room.status === "waiting") {
      return "Waiting for opponent to join…";
    }
    if (room.status === "finished") {
      if (room.endReason === "resign") {
        return room.winner === myColor ? "Opponent resigned — you win" : "You resigned";
      }
      if (room.winner === "draw") {
        return "Draw";
      }
      if (room.winner === myColor) {
        return "You win";
      }
      if (room.winner) {
        return "You lose";
      }
      return "Game over";
    }
    if (movePending) {
      return "Sending move…";
    }
    if (room.board.turn === myColor) {
      return "Your turn";
    }
    return "Opponent's turn";
  }, [movePending, myColor, room]);

  return (
    <div className="online-shell">
      <div className="online-banner" data-turn={room.board.turn === myColor ? "yours" : "opponent"}>
        <span>{banner}</span>
        {room.status === "active" ? (
          <button className="secondary-button compact" type="button" onClick={() => void onResign()}>
            Resign
          </button>
        ) : null}
      </div>
      {error ? <p className="bot-error online-error">{error}</p> : null}
      <NChessBoard
        connection="online"
        initialBoardConfig={room.boardConfig}
        online={{
          room,
          myColor,
          movePending,
          onMove,
        }}
      />
    </div>
  );
}
