"use client";

import { useMemo, useState } from "react";

import {
  applyMove,
  createInitialBoard,
  legalMovesForPiece,
  Move,
  nextTurn,
  pieceAt,
  PIECE_SYMBOLS,
  positionKey,
  positionsEqual,
  type BoardState,
  type Piece,
  type Position,
} from "@/lib/chess";

type Slice = {
  k: number;
  h: number;
};

export function NChessBoard() {
  const [board, setBoard] = useState<BoardState>(() => createInitialBoard());
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null);
  const [history, setHistory] = useState<string[]>([]);
  const [botEnabled, setBotEnabled] = useState(true);
  const [botThinking, setBotThinking] = useState(false);
  const [botError, setBotError] = useState<string | null>(null);

  const selectedPiece = selectedPosition ? pieceAt(board, selectedPosition) : undefined;
  const canHumanMove = !botThinking && (!botEnabled || board.turn === "white");
  const selectedMoves = useMemo(() => {
    if (!canHumanMove || !selectedPiece || selectedPiece.color !== board.turn) {
      return [];
    }
    return legalMovesForPiece(board, selectedPiece);
  }, [board, canHumanMove, selectedPiece]);

  function resetGame() {
    setBoard(createInitialBoard());
    setSelectedPosition(null);
    setHistory([]);
    setBotError(null);
    setBotThinking(false);
  }

  async function handleCellClick(position: Position) {
    if (!canHumanMove) {
      return;
    }

    const clickedPiece = pieceAt(board, position);
    const matchingMove = selectedMoves.find((move) => positionsEqual(move.to, position));

    if (matchingMove) {
      const movingPiece = pieceAt(board, matchingMove.from);
      const capturedPiece = pieceAt(board, matchingMove.to);
      const nextBoard = applyMove(board, matchingMove);
      setBoard(nextBoard);
      setSelectedPosition(null);
      setHistory((moves) => [
        describeMove(movingPiece, capturedPiece, matchingMove),
        ...moves,
      ].slice(0, 12));
      await requestBotMove(nextBoard);
      return;
    }

    if (clickedPiece?.color === board.turn) {
      setSelectedPosition(position);
      return;
    }

    setSelectedPosition(null);
  }

  async function requestBotMove(currentBoard: BoardState) {
    if (!botEnabled || currentBoard.turn !== "black") {
      return;
    }

    setBotThinking(true);
    setBotError(null);
    try {
      const response = await fetch("/api/bot", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          board: currentBoard,
          color: "black",
          depth: 1,
        }),
      });

      const payload = await response.json() as {
        move?: Move | null;
        error?: string;
        detail?: string;
      };
      if (!response.ok) {
        throw new Error(payload.detail ?? payload.error ?? "Bot request failed");
      }
      if (!payload.move) {
        setHistory((moves) => ["black bot has no legal move", ...moves].slice(0, 12));
        return;
      }

      const botMove = payload.move;
      const movingPiece = pieceAt(currentBoard, botMove.from);
      const capturedPiece = pieceAt(currentBoard, botMove.to);
      const nextBoard = applyMove(currentBoard, botMove);
      setBoard(nextBoard);
      setHistory((moves) => [
        `${describeMove(movingPiece, capturedPiece, botMove)} (bot)`,
        ...moves,
      ].slice(0, 12));
    } catch (error) {
      setBotError(error instanceof Error ? error.message : "Bot request failed");
    } finally {
      setBotThinking(false);
    }
  }

  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">n-dimensional chess</p>
        <h1>Play the 4D prototype in the browser.</h1>
        <p>
          This Next.js version replaces the Kivy-only GUI with a model-driven React board.
          Select a piece, inspect legal destinations across the 4D slices, and move pieces
          without a desktop runtime.
        </p>
      </section>

      <section className="game-layout" aria-label="nChess game">
        <div className="board-stack">
          <div className="slice-grid">
            {slicesForBoard(board).map((slice) => (
              <BoardSlice
                key={`${slice.k}-${slice.h}`}
                board={board}
                slice={slice}
                selectedMoves={selectedMoves}
                selectedPosition={selectedPosition}
                onCellClick={handleCellClick}
              />
            ))}
          </div>
        </div>

        <aside className="side-panel">
          <h2>Game state</h2>
          <div className="status">
            <span>Turn</span>
            <div className="turn">{botThinking ? "Bot thinking..." : board.turn}</div>
          </div>
          {botError ? <p className="bot-error">{botError}</p> : null}

          <div className="actions">
            <button className="primary-button" type="button" onClick={resetGame}>
              Reset
            </button>
            <button
              className="secondary-button"
              type="button"
              aria-pressed={botEnabled}
              onClick={() => setBotEnabled((enabled) => !enabled)}
            >
              Bot {botEnabled ? "on" : "off"}
            </button>
            <button
              className="secondary-button"
              type="button"
              disabled={botThinking || board.turn !== "black"}
              onClick={() => {
                void requestBotMove(board);
              }}
            >
              Bot move
            </button>
            <button
              className="secondary-button"
              type="button"
              disabled={botThinking}
              onClick={() => setBoard((currentBoard) => ({ ...currentBoard, turn: nextTurn(currentBoard.turn) }))}
            >
              Pass turn
            </button>
          </div>

          <h3>Recent moves</h3>
          {history.length === 0 ? (
            <p>No moves yet.</p>
          ) : (
            <ol className="move-list">
              {history.map((entry, index) => (
                <li key={`${entry}-${index}`}>{entry}</li>
              ))}
            </ol>
          )}
        </aside>
      </section>
    </main>
  );
}

function BoardSlice({
  board,
  slice,
  selectedMoves,
  selectedPosition,
  onCellClick,
}: {
  board: BoardState;
  slice: Slice;
  selectedMoves: Move[];
  selectedPosition: Position | null;
  onCellClick: (position: Position) => void | Promise<void>;
}) {
  const cells = [];

  for (let y = board.size[1] - 1; y >= 0; y -= 1) {
    for (let x = 0; x < board.size[0]; x += 1) {
      const position = [x, y, slice.k, slice.h];
      cells.push(
        <BoardCell
          key={positionKey(position)}
          board={board}
          position={position}
          selectedMoves={selectedMoves}
          selectedPosition={selectedPosition}
          onClick={onCellClick}
        />,
      );
    }
  }

  return (
    <article className="slice" aria-label={`Slice z ${slice.k}, w ${slice.h}`}>
      <div className="slice-label">
        <span>z={slice.k}</span>
        <span>w={slice.h}</span>
      </div>
      <div className="cells">{cells}</div>
    </article>
  );
}

function BoardCell({
  board,
  position,
  selectedMoves,
  selectedPosition,
  onClick,
}: {
  board: BoardState;
  position: Position;
  selectedMoves: Move[];
  selectedPosition: Position | null;
  onClick: (position: Position) => void | Promise<void>;
}) {
  const piece = pieceAt(board, position);
  const isSelected = Boolean(selectedPosition && positionsEqual(selectedPosition, position));
  const legalMove = selectedMoves.find((move) => positionsEqual(move.to, position));
  const isCapture = Boolean(legalMove && piece && piece.color !== board.turn);
  const shade = (position[0] + position[1]) % 2 === 0 ? "dark" : "light";

  return (
    <button
      aria-label={cellLabel(position, piece)}
      className={[
        "cell",
        shade,
        isSelected ? "selected" : "",
        legalMove ? "legal" : "",
        isCapture ? "capture" : "",
      ].filter(Boolean).join(" ")}
      type="button"
      onClick={() => {
        void onClick(position);
      }}
    >
      {piece ? (
        <span className={`piece ${piece.color}`}>{PIECE_SYMBOLS[piece.color][piece.kind]}</span>
      ) : null}
    </button>
  );
}

function slicesForBoard(board: BoardState): Slice[] {
  const slices: Slice[] = [];
  for (let k = board.size[2] - 1; k >= 0; k -= 1) {
    for (let h = 0; h < board.size[3]; h += 1) {
      slices.push({ k, h });
    }
  }
  return slices;
}

function describeMove(piece: Piece | undefined, capturedPiece: Piece | undefined, move: Move): string {
  const actor = piece ? `${piece.color} ${piece.kind}` : "piece";
  const capture = capturedPiece ? ` captures ${capturedPiece.color} ${capturedPiece.kind}` : "";
  return `${actor}${capture}: ${positionKey(move.from)} → ${positionKey(move.to)}`;
}

function cellLabel(position: Position, piece: Piece | undefined): string {
  const base = `Cell ${positionKey(position)}`;
  return piece ? `${base}, ${piece.color} ${piece.kind}` : base;
}
