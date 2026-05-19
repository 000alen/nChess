import type { PieceColor, PieceKind } from "@/lib/chess";

export type PlayerKind = "human" | "engine";

export type PromotionKind = Exclude<PieceKind, "king" | "pawn">;

export type SeatConfig = {
  kind: PlayerKind;
  promotion: PromotionKind;
};

export type GameSeats = Record<PieceColor, SeatConfig>;

export type GameMode = "human-bot" | "bot-bot" | "human-human" | "analysis";

export const GAME_MODE_STORAGE_KEY = "nchess-game-mode";
export const ENGINE_COLOR_STORAGE_KEY = "nchess-engine-color";

export const DEFAULT_ENGINE_DEPTH = 2;
export const DEFAULT_ENGINE_TIME_MS = 750;

export function defaultSeat(kind: PlayerKind, promotion: PromotionKind = "queen"): SeatConfig {
  return { kind, promotion };
}

export function seatsForMode(mode: GameMode, engineColor: PieceColor = "black"): GameSeats {
  switch (mode) {
    case "human-bot":
      return {
        white: defaultSeat(engineColor === "white" ? "engine" : "human"),
        black: defaultSeat(engineColor === "black" ? "engine" : "human"),
      };
    case "bot-bot":
      return {
        white: defaultSeat("engine"),
        black: defaultSeat("engine"),
      };
    case "human-human":
    case "analysis":
      return {
        white: defaultSeat("human"),
        black: defaultSeat("human"),
      };
  }
}

export function engineColorForMode(mode: GameMode, seats: GameSeats): PieceColor {
  if (seats.white.kind === "engine" && seats.black.kind === "human") {
    return "white";
  }
  if (seats.black.kind === "engine" && seats.white.kind === "human") {
    return "black";
  }
  return "black";
}

export function gameModeLabel(mode: GameMode): string {
  switch (mode) {
    case "human-bot":
      return "Human vs bot";
    case "bot-bot":
      return "Bot vs bot";
    case "human-human":
      return "Human vs human";
    case "analysis":
      return "Analysis";
  }
}

export function gameModeOptions(): Array<{ value: GameMode; label: string }> {
  return [
    { value: "human-bot", label: "Human vs bot" },
    { value: "bot-bot", label: "Bot vs bot" },
    { value: "human-human", label: "Human vs human" },
    { value: "analysis", label: "Analysis" },
  ];
}

export type SideStatus = {
  inCheck: boolean;
  inCheckmate: boolean;
  inStalemate: boolean;
};

export type GameStatus = Record<PieceColor, SideStatus>;

export function isTerminalForSide(status: GameStatus | null, color: PieceColor): boolean {
  if (!status) {
    return false;
  }
  const side = status[color];
  return side.inCheckmate || side.inStalemate;
}

export function isAutoPlayMode(mode: GameMode): boolean {
  return mode === "bot-bot";
}

export function allowsPassTurn(mode: GameMode): boolean {
  return mode === "analysis" || mode === "human-human";
}

export function allowsHint(mode: GameMode): boolean {
  return mode !== "bot-bot";
}

export function allowsManualEngineMove(seats: GameSeats, turn: PieceColor): boolean {
  return seats[turn].kind === "engine";
}

export function humanPromotionChoice(seats: GameSeats, color: PieceColor): PromotionKind {
  return seats[color].promotion;
}
