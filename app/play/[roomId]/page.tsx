import { Suspense } from "react";

import { PlayRoomClient } from "@/components/play-room-client";

type PlayRoomPageProps = {
  params: Promise<{ roomId: string }>;
};

export default async function PlayRoomPage({ params }: PlayRoomPageProps) {
  const { roomId } = await params;
  return (
    <Suspense fallback={<main className="play-page"><p>Loading…</p></main>}>
      <PlayRoomClient roomId={roomId} />
    </Suspense>
  );
}
