"use client";

import type { CSSProperties } from "react";
import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";

import {
  createInitialBoard,
  DEFAULT_BOARD_CONFIG,
  describeEvaluation,
  evaluateBoard,
  MATE_THRESHOLD,
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
  type PieceColor,
  type PieceKind,
  type Position,
} from "@/lib/chess";

type Slice = {
  coordinates: Position;
  label: string;
};

const BoardScene3D = dynamic(
  () => import("@/components/iso-scene").then((mod) => mod.BoardScene3D),
  { ssr: false },
);

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
  timeMs?: number;
};

type EngineEvaluation = {
  loading: boolean;
  score: number | null;
  mateIn: number | null;
  status: EngineStatus | null;
};

type EngineStatus = Record<"white" | "black", {
  inCheck: boolean;
  inCheckmate: boolean;
  inStalemate: boolean;
}>;

type AnalysisPartial = {
  board?: BoardState;
  cached?: boolean;
  depth?: number;
  elapsedMs?: number;
  error?: ApiErrorPayload | string;
  mateIn?: number | null;
  move?: Move | null;
  nodes?: number;
  ok?: boolean;
  requestedDepth?: number;
  score?: number;
  searchElapsedMs?: number;
};

type StreamEvent = {
  type: "started" | "depth" | "final";
  depth?: number;
  score?: number;
  mateIn?: number | null;
  nodes?: number;
  elapsedMs?: number;
  searchElapsedMs?: number;
  move?: Move | null;
  board?: BoardState;
  positionHash?: string;
  requestId?: string;
  maxDepth?: number;
  timeLimitMs?: number;
  color?: string;
};

type ApiErrorPayload = {
  code?: string;
  message?: string;
};

type ApiFailurePayload = {
  detail?: string;
  error?: ApiErrorPayload | string;
};

type Theme = "dark" | "light";
type ViewMode = "flat" | "isometric";
type PromotionKind = Exclude<PieceKind, "king" | "pawn">;
const THEME_STORAGE_KEY = "nchess-theme";
const VIEW_MODE_STORAGE_KEY = "nchess-view-mode";
const ISO_SPACING_STORAGE_KEY = "nchess-iso-spacing";
const ISO_SPACING_MIN = 0.4;
const ISO_SPACING_MAX = 2.0;
const ISO_SPACING_DEFAULT = 1.0;
const BOARD_PRESETS: Array<{ label: string; config: BoardConfig }> = [
  { label: "2D Classic", config: { dimension: 2, size: [8, 8] } },
  { label: "3D Compact", config: { dimension: 3, size: [5, 5, 4] } },
  { label: "4D Classic", config: DEFAULT_BOARD_CONFIG },
];

export function NChessBoard() {
  const [boardConfig, setBoardConfig] = useState<BoardConfig>(DEFAULT_BOARD_CONFIG);
  const [draftConfig, setDraftConfig] = useState<BoardConfig>(DEFAULT_BOARD_CONFIG);
  const [board, setBoard] = useState<BoardState>(() => createInitialBoard(DEFAULT_BOARD_CONFIG));
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null);
  const [moveHistory, setMoveHistory] = useState<MoveRecord[]>([]);
  const [currentPly, setCurrentPly] = useState(0);
  const [theme, setTheme] = useState<Theme>("dark");
  const [themeLoaded, setThemeLoaded] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("flat");
  const [viewModeLoaded, setViewModeLoaded] = useState(false);
  const [isoSpacing, setIsoSpacing] = useState<number>(ISO_SPACING_DEFAULT);
  const [isoLoaded, setIsoLoaded] = useState(false);
  const [isoCameraResetCounter, setIsoCameraResetCounter] = useState(0);
  const [botEnabled, setBotEnabled] = useState(true);
  const [botColor, setBotColor] = useState<PieceColor>("black");
  const [botDepth, setBotDepth] = useState(2);
  const [botTimeLimitMs, setBotTimeLimitMs] = useState(750);
  const [promotionChoice, setPromotionChoice] = useState<PromotionKind>("queen");
  const [botThinking, setBotThinking] = useState(false);
  const [botError, setBotError] = useState<string | null>(null);
  const [hintMove, setHintMove] = useState<Move | null>(null);
  const [hintThinking, setHintThinking] = useState(false);
  const [hintError, setHintError] = useState<string | null>(null);
  const [analysisInfo, setAnalysisInfo] = useState<string | null>(null);
  const [analysisMove, setAnalysisMove] = useState<Move | null>(null);
  const [legalMoves, setLegalMoves] = useState<Move[]>([]);
  const [legalMovesLoading, setLegalMovesLoading] = useState(false);
  const [moveError, setMoveError] = useState<string | null>(null);
  const [engineEvaluation, setEngineEvaluation] = useState<EngineEvaluation>({
    loading: true,
    score: null,
    mateIn: null,
    status: null,
  });

  const fallbackEvaluation = useMemo(() => evaluateBoard(board), [board]);
  const evaluation = engineEvaluation.score ?? fallbackEvaluation;
  const currentStatus = engineEvaluation.status?.[board.turn] ?? null;
  const isViewingPast = currentPly < moveHistory.length;
  const capturedPieces = useMemo(() => moveHistory.flatMap((record) => (
    record.capturedPiece ? [record.capturedPiece] : []
  )), [moveHistory]);
  const canHumanMove = !botThinking && (!botEnabled || board.turn !== botColor);
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
            // Bounded mate-aware iterative deepening. The score we trust is
            // the analytical one from the engine search; the heuristic eval
            // only serves as the bar's continuous fill while the search runs.
            searchDepth: 4,
            searchTimeMs: 250,
          }),
          signal: controller.signal,
        });
        const payload = await response.json() as {
          mateIn?: number | null;
          status?: EngineStatus;
          whiteScore?: number;
        };

        if (!response.ok || typeof payload.whiteScore !== "number") {
          throw new Error("Evaluation request failed");
        }
        const whiteScore = payload.whiteScore;
        const mateIn = typeof payload.mateIn === "number" ? payload.mateIn : null;
        setEngineEvaluation({
          loading: false,
          score: whiteScore,
          mateIn,
          status: payload.status ?? null,
        });
        setMoveHistory((records) => records.map((record) => (
          sameBoard(record.board, board)
            ? { ...record, evaluation: whiteScore, evaluationSource: "engine" }
            : record
        )));
      } catch (error) {
        if (!controller.signal.aborted) {
          setEngineEvaluation({ loading: false, score: null, mateIn: null, status: null });
        }
      }
    }

    void loadEvaluation();

    return () => controller.abort();
  }, [board]);

  useEffect(() => {
    if (!themeLoaded) {
      return;
    }
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme, themeLoaded]);

  useEffect(() => {
    const savedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (savedTheme === "dark" || savedTheme === "light") {
      setTheme(savedTheme);
      setThemeLoaded(true);
      return;
    }
    setTheme(window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    setThemeLoaded(true);
  }, []);

  useEffect(() => {
    if (!viewModeLoaded) {
      return;
    }
    window.localStorage.setItem(VIEW_MODE_STORAGE_KEY, viewMode);
  }, [viewMode, viewModeLoaded]);

  useEffect(() => {
    const savedViewMode = window.localStorage.getItem(VIEW_MODE_STORAGE_KEY);
    if (savedViewMode === "flat" || savedViewMode === "isometric") {
      setViewMode(savedViewMode);
    }
    setViewModeLoaded(true);
  }, []);

  useEffect(() => {
    const savedSpacing = Number(window.localStorage.getItem(ISO_SPACING_STORAGE_KEY));
    if (Number.isFinite(savedSpacing) && savedSpacing > 0) {
      setIsoSpacing(clamp(savedSpacing, ISO_SPACING_MIN, ISO_SPACING_MAX));
    }
    setIsoLoaded(true);
  }, []);

  useEffect(() => {
    if (!isoLoaded) {
      return;
    }
    window.localStorage.setItem(ISO_SPACING_STORAGE_KEY, String(isoSpacing));
  }, [isoLoaded, isoSpacing]);

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
          elapsedMs?: number;
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

  function commitMove(
    currentBoard: BoardState,
    move: Move,
    nextBoard: BoardState,
    actor: MoveActor,
    basePly: number,
    timeMs?: number,
  ): BoardState {
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
      timeMs,
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
          promotion: pieceAt(board, move.from)?.kind === "pawn" ? promotionChoice : undefined,
        }),
      });
      const payload = await response.json() as {
        board?: BoardState;
        elapsedMs?: number;
        move?: Move;
      } & ApiFailurePayload;
      if (!response.ok || !payload.board || !payload.move) {
        throw new Error(responseErrorMessage(payload, "Move request failed"));
      }
      const nextBoard = commitMove(board, payload.move, payload.board, "human", currentPly, payload.elapsedMs);
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
    setAnalysisInfo(null);
    setAnalysisMove(null);
  }

  function applyAnalysisMate(partial: AnalysisPartial | null | undefined) {
    if (!partial) {
      return;
    }
    let mateIn: number | null = null;
    if (typeof partial.mateIn === "number") {
      mateIn = partial.mateIn;
    } else if (typeof partial.score === "number" && Math.abs(partial.score) >= MATE_THRESHOLD) {
      // Server somehow didn't pre-compute; the score is enough on its own
      // because describeEvaluation will recover the distance.
      mateIn = null;
    }
    if (mateIn === null && typeof partial.score !== "number") {
      return;
    }
    setEngineEvaluation((current) => {
      if (mateIn === null && (typeof partial.score !== "number" || Math.abs(partial.score) < MATE_THRESHOLD)) {
        return current;
      }
      return { ...current, mateIn: mateIn ?? current.mateIn };
    });
  }

  async function requestHint() {
    setHintThinking(true);
    setHintError(null);
    try {
      const finalPartial = await streamAnalysis({
        board,
        color: board.turn,
        maxDepth: botDepth,
        timeLimitMs: botTimeLimitMs,
        onPartial: (partial) => {
          if (partial.move) {
            setHintMove(partial.move);
            setAnalysisMove(partial.move);
          }
          setAnalysisInfo(formatAnalysisInfo(partial));
          applyAnalysisMate(partial);
        },
      });

      if (!finalPartial?.move) {
        setHintMove(null);
        setHintError(errorMessage(finalPartial?.error, "No legal hint available."));
        return;
      }
      setHintMove(finalPartial.move);
      applyAnalysisMate(finalPartial);
    } catch (error) {
      setHintError(error instanceof Error ? error.message : "Hint request failed");
    } finally {
      setHintThinking(false);
    }
  }

  async function streamAnalysis({
    board: boardToAnalyze,
    color,
    maxDepth,
    onPartial,
    timeLimitMs,
  }: {
    board: BoardState;
    color: PieceColor;
    maxDepth: number;
    onPartial: (partial: AnalysisPartial) => void;
    timeLimitMs: number;
  }): Promise<AnalysisPartial | null> {
    let response: Response;
    try {
      response = await fetch("/api/bot", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/x-ndjson, application/json",
        },
        body: JSON.stringify({
          board: boardToAnalyze,
          color,
          depth: maxDepth,
          timeLimitMs,
          stream: true,
        }),
      });
    } catch {
      return fallbackPerDepthAnalysis({ boardToAnalyze, color, maxDepth, onPartial, timeLimitMs });
    }

    const contentType = response.headers.get("content-type") ?? "";
    const isStream = contentType.includes("ndjson") || contentType.includes("event-stream");

    if (!response.ok || !response.body || !isStream) {
      // Server returned a single JSON response (older non-streaming branch),
      // either because stream=true wasn't honoured or the request errored
      // before streaming started; surface it as one partial.
      let payload: AnalysisPartial;
      try {
        payload = await readJsonResponse<AnalysisPartial>(response, "Analysis request failed");
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : "Analysis request failed",
          ok: response.ok,
          requestedDepth: maxDepth,
        };
      }
      const partial = { ...payload, ok: response.ok, requestedDepth: maxDepth };
      onPartial(partial);
      return partial;
    }

    let latestPartial: AnalysisPartial | null = null;
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (value) {
        buffer += decoder.decode(value, { stream: true });
        let newlineIndex = buffer.indexOf("\n");
        while (newlineIndex >= 0) {
          const line = buffer.slice(0, newlineIndex).trim();
          buffer = buffer.slice(newlineIndex + 1);
          newlineIndex = buffer.indexOf("\n");
          if (!line) continue;
          let event: StreamEvent;
          try {
            event = JSON.parse(line) as StreamEvent;
          } catch {
            continue;
          }
          if (event.type === "depth" || event.type === "final") {
            const partial: AnalysisPartial = {
              board: event.board,
              cached: false,
              depth: event.depth,
              elapsedMs: event.elapsedMs,
              mateIn: event.mateIn ?? null,
              move: event.move ?? null,
              nodes: event.nodes,
              ok: true,
              requestedDepth: maxDepth,
              score: event.score,
              searchElapsedMs: event.searchElapsedMs,
            };
            latestPartial = partial;
            onPartial(partial);
          }
        }
      }
      if (done) break;
    }
    return latestPartial;
  }

  async function fallbackPerDepthAnalysis({
    boardToAnalyze,
    color,
    maxDepth,
    onPartial,
    timeLimitMs,
  }: {
    boardToAnalyze: BoardState;
    color: PieceColor;
    maxDepth: number;
    onPartial: (partial: AnalysisPartial) => void;
    timeLimitMs: number;
  }): Promise<AnalysisPartial | null> {
    let latestPartial: AnalysisPartial | null = null;
    for (let depth = 1; depth <= maxDepth; depth += 1) {
      const response = await fetch("/api/bot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ board: boardToAnalyze, color, depth, timeLimitMs }),
      });
      const payload = await readJsonResponse<AnalysisPartial>(response, "Analysis request failed");
      const partial = { ...payload, ok: response.ok, requestedDepth: depth };
      latestPartial = partial;
      onPartial(partial);
      if (!response.ok || !partial.move) break;
    }
    return latestPartial;
  }

  async function requestBotMove(currentBoard: BoardState, basePly = currentPly) {
    if (!botEnabled || currentBoard.turn !== botColor) {
      return;
    }

    setBotThinking(true);
    setBotError(null);
    try {
      const finalPartial = await streamAnalysis({
        board: currentBoard,
        color: botColor,
        maxDepth: botDepth,
        timeLimitMs: botTimeLimitMs,
        onPartial: (partial) => {
          if (partial.move) {
            setHintMove(partial.move);
            setAnalysisMove(partial.move);
          }
          setAnalysisInfo(formatAnalysisInfo(partial));
          applyAnalysisMate(partial);
        },
      });

      if (!finalPartial?.move) {
        setBotError(errorMessage(finalPartial?.error, "Bot has no legal move."));
        return;
      }
      applyAnalysisMate(finalPartial);

      const botMove = finalPartial.move;
      if (finalPartial.board) {
        commitMove(currentBoard, botMove, finalPartial.board, "bot", basePly, finalPartial.elapsedMs);
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
        const movePayload = await response.json() as { board?: BoardState; elapsedMs?: number };
        if (!response.ok || !movePayload.board) {
          throw new Error("Bot move application failed");
        }
        commitMove(currentBoard, botMove, movePayload.board, "bot", basePly, movePayload.elapsedMs);
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
        <div className="top-bar-actions">
          {board.dimension >= 3 ? (
            <button
              className="theme-toggle"
              type="button"
              aria-pressed={viewMode === "isometric"}
              aria-label={`Switch to ${viewMode === "isometric" ? "flat" : "isometric"} view`}
              onClick={() => setViewMode((current) => (current === "isometric" ? "flat" : "isometric"))}
            >
              {viewMode === "isometric" ? "Flat view" : "Isometric"}
            </button>
          ) : null}
          <button
            className="theme-toggle"
            type="button"
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            onClick={() => setTheme((currentTheme) => (currentTheme === "dark" ? "light" : "dark"))}
          >
            {theme === "dark" ? "Light mode" : "Dark mode"}
          </button>
        </div>
      </header>

      <section className="game-layout" aria-label="nChess game">
        <VerticalEvaluationBar
          loading={engineEvaluation.loading}
          mateIn={engineEvaluation.mateIn}
          positionHash={board.hash}
          score={evaluation}
          source={engineEvaluation.score === null ? "local" : "engine"}
        />

        <div className="board-stack" data-view-mode={board.dimension >= 3 ? viewMode : "flat"}>
          {board.dimension >= 3 ? (
            <div className="iso-canvas-shell" key={`iso-${isoCameraResetCounter}`}>
              <BoardScene3D
                analysisMove={analysisMove}
                board={board}
                canHumanMove={canHumanMove}
                hintMove={hintMove}
                selectedMoves={selectedMoves}
                selectedPosition={selectedPosition}
                spacing={isoSpacing}
                viewMode={viewMode}
                onCellClick={handleCellClick}
              />
            </div>
          ) : (
            <div className="slice-grid" style={{ "--slice-columns": sliceColumnCount(board) } as CSSProperties}>
              {slicesForBoard(board).map((slice) => (
                <BoardSlice
                  key={slice.coordinates.join(",") || "2d"}
                  board={board}
                  canHumanMove={canHumanMove}
                  hintMove={hintMove}
                  slice={slice}
                  selectedMoves={selectedMoves}
                  selectedPosition={selectedPosition}
                  onCellClick={handleCellClick}
                  onDropMove={(from, to) => {
                    void requestHumanMove({ from, to });
                  }}
                />
              ))}
            </div>
          )}
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
          {botError ? <p className="bot-error">{botError}</p> : null}
          {moveError ? <p className="bot-error">{moveError}</p> : null}
          <BoardSetup
            config={draftConfig}
            currentConfig={boardConfig}
            onApply={startNewGame}
            onChange={setDraftConfig}
          />
          {board.dimension >= 3 ? (
            <IsometricControls
              isoSpacing={isoSpacing}
              showSpacing={viewMode === "isometric"}
              viewMode={viewMode}
              onIsoSpacingChange={(value) => setIsoSpacing(clamp(value, ISO_SPACING_MIN, ISO_SPACING_MAX))}
              onResetCamera={() => setIsoCameraResetCounter((value) => value + 1)}
              onResetSpacing={() => setIsoSpacing(ISO_SPACING_DEFAULT)}
            />
          ) : null}
          <BotSettings
            botColor={botColor}
            depth={botDepth}
            onBotColorChange={setBotColor}
            timeLimitMs={botTimeLimitMs}
            onDepthChange={setBotDepth}
            onTimeLimitChange={setBotTimeLimitMs}
          />
          <PromotionSettings
            promotionChoice={promotionChoice}
            onPromotionChoiceChange={setPromotionChoice}
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
              disabled={botThinking || board.turn !== botColor}
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
          {analysisInfo ? <p className="analysis-line">{analysisInfo}</p> : null}
          {analysisMove ? (
            <p className="analysis-line">
              PV: {formatPosition(analysisMove.from)} → {formatPosition(analysisMove.to)}
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
      <div className="preset-grid" aria-label="Board presets">
        {BOARD_PRESETS.map((preset) => (
          <button
            className="secondary-button compact"
            key={preset.label}
            type="button"
            onClick={() => onChange(normalizeBoardConfig(preset.config))}
          >
            {preset.label}
          </button>
        ))}
      </div>
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

function IsometricControls({
  isoSpacing,
  onIsoSpacingChange,
  onResetCamera,
  onResetSpacing,
  showSpacing,
  viewMode,
}: {
  isoSpacing: number;
  onIsoSpacingChange: (value: number) => void;
  onResetCamera: () => void;
  onResetSpacing: () => void;
  showSpacing: boolean;
  viewMode: "flat" | "isometric";
}) {
  return (
    <section className="setup-card" aria-label="3D scene controls">
      <div className="setup-heading">
        <h3>3D scene</h3>
        <span>{viewMode === "isometric" ? "Isometric" : "Flat"}</span>
      </div>
      {showSpacing ? (
        <label className="field">
          <span>Slice spacing {Math.round(isoSpacing * 100)}%</span>
          <input
            type="range"
            min={ISO_SPACING_MIN * 100}
            max={ISO_SPACING_MAX * 100}
            step={1}
            value={Math.round(isoSpacing * 100)}
            onChange={(event) => onIsoSpacingChange(Number(event.target.value) / 100)}
          />
        </label>
      ) : null}
      <div className="axis-grid">
        {showSpacing ? (
          <button className="secondary-button compact" type="button" onClick={onResetSpacing}>
            Reset spacing
          </button>
        ) : null}
        <button className="secondary-button compact" type="button" onClick={onResetCamera}>
          Reset camera
        </button>
      </div>
      <p className="setup-note">
        {viewMode === "isometric"
          ? "Iso: drag to orbit, scroll to zoom, right-drag to pan. Hint moves render as orange arcs across slices; analysis as cyan dashed."
          : "Flat: scroll to zoom, right-drag to pan. Toggle to Isometric to lift the boards into a 3D stack."}
      </p>
    </section>
  );
}

function BotSettings({
  botColor,
  depth,
  timeLimitMs,
  onBotColorChange,
  onDepthChange,
  onTimeLimitChange,
}: {
  botColor: PieceColor;
  depth: number;
  timeLimitMs: number;
  onBotColorChange: (color: PieceColor) => void;
  onDepthChange: (depth: number) => void;
  onTimeLimitChange: (timeLimitMs: number) => void;
}) {
  return (
    <section className="setup-card" aria-label="Bot settings">
      <div className="setup-heading">
        <h3>Bot settings</h3>
        <span>Timed search</span>
      </div>
      <div className="axis-grid">
        <label className="field">
          <span>Bot color</span>
          <select value={botColor} onChange={(event) => onBotColorChange(event.target.value as PieceColor)}>
            <option value="black">Black</option>
            <option value="white">White</option>
          </select>
        </label>
        <label className="field">
          <span>Depth</span>
          <input
            type="number"
            min={1}
            max={6}
            value={depth}
            onChange={(event) => onDepthChange(clamp(Number(event.target.value), 1, 6))}
          />
        </label>
        <label className="field">
          <span>Time ms</span>
          <input
            type="number"
            min={100}
            max={10000}
            step={100}
            value={timeLimitMs}
            onChange={(event) => onTimeLimitChange(clamp(Number(event.target.value), 100, 10000))}
          />
        </label>
      </div>
    </section>
  );
}

function PromotionSettings({
  promotionChoice,
  onPromotionChoiceChange,
}: {
  promotionChoice: PromotionKind;
  onPromotionChoiceChange: (kind: PromotionKind) => void;
}) {
  return (
    <section className="setup-card" aria-label="Promotion settings">
      <div className="setup-heading">
        <h3>Promotion</h3>
        <span>Choice</span>
      </div>
      <label className="field">
        <span>Promote pawns to</span>
        <select
          value={promotionChoice}
          onChange={(event) => onPromotionChoiceChange(event.target.value as PromotionKind)}
        >
          <option value="queen">Queen</option>
          <option value="rook">Rook</option>
          <option value="bishop">Bishop</option>
          <option value="knight">Knight</option>
        </select>
      </label>
    </section>
  );
}

function VerticalEvaluationBar({
  loading,
  mateIn,
  positionHash,
  score,
  source,
}: {
  loading: boolean;
  mateIn: number | null;
  positionHash?: string;
  score: number;
  source: "engine" | "local";
}) {
  const view = describeEvaluation(score, mateIn);
  const tooltipParts = [
    `${source === "engine" ? "Engine" : "Local"} eval ${view.label}`,
    view.isMate ? "forced mate" : null,
    positionHash ? `pos ${positionHash}` : null,
  ].filter(Boolean) as string[];

  return (
    <aside
      className="eval-rail"
      aria-label={`Evaluation ${view.label}`}
      data-mate={view.isMate || undefined}
      title={tooltipParts.join(" · ")}
    >
      <span className="eval-rail-score" data-loading={loading || undefined} data-mate={view.isMate || undefined}>
        {view.label}
      </span>
      <div className="eval-rail-track" aria-hidden="true">
        <div className="eval-rail-fill" style={{ height: `${view.fillPercent}%` }} />
        <div className="eval-rail-marker" style={{ bottom: `${view.fillPercent}%` }} />
      </div>
    </aside>
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
                  {typeof record.timeMs === "number" ? <span className="move-time">{formatTime(record.timeMs)}</span> : null}
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
  canHumanMove,
  hintMove,
  slice,
  selectedMoves,
  selectedPosition,
  onCellClick,
  onDropMove,
}: {
  board: BoardState;
  canHumanMove: boolean;
  hintMove: Move | null;
  slice: Slice;
  selectedMoves: Move[];
  selectedPosition: Position | null;
  onCellClick: (position: Position) => void | Promise<void>;
  onDropMove: (from: Position, to: Position) => void;
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
          canHumanMove={canHumanMove}
          hintMove={hintMove}
          position={position}
          selectedMoves={selectedMoves}
          selectedPosition={selectedPosition}
          onClick={onCellClick}
          onDropMove={onDropMove}
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
  canHumanMove,
  hintMove,
  position,
  selectedMoves,
  selectedPosition,
  onClick,
  onDropMove,
}: {
  board: BoardState;
  canHumanMove: boolean;
  hintMove: Move | null;
  position: Position;
  selectedMoves: Move[];
  selectedPosition: Position | null;
  onClick: (position: Position) => void | Promise<void>;
  onDropMove: (from: Position, to: Position) => void;
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
      draggable={Boolean(canHumanMove && piece?.color === board.turn)}
      type="button"
      onDragOver={(event) => {
        event.preventDefault();
      }}
      onDragStart={(event) => {
        event.dataTransfer.setData("application/x-nchess-position", JSON.stringify(position));
      }}
      onDrop={(event) => {
        event.preventDefault();
        const rawPosition = event.dataTransfer.getData("application/x-nchess-position");
        if (!rawPosition) {
          return;
        }
        onDropMove(JSON.parse(rawPosition) as Position, position);
      }}
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
  return `${actor}${capture}: ${formatPosition(move.from)} → ${formatPosition(move.to)}`;
}

function sameBoard(left: BoardState, right: BoardState): boolean {
  return (
    left.turn === right.turn
    && left.dimension === right.dimension
    && positionsEqual(left.size, right.size)
    && left.pieces.length === right.pieces.length
    && canonicalPieces(left).every((piece, index) => piece === canonicalPieces(right)[index])
  );
}

function canonicalPieces(board: BoardState): string[] {
  return board.pieces
    .map((piece) => [
      piece.id,
      piece.kind,
      piece.color,
      piece.hasMoved ? "1" : "0",
      positionKey(piece.position),
    ].join(":"))
    .sort();
}

function formatScore(score: number): string {
  if (Math.abs(score) >= MATE_THRESHOLD) {
    return describeEvaluation(score).label;
  }
  return `${score >= 0 ? "+" : ""}${score.toFixed(1)}`;
}

function formatTime(timeMs: number): string {
  return `${Math.round(timeMs)}ms`;
}

function formatAnalysisInfo(partial: AnalysisPartial): string {
  if (partial.error) {
    return errorMessage(partial.error, "Analysis failed");
  }
  const depth = partial.depth ?? partial.requestedDepth ?? 0;
  const score = typeof partial.score === "number" ? ` ${formatScore(partial.score)}` : "";
  const nodes = typeof partial.nodes === "number" ? ` ${partial.nodes} nodes` : "";
  const elapsed = typeof partial.searchElapsedMs === "number" ? ` ${formatTime(partial.searchElapsedMs)}` : "";
  const cached = partial.cached ? " cached" : "";
  return `Depth ${depth}${score}${nodes}${elapsed}${cached}`;
}

function errorMessage(error: ApiErrorPayload | string | undefined, fallback: string): string {
  if (!error) {
    return fallback;
  }
  if (typeof error === "string") {
    return error;
  }
  return error.message ?? error.code ?? fallback;
}

function responseErrorMessage(payload: ApiFailurePayload, fallback: string): string {
  return payload.detail ?? errorMessage(payload.error, fallback);
}

async function readJsonResponse<T>(response: Response, fallbackMessage: string): Promise<T> {
  const text = await response.text();
  try {
    return JSON.parse(text) as T;
  } catch {
    const preview = text.trim().slice(0, 80);
    throw new Error(`${fallbackMessage}: ${preview || "empty response"}`);
  }
}

function formatPosition(position: Position): string {
  const file = String.fromCharCode("a".charCodeAt(0) + position[0]);
  const rank = position[1] + 1;
  const extras = position.slice(2).map((coordinate, index) => `${axisLabel(index + 2)}${coordinate}`).join(".");
  return extras ? `${file}${rank}.${extras}` : `${file}${rank}`;
}

function cellLabel(position: Position, piece: Piece | undefined): string {
  const base = `Cell ${positionKey(position)}`;
  return piece ? `${base}, ${piece.color} ${piece.kind}` : base;
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}
