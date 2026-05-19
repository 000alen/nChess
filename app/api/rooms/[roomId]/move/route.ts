import type { SubmitMoveRequest } from "@/lib/game-room";
import { roomErrorResponse } from "@/lib/room-route";
import { parseBearerToken, submitRoomMove } from "@/lib/room-server";

export const runtime = "nodejs";

type RouteContext = {
  params: Promise<{ roomId: string }>;
};

export async function POST(request: Request, context: RouteContext) {
  try {
    const { roomId } = await context.params;
    const body = await request.json() as SubmitMoveRequest;
    const token = parseBearerToken(request.headers.get("authorization"));
    const response = await submitRoomMove(roomId, token, body);
    return Response.json(response);
  } catch (error) {
    return roomErrorResponse(error);
  }
}
