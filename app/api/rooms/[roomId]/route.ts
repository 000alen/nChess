import { roomErrorResponse } from "@/lib/room-route";
import { getRoomSnapshot, parseBearerToken } from "@/lib/room-server";

export const runtime = "nodejs";

type RouteContext = {
  params: Promise<{ roomId: string }>;
};

export async function GET(request: Request, context: RouteContext) {
  try {
    const { roomId } = await context.params;
    const sinceVersionRaw = new URL(request.url).searchParams.get("sinceVersion");
    const sinceVersion = sinceVersionRaw ? Number(sinceVersionRaw) : undefined;
    const token = parseBearerToken(request.headers.get("authorization"));
    const snapshot = await getRoomSnapshot(
      roomId,
      token,
      Number.isFinite(sinceVersion) ? sinceVersion : undefined,
    );
    return Response.json(snapshot);
  } catch (error) {
    return roomErrorResponse(error);
  }
}
