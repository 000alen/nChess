import { getAppOrigin } from "@/lib/app-origin";
import type { CreateRoomRequest } from "@/lib/game-room";
import { roomErrorResponse } from "@/lib/room-route";
import { createRoom } from "@/lib/room-server";

export const runtime = "nodejs";

export async function POST(request: Request) {
  try {
    const body = await request.json() as CreateRoomRequest;
    const response = await createRoom(body, getAppOrigin());
    return Response.json(response, { status: 201 });
  } catch (error) {
    return roomErrorResponse(error);
  }
}
