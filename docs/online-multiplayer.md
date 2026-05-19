# Online multiplayer

Server-authoritative human vs human games over invite links.

## Flow

1. Host opens `/play/new`, creates a game, gets a room URL.
2. Guest opens the same `/play/{roomId}` link and joins the open seat.
3. Moves are submitted to `POST /api/rooms/:id/move` and validated via `/api/move`.
4. Clients poll `GET /api/rooms/:id` every ~1.5s for updates.

## Storage

- **Production:** set `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`.
- **Local dev:** in-memory store (rooms reset when the dev server restarts).

## Environment

```bash
NEXT_PUBLIC_APP_URL=http://localhost:3000
ROOM_TTL_SECONDS=604800
UPSTASH_REDIS_REST_URL=
UPSTASH_REDIS_REST_TOKEN=
```

## API

See the full spec in the project PR description: create, join, get, move, resign under `/api/rooms`.
