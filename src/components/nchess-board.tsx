"use client";

import type { CSSProperties } from "react";
import { useEffect, useMemo, useState } from "react";

import {
  applyMove,
  createInitialBoard,
  DEFAULT_BOARD_CONFIG,
  evaluateBoard,
  legalMovesForPiece,
  Move,
  nextTurn,
  normalizeBoardConfig,
  pieceAt,
  PIECE_SYMBOLS,
  positionKey,
  positionsEqual,
  type BoardConfig,
  type BoardDimension,
  type BoardState,
  type Piece,
  type Position,
} from "@/lib/chess";

type Slice = {
  coordinates: Position;
  label: string;
};

type MoveActor = "human" | "bot";

type MoveRecord = {
  id: string;
  actor: MoveActor;
  board: BoardState;
  label: string;
  move: Move;
  ply: number;
};

type EngineEvaluation = {
  loading: boolean;
  score: number | null;
};

type Theme = "dark" | "light";
const THEME_STORAGE_KEY = "nchess-theme";

function getInitialTheme(): Theme {
  if (typeof window === "undefined") {
    return "dark";
  }

  const savedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
  if (savedTheme === "dark" || savedTheme === "light") {
    return savedTheme;
  }

  return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

export function NChessBoard() {
  const [boardConfig, setBoardConfig] = useState<BoardConfig>(DEFAULT_BOARD_CONFIG);
  const [draftConfig, setDraftConfig] = useState<BoardConfig>(DEFAULT_BOARD_CONFIG);
  const [board, setBoard] = useState<BoardState>(() => createInitialBoard(DEFAULT_BOARD_CONFIG));
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null);
  const [moveHistory, setMoveHistory] = useState<MoveRecord[]>([]);
  const [currentPly, setCurrentPly] = useState(0);
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  const [botEnabled, setBotEnabled] = useState(true);
  const [botThinking, setBotThinking] = useState(false);
  const [botError, setBotError] = useState<string | null>(null);
  const [engineEvaluation, setEngineEvaluation] = useState<EngineEvaluation>({
    loading: true,
    score: null,
  });

  const fallbackEvaluation = useMemo(() => evaluateBoard(board), [board]);
  const evaluation = engineEvaluation.score ?? fallbackEvaluation;
  const selectedPiece = selectedPosition ? pieceAt(board, selectedPosition) : undefined;
  const canHumanMove = !botThinking && (!botEnabled || board.turn === "white");
  const selectedMoves = useMemo(() => {
    if (!canHumanMove || !selectedPiece || selectedPiece.color !== board.turn) {
      return [];
    }
    return legalMovesForPiece(board, selectedPiece);
  }, [board, canHumanMove, selectedPiece]);

  useEffect(() => {
    const controller = new AbortController();
    setEngineEvaluation((current) => ({ ...current, loading: true }));

    async function loadEvaluation() {
      try {
        const response = await fetch("/api/evaluate", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            board,
            color: "white",
          }),
          signal: controller.signal,
        });
        const payload = await response.json() as {
          whiteScore?: number;
        };

        if (!response.ok || typeof payload.whiteScore !== "number") {
          throw new Error("Evaluation request failed");
        }
        setEngineEvaluation({ loading: false, score: payload.whiteScore });
      } catch (error) {
        if (!controller.signal.aborted) {
          setEngineEvaluation({ loading: false, score: null });
        }
      }
    }

    void loadEvaluation();

    return () => controller.abort();
  }, [board]);

  useEffect(() => {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  function resetGame() {
    startNewGame(boardConfig);
  }

  function startNewGame(config: BoardConfig) {
    const nextConfig = normalizeBoardConfig(config);
    setBoardConfig(nextConfig);
    setDraftConfig(nextConfig);
    setBoard(createInitialBoard(nextConfig));
    setSelectedPosition(null);
    setMoveHistory([]);
    setCurrentPly(0);
    setBotError(null);
    setBotThinking(false);
  }

  function commitMove(currentBoard: BoardState, move: Move, actor: MoveActor, basePly: number): BoardState {
    const movingPiece = pieceAt(currentBoard, move.from);
    const capturedPiece = pieceAt(currentBoard, move.to);
    const nextBoard = applyMove(currentBoard, move);
    const record: MoveRecord = {
      actor,
      board: nextBoard,
      id: `${basePly + 1}-${positionKey(move.from)}-${positionKey(move.to)}`,
      label: describeMove(movingPiece, capturedPiece, move),
      move,
      ply: basePly + 1,
    };

    setBoard(nextBoard);
    setMoveHistory((records) => [...records.slice(0, basePly), record]);
    setCurrentPly(record.ply);
    return nextBoard;
  }

  function jumpToPly(ply: number) {
    if (botThinking) {
      return;
    }

    const boundedPly = Math.max(0, Math.min(ply, moveHistory.length));
    const targetBoard = boundedPly === 0 ? createInitialBoard(boardConfig) : moveHistory[boundedPly - 1].board;
    setBoard(targetBoard);
    setCurrentPly(boundedPly);
    setSelectedPosition(null);
    setBotError(null);
  }

  async function handleCellClick(position: Position) {
    if (!canHumanMove) {
      return;
    }

    const clickedPiece = pieceAt(board, position);
    const matchingMove = selectedMoves.find((move) => positionsEqual(move.to, position));

    if (matchingMove) {
      const nextBoard = commitMove(board, matchingMove, "human", currentPly);
      setSelectedPosition(null);
      await requestBotMove(nextBoard, currentPly + 1);
      return;
    }

    if (clickedPiece?.color === board.turn) {
      setSelectedPosition(position);
      return;
    }

    setSelectedPosition(null);
  }

  async function requestBotMove(currentBoard: BoardState, basePly = currentPly) {
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
        setBotError("Bot has no legal move.");
        return;
      }

      const botMove = payload.move;
      commitMove(currentBoard, botMove, "bot", basePly);
    } catch (error) {
      setBotError(error instanceof Error ? error.message : "Bot request failed");
    } finally {
      setBotThinking(false);
    }
  }

  return (
    <main className="page-shell" data-theme={theme}>
      <header className="top-bar">
        <div>
          <p className="brand-kicker">nChess</p>
          <strong>{board.dimension}D Chess Arena</strong>
        </div>
        <button
          className="theme-toggle"
          type="button"
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          onClick={() => setTheme((currentTheme) => (currentTheme === "dark" ? "light" : "dark"))}
        >
          {theme === "dark" ? "Light mode" : "Dark mode"}
        </button>
      </header>

      <section className="game-layout" aria-label="nChess game">
        <div className="board-stack">
          <div className="slice-grid" style={{ "--slice-columns": sliceColumnCount(board) } as CSSProperties}>
            {slicesForBoard(board).map((slice) => (
              <BoardSlice
                key={slice.coordinates.join(",") || "2d"}
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
          <div className="panel-title">
            <h2>Game state</h2>
            <span>{botEnabled ? "Vs bot" : "Analysis"}</span>
          </div>
          <div className="status">
            <span>Turn</span>
            <div className="turn">{botThinking ? "Bot thinking..." : board.turn}</div>
          </div>
          <EvaluationBar
            loading={engineEvaluation.loading}
            score={evaluation}
            source={engineEvaluation.score === null ? "local" : "engine"}
          />
          {botError ? <p className="bot-error">{botError}</p> : null}
          <BoardSetup
            config={draftConfig}
            currentConfig={boardConfig}
            onApply={startNewGame}
            onChange={setDraftConfig}
          />

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
                void requestBotMove(board, currentPly);
              }}
            >
              Bot move
            </button>
            <button
              className="secondary-button"
              type="button"
              disabled={botThinking}
              onClick={() => {
                setBoard((currentBoard) => ({ ...currentBoard, turn: nextTurn(currentBoard.turn) }));
              }}
            >
              Pass turn
            </button>
          </div>

          <HistoryPanel
            currentPly={currentPly}
            disabled={botThinking}
            moveHistory={moveHistory}
            onJump={jumpToPly}
          />
        </aside>
      </section>
    </main>
  );
}

function BoardSetup({
  config,
  currentConfig,
  onApply,
  onChange,
}: {
  config: BoardConfig;
  currentConfig: BoardConfig;
  onApply: (config: BoardConfig) => void;
  onChange: (config: BoardConfig) => void;
}) {
  const normalizedConfig = normalizeBoardConfig(config);
  const isCurrentConfig = (
    normalizedConfig.dimension === currentConfig.dimension
    && normalizedConfig.size.length === currentConfig.size.length
    && normalizedConfig.size.every((value, index) => value === currentConfig.size[index])
  );

  function updateDimension(dimension: BoardDimension) {
    const nextSize = Array.from({ length: dimension }, (_, axis) => config.size[axis] ?? 4);
    onChange(normalizeBoardConfig({ dimension, size: nextSize }));
  }

  function updateAxisSize(axis: number, value: number) {
    const nextSize = config.size.map((size, index) => (index === axis ? value : size));
    onChange(normalizeBoardConfig({ dimension: config.dimension, size: nextSize }));
  }

  return (
    <section className="setup-card" aria-label="Board setup">
      <div className="setup-heading">
        <h3>Board setup</h3>
        <span>{currentConfig.dimension}D active</span>
      </div>
      <label className="field">
        <span>Dimensions</span>
        <select
          value={config.dimension}
          onChange={(event) => updateDimension(Number(event.target.value) as BoardDimension)}
        >
          <option value={2}>2D</option>
          <option value={3}>3D</option>
          <option value={4}>4D</option>
        </select>
      </label>
      <div className="axis-grid">
        {config.size.map((axisSize, axis) => (
          <label className="field" key={`axis-${axis}`}>
            <span>{axisLabel(axis)}</span>
            <input
              type="number"
              min={4}
              max={12}
              value={axisSize}
              onChange={(event) => updateAxisSize(axis, Number(event.target.value))}
            />
          </label>
        ))}
      </div>
      <button
        className="primary-button"
        disabled={isCurrentConfig}
        type="button"
        onClick={() => onApply(normalizedConfig)}
      >
        New {normalizedConfig.dimension}D game
      </button>
      <p className="setup-note">Generated starts require at least 4 cells per axis.</p>
    </section>
  );
}

function EvaluationBar({
  loading,
  score,
  source,
}: {
  loading: boolean;
  score: number;
  source: "engine" | "local";
}) {
  const whitePercent = clamp(50 + score * 4, 4, 96);
  const label = `${score >= 0 ? "+" : ""}${score.toFixed(1)}`;

  return (
    <section className="evaluation-card" aria-label={`Evaluation ${label}`}>
      <div className="evaluation-heading">
        <span>Evaluation</span>
        <strong>{loading ? `${label} …` : label}</strong>
      </div>
      <p className="evaluation-source">
        {source === "engine" ? "Python engine score" : "Local material fallback"}
      </p>
      <div className="evaluation-bar" aria-hidden="true">
        <div className="evaluation-white" style={{ height: `${whitePercent}%` }} />
        <div className="evaluation-marker" style={{ bottom: `${whitePercent}%` }} />
      </div>
      <div className="evaluation-labels">
        <span>Black better</span>
        <span>White better</span>
      </div>
    </section>
  );
}

function HistoryPanel({
  currentPly,
  disabled,
  moveHistory,
  onJump,
}: {
  currentPly: number;
  disabled: boolean;
  moveHistory: MoveRecord[];
  onJump: (ply: number) => void;
}) {
  return (
    <section className="history-panel">
      <div className="history-heading">
        <h3>Move history</h3>
        <span>
          Ply {currentPly}/{moveHistory.length}
        </span>
      </div>
      <div className="rewind-controls" aria-label="Replay controls">
        <button className="secondary-button compact" type="button" disabled={disabled || currentPly === 0} onClick={() => onJump(0)}>
          Start
        </button>
        <button className="secondary-button compact" type="button" disabled={disabled || currentPly === 0} onClick={() => onJump(currentPly - 1)}>
          Prev
        </button>
        <button
          className="secondary-button compact"
          type="button"
          disabled={disabled || currentPly >= moveHistory.length}
          onClick={() => onJump(currentPly + 1)}
        >
          Next
        </button>
        <button
          className="secondary-button compact"
          type="button"
          disabled={disabled || currentPly >= moveHistory.length}
          onClick={() => onJump(moveHistory.length)}
        >
          Latest
        </button>
      </div>

      {moveHistory.length === 0 ? (
        <p>No moves yet.</p>
      ) : (
        <ol className="move-list">
          {moveHistory.map((record) => (
            <li key={record.id}>
              <button
                className={record.ply === currentPly ? "move-entry active" : "move-entry"}
                disabled={disabled}
                type="button"
                onClick={() => onJump(record.ply)}
              >
                <span className="move-ply">{record.ply}.</span>
                <span>{record.label}</span>
                <span className="move-actor">{record.actor}</span>
              </button>
            </li>
          ))}
        </ol>
      )}
    </section>
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
  const columns = board.size[0];
  const rows = board.size[1];

  for (let y = rows - 1; y >= 0; y -= 1) {
    for (let x = 0; x < columns; x += 1) {
      const position = [x, y, ...slice.coordinates];
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

  const gridStyle = {
    "--board-columns": columns,
    "--board-rows": rows,
  } as CSSProperties;

  return (
    <article className="slice" aria-label={slice.label}>
      <div className="slice-label">
        <span>{slice.label}</span>
      </div>
      <div className="cells" style={gridStyle}>{cells}</div>
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
  if (board.dimension === 2) {
    return [{ coordinates: [], label: "Board" }];
  }

  if (board.dimension === 3) {
    return Array.from({ length: board.size[2] }, (_, index) => {
      const z = board.size[2] - index - 1;
      return {
        coordinates: [z],
        label: `z=${z}`,
      };
    });
  }

  const slices: Slice[] = [];
  for (let k = board.size[2] - 1; k >= 0; k -= 1) {
    for (let h = 0; h < board.size[3]; h += 1) {
      slices.push({
        coordinates: [k, h],
        label: `z=${k} w=${h}`,
      });
    }
  }
  return slices;
}

function sliceColumnCount(board: BoardState): number {
  if (board.dimension === 2) {
    return 1;
  }
  if (board.dimension === 3) {
    return Math.min(board.size[2], 4);
  }
  return Math.min(board.size[3], 4);
}

function axisLabel(axis: number): string {
  return ["x", "y", "z", "w"][axis] ?? `axis ${axis + 1}`;
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

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}
