import { roomErrorResponse } from "@/lib/room-route";
import { parseBearerToken, resignRoom } from "@/lib/room-server";

export const runtime = "nodejs";

type RouteContext = {
  params: Promise<{ roomId: string }>;
};

export async function POST(request: Request, context: RouteContext) {
  try {
    const { roomId } = await context.params;
    const token = parseBearerToken(request.headers.get("authorization"));
    const room = await resignRoom(roomId, token);
    return Response.json({ room });
  } catch (error) {
    return roomErrorResponse(error);
  }
}
