"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { DEFAULT_BOARD_CONFIG, normalizeBoardConfig, type BoardConfig, type PieceColor } from "@/lib/chess";
import { apiCreateRoom } from "@/lib/room-api";
import { saveOnlineSession } from "@/lib/online-session";

const PRESETS: Array<{ label: string; config: BoardConfig }> = [
  { label: "2D Classic (8×8)", config: { dimension: 2, size: [8, 8] } },
  { label: "3D Compact", config: { dimension: 3, size: [5, 5, 4] } },
  { label: "4D Classic", config: DEFAULT_BOARD_CONFIG },
];

export default function NewOnlineGamePage() {
  const router = useRouter();
  const [config, setConfig] = useState<BoardConfig>(PRESETS[0].config);
  const [seat, setSeat] = useState<PieceColor>("white");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [inviteUrl, setInviteUrl] = useState<string | null>(null);

  async function handleCreate() {
    setCreating(true);
    setError(null);
    try {
      const playerId = crypto.randomUUID();
      const response = await apiCreateRoom({
        boardConfig: normalizeBoardConfig(config),
        seat,
        playerId,
      });
      saveOnlineSession({
        roomId: response.room.id,
        myColor: response.myColor,
        token: response.token,
        playerId: response.playerId,
      });
      setInviteUrl(response.inviteUrl);
      router.push(`/play/${response.room.id}`);
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Failed to create game");
    } finally {
      setCreating(false);
    }
  }

  return (
    <main className="play-page">
      <header className="play-page-header">
        <Link className="play-back-link" href="/">
          ← Local play
        </Link>
        <h1>Create online game</h1>
        <p>Share the invite link after creating. You play as {seat}.</p>
      </header>

      <section className="play-setup-card">
        <label className="field">
          <span>Board</span>
          <select
            value={PRESETS.findIndex((preset) => preset.config.dimension === config.dimension && preset.config.size[0] === config.size[0])}
            onChange={(event) => setConfig(PRESETS[Number(event.target.value)].config)}
          >
            {PRESETS.map((preset, index) => (
              <option key={preset.label} value={index}>
                {preset.label}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Your color</span>
          <select value={seat} onChange={(event) => setSeat(event.target.value as PieceColor)}>
            <option value="white">White</option>
            <option value="black">Black</option>
          </select>
        </label>

        <button className="primary-button" type="button" disabled={creating} onClick={() => void handleCreate()}>
          {creating ? "Creating…" : "Create game"}
        </button>

        {error ? <p className="bot-error">{error}</p> : null}
        {inviteUrl ? (
          <p className="play-invite-hint">
            Invite link copied to navigation. Waiting room: <code>{inviteUrl}</code>
          </p>
        ) : null}
      </section>
    </main>
  );
}
