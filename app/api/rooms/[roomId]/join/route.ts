import type { JoinRoomRequest } from "@/lib/game-room";
import { roomErrorResponse } from "@/lib/room-route";
import { joinRoom } from "@/lib/room-server";

export const runtime = "nodejs";

type RouteContext = {
  params: Promise<{ roomId: string }>;
};

export async function POST(request: Request, context: RouteContext) {
  try {
    const { roomId } = await context.params;
    const body = await request.json() as JoinRoomRequest;
    const response = await joinRoom(roomId, body);
    return Response.json(response);
  } catch (error) {
    return roomErrorResponse(error);
  }
}
