"use client";

import type { CSSProperties } from "react";
import { useEffect, useMemo, useState } from "react";

import {
  createInitialBoard,
  DEFAULT_BOARD_CONFIG,
  evaluateBoard,
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
  capturedPiece?: Piece;
  evaluation: number;
  evaluationSource: "engine" | "local";
  label: string;
  move: Move;
  ply: number;
};

type EngineEvaluation = {
  loading: boolean;
  score: number | null;
  status: EngineStatus | null;
};

type EngineStatus = Record<"white" | "black", {
  inCheck: boolean;
  inCheckmate: boolean;
  inStalemate: boolean;
}>;

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
  const [hintMove, setHintMove] = useState<Move | null>(null);
  const [hintThinking, setHintThinking] = useState(false);
  const [hintError, setHintError] = useState<string | null>(null);
  const [legalMoves, setLegalMoves] = useState<Move[]>([]);
  const [legalMovesLoading, setLegalMovesLoading] = useState(false);
  const [moveError, setMoveError] = useState<string | null>(null);
  const [engineEvaluation, setEngineEvaluation] = useState<EngineEvaluation>({
    loading: true,
    score: null,
    status: null,
  });

  const fallbackEvaluation = useMemo(() => evaluateBoard(board), [board]);
  const evaluation = engineEvaluation.score ?? fallbackEvaluation;
  const currentStatus = engineEvaluation.status?.[board.turn] ?? null;
  const isViewingPast = currentPly < moveHistory.length;
  const capturedPieces = useMemo(() => moveHistory.flatMap((record) => (
    record.capturedPiece ? [record.capturedPiece] : []
  )), [moveHistory]);
  const canHumanMove = !botThinking && (!botEnabled || board.turn === "white");
  const selectedMoves = legalMovesLoading ? [] : legalMoves;

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
          status?: EngineStatus;
          whiteScore?: number;
        };

        if (!response.ok || typeof payload.whiteScore !== "number") {
          throw new Error("Evaluation request failed");
        }
        const whiteScore = payload.whiteScore;
        setEngineEvaluation({ loading: false, score: whiteScore, status: payload.status ?? null });
        setMoveHistory((records) => records.map((record) => (
          sameBoard(record.board, board)
            ? { ...record, evaluation: whiteScore, evaluationSource: "engine" }
            : record
        )));
      } catch (error) {
        if (!controller.signal.aborted) {
          setEngineEvaluation({ loading: false, score: null, status: null });
        }
      }
    }

    void loadEvaluation();

    return () => controller.abort();
  }, [board]);

  useEffect(() => {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadLegalMoves() {
      if (!selectedPosition || !canHumanMove) {
        setLegalMoves([]);
        return;
      }

      setLegalMovesLoading(true);
      try {
        const response = await fetch("/api/legal-moves", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            board,
            position: selectedPosition,
          }),
          signal: controller.signal,
        });
        const payload = await response.json() as {
          moves?: Move[];
        };
        if (!response.ok || !Array.isArray(payload.moves)) {
          throw new Error("Legal moves request failed");
        }
        setLegalMoves(payload.moves);
      } catch (error) {
        if (!controller.signal.aborted) {
          setLegalMoves([]);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLegalMovesLoading(false);
        }
      }
    }

    void loadLegalMoves();
    return () => controller.abort();
  }, [board, canHumanMove, selectedPosition]);

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
    clearHint();
    setMoveError(null);
    setLegalMoves([]);
  }

  function commitMove(currentBoard: BoardState, move: Move, nextBoard: BoardState, actor: MoveActor, basePly: number): BoardState {
    const movingPiece = pieceAt(currentBoard, move.from);
    const capturedPiece = pieceAt(currentBoard, move.to);
    const record: MoveRecord = {
      actor,
      board: nextBoard,
      capturedPiece,
      evaluation: evaluateBoard(nextBoard),
      evaluationSource: "local",
      id: `${basePly + 1}-${positionKey(move.from)}-${positionKey(move.to)}`,
      label: describeMove(movingPiece, capturedPiece, move),
      move,
      ply: basePly + 1,
    };

    setBoard(nextBoard);
    setMoveHistory((records) => [...records.slice(0, basePly), record]);
    setCurrentPly(record.ply);
    setMoveError(null);
    setLegalMoves([]);
    clearHint();
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
    setMoveError(null);
    setLegalMoves([]);
    clearHint();
  }

  async function handleCellClick(position: Position) {
    if (!canHumanMove) {
      return;
    }

    const clickedPiece = pieceAt(board, position);
    const matchingMove = selectedMoves.find((move) => positionsEqual(move.to, position));

    if (matchingMove) {
      await requestHumanMove(matchingMove);
      return;
    }

    if (clickedPiece?.color === board.turn) {
      setSelectedPosition(position);
      return;
    }

    setSelectedPosition(null);
    setLegalMoves([]);
    clearHint();
  }

  async function requestHumanMove(move: Move) {
    setMoveError(null);
    try {
      const response = await fetch("/api/move", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          board,
          move,
        }),
      });
      const payload = await response.json() as {
        board?: BoardState;
        move?: Move;
        error?: string;
        detail?: string;
      };
      if (!response.ok || !payload.board || !payload.move) {
        throw new Error(payload.detail ?? payload.error ?? "Move request failed");
      }
      const nextBoard = commitMove(board, payload.move, payload.board, "human", currentPly);
      setSelectedPosition(null);
      await requestBotMove(nextBoard, currentPly + 1);
    } catch (error) {
      setMoveError(error instanceof Error ? error.message : "Move request failed");
    }
  }

  function clearHint() {
    setHintMove(null);
    setHintError(null);
    setHintThinking(false);
  }

  async function requestHint() {
    setHintThinking(true);
    setHintError(null);
    try {
      const response = await fetch("/api/bot", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          board,
          color: board.turn,
          depth: 1,
        }),
      });
      const payload = await response.json() as {
        board?: BoardState;
        move?: Move | null;
        error?: string;
        detail?: string;
      };

      if (!response.ok) {
        throw new Error(payload.detail ?? payload.error ?? "Hint request failed");
      }
      if (!payload.move) {
        setHintMove(null);
        setHintError("No legal hint available.");
        return;
      }
      setHintMove(payload.move);
    } catch (error) {
      setHintError(error instanceof Error ? error.message : "Hint request failed");
    } finally {
      setHintThinking(false);
    }
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
        board?: BoardState;
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
      if (payload.board) {
        commitMove(currentBoard, botMove, payload.board, "bot", basePly);
      } else {
        const response = await fetch("/api/move", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            board: currentBoard,
            move: botMove,
          }),
        });
        const movePayload = await response.json() as { board?: BoardState };
        if (!response.ok || !movePayload.board) {
          throw new Error("Bot move application failed");
        }
        commitMove(currentBoard, botMove, movePayload.board, "bot", basePly);
      }
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
                hintMove={hintMove}
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
            {currentStatus ? <StatusLine status={currentStatus} /> : null}
            {isViewingPast ? <p className="rewind-state">Viewing past position</p> : null}
          </div>
          <EvaluationBar
            loading={engineEvaluation.loading}
            score={evaluation}
            source={engineEvaluation.score === null ? "local" : "engine"}
          />
          {botError ? <p className="bot-error">{botError}</p> : null}
          {moveError ? <p className="bot-error">{moveError}</p> : null}
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
              disabled={hintThinking || botThinking}
              onClick={() => {
                void requestHint();
              }}
            >
              {hintThinking ? "Hint..." : "Hint"}
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
          {hintError ? <p className="hint-error">{hintError}</p> : null}
          {hintMove ? (
            <p className="hint-line">
              Hint: {positionKey(hintMove.from)} → {positionKey(hintMove.to)}
            </p>
          ) : null}

          <HistoryPanel
            capturedPieces={capturedPieces}
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
  capturedPieces,
  currentPly,
  disabled,
  moveHistory,
  onJump,
}: {
  capturedPieces: Piece[];
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
                <span className="move-meta">
                  <span className="move-eval">{formatScore(record.evaluation)}</span>
                  <span className="move-actor">{record.actor}</span>
                </span>
              </button>
            </li>
          ))}
        </ol>
      )}
      <CapturedPieces pieces={capturedPieces} />
    </section>
  );
}

function CapturedPieces({ pieces }: { pieces: Piece[] }) {
  return (
    <section className="captured-panel" aria-label="Captured pieces">
      <div className="history-heading">
        <h3>Captured</h3>
        <span>{pieces.length}</span>
      </div>
      {pieces.length === 0 ? (
        <p>No captures yet.</p>
      ) : (
        <div className="captured-list">
          {pieces.map((piece, index) => (
            <span className={`captured-piece ${piece.color}`} key={`${piece.id}-${index}`}>
              {PIECE_SYMBOLS[piece.color][piece.kind]}
            </span>
          ))}
        </div>
      )}
    </section>
  );
}

function StatusLine({ status }: { status: EngineStatus["white"] }) {
  if (status.inCheckmate) {
    return <p className="status-line danger">Checkmate</p>;
  }
  if (status.inStalemate) {
    return <p className="status-line">Stalemate</p>;
  }
  if (status.inCheck) {
    return <p className="status-line danger">Check</p>;
  }
  return <p className="status-line">Safe</p>;
}

function BoardSlice({
  board,
  hintMove,
  slice,
  selectedMoves,
  selectedPosition,
  onCellClick,
}: {
  board: BoardState;
  hintMove: Move | null;
  slice: Slice;
  selectedMoves: Move[];
  selectedPosition: Position | null;
  onCellClick: (position: Position) => void | Promise<void>;
}) {
  const cells = [];
  const columns = board.size[0];
  const rows = board.size[1];
  const hintArrow = hintMove ? arrowForSlice(hintMove, slice, columns, rows) : null;

  for (let y = rows - 1; y >= 0; y -= 1) {
    for (let x = 0; x < columns; x += 1) {
      const position = [x, y, ...slice.coordinates];
      cells.push(
        <BoardCell
          key={positionKey(position)}
          board={board}
          hintMove={hintMove}
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
      <div className="cells" style={gridStyle}>
        {cells}
        {hintArrow ? <HintArrow arrow={hintArrow} /> : null}
      </div>
    </article>
  );
}

function HintArrow({
  arrow,
}: {
  arrow: {
    from: { x: number; y: number };
    to: { x: number; y: number };
  };
}) {
  const markerId = `hint-arrow-${Math.round(arrow.from.x)}-${Math.round(arrow.from.y)}-${Math.round(arrow.to.x)}-${Math.round(arrow.to.y)}`;

  return (
    <svg className="hint-arrow" viewBox="0 0 100 100" aria-hidden="true">
      <defs>
        <marker
          id={markerId}
          markerHeight="8"
          markerWidth="8"
          orient="auto"
          refX="7"
          refY="4"
          viewBox="0 0 8 8"
        >
          <path d="M0,0 L8,4 L0,8 Z" />
        </marker>
      </defs>
      <line
        x1={arrow.from.x}
        y1={arrow.from.y}
        x2={arrow.to.x}
        y2={arrow.to.y}
        markerEnd={`url(#${markerId})`}
      />
    </svg>
  );
}

function BoardCell({
  board,
  hintMove,
  position,
  selectedMoves,
  selectedPosition,
  onClick,
}: {
  board: BoardState;
  hintMove: Move | null;
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
      const z = index;
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

function arrowForSlice(
  move: Move,
  slice: Slice,
  columns: number,
  rows: number,
): { from: { x: number; y: number }; to: { x: number; y: number } } | null {
  const fromSlice = move.from.slice(2);
  const toSlice = move.to.slice(2);
  const isFromSlice = positionsEqual(fromSlice, slice.coordinates);
  const isToSlice = positionsEqual(toSlice, slice.coordinates);

  if (!isFromSlice && !isToSlice) {
    return null;
  }

  if (isFromSlice && isToSlice) {
    return {
      from: cellCenter(move.from, columns, rows),
      to: cellCenter(move.to, columns, rows),
    };
  }

  const anchor = isFromSlice ? cellCenter(move.from, columns, rows) : cellCenter(move.to, columns, rows);
  return {
    from: anchor,
    to: {
      x: isFromSlice ? Math.min(96, anchor.x + 18) : Math.max(4, anchor.x - 18),
      y: isFromSlice ? Math.max(4, anchor.y - 18) : Math.min(96, anchor.y + 18),
    },
  };
}

function cellCenter(position: Position, columns: number, rows: number): { x: number; y: number } {
  return {
    x: ((position[0] + 0.5) / columns) * 100,
    y: ((rows - position[1] - 0.5) / rows) * 100,
  };
}

function axisLabel(axis: number): string {
  return ["x", "y", "z", "w"][axis] ?? `axis ${axis + 1}`;
}

function describeMove(piece: Piece | undefined, capturedPiece: Piece | undefined, move: Move): string {
  const actor = piece ? `${piece.color} ${piece.kind}` : "piece";
  const capture = capturedPiece ? ` captures ${capturedPiece.color} ${capturedPiece.kind}` : "";
  return `${actor}${capture}: ${positionKey(move.from)} → ${positionKey(move.to)}`;
}

function sameBoard(left: BoardState, right: BoardState): boolean {
  return (
    left.turn === right.turn
    && left.dimension === right.dimension
    && positionsEqual(left.size, right.size)
    && left.pieces.length === right.pieces.length
    && left.pieces.every((piece, index) => {
      const other = right.pieces[index];
      return Boolean(other)
        && piece.id === other.id
        && piece.kind === other.kind
        && piece.color === other.color
        && piece.hasMoved === other.hasMoved
        && positionsEqual(piece.position, other.position);
    })
  );
}

function formatScore(score: number): string {
  return `${score >= 0 ? "+" : ""}${score.toFixed(1)}`;
}

function cellLabel(position: Position, piece: Piece | undefined): string {
  const base = `Cell ${positionKey(position)}`;
  return piece ? `${base}, ${piece.color} ${piece.kind}` : base;
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}
