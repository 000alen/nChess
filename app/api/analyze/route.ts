export const runtime = "nodejs";

type AnalyzeRequest = {
  board: unknown;
  color: "white" | "black";
  maxDepth?: number;
  timeLimitMs?: number;
};

export async function POST(request: Request) {
  const payload = await request.json() as AnalyzeRequest;
  const maxDepth = clampInteger(payload.maxDepth ?? 2, 1, 3);
  const timeLimitMs = clampInteger(payload.timeLimitMs ?? 750, 100, 3000);
  const origin = new URL(request.url).origin;
  const encoder = new TextEncoder();

  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      try {
        for (let depth = 1; depth <= maxDepth; depth += 1) {
          const response = await fetch(`${origin}/api/bot`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              board: payload.board,
              color: payload.color,
              depth,
              timeLimitMs,
            }),
          });
          const result = await response.json();

          controller.enqueue(encoder.encode(`${JSON.stringify({
            ...result,
            requestedDepth: depth,
            ok: response.ok,
          })}\n`));

          if (!response.ok || !result.move) {
            break;
          }
        }
      } catch (error) {
        controller.enqueue(encoder.encode(`${JSON.stringify({
          ok: false,
          error: error instanceof Error ? error.message : "analysis failed",
        })}\n`));
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Cache-Control": "no-store",
      "Content-Type": "application/x-ndjson",
    },
  });
}

function clampInteger(value: number, min: number, max: number): number {
  if (!Number.isFinite(value)) {
    return min;
  }
  return Math.max(min, Math.min(max, Math.trunc(value)));
}
