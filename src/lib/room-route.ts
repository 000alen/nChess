import { RoomError, type RoomApiError } from "@/lib/game-room";

export function roomErrorResponse(error: unknown): Response {
  if (error instanceof RoomError) {
    const body: RoomApiError = {
      error: { code: error.code, message: error.message },
    };
    return Response.json(body, { status: error.status });
  }
  console.error(error);
  const body: RoomApiError = {
    error: { code: "INVALID_REQUEST", message: "Unexpected server error" },
  };
  return Response.json(body, { status: 500 });
}
