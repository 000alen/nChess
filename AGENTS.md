# AGENTS.md

## Cursor Cloud specific instructions

This is a Next.js 16 + Python chess engine application (n-dimensional chess). No external services or databases are required.

### Services

| Service | Command | Port | Notes |
|---------|---------|------|-------|
| Next.js UI (dev) | `pnpm dev` | 3000 | Frontend only; engine-backed features (bot, hints, eval) won't work |
| Full-stack dev | `vercel dev` | 3000 | Serves both UI and Python API functions; requires Vercel auth |

### Key commands

- **Typecheck**: `pnpm typecheck`
- **Build**: `pnpm build`
- **Python tests**: `python3.13 -m unittest discover -s tests -v`
- **Dev server (UI only)**: `pnpm dev`

### Gotchas

- `vercel dev` requires a Vercel account/token (`VERCEL_TOKEN` env var or interactive login). Without it, use `pnpm dev` for UI-only development and validate Python API logic via unit tests.
- Python 3.13 is required (see `.python-version`). Use `python3.13` explicitly since the system default may be an older version.
- The Python engine has zero external dependencies — only stdlib + local `nChess/` package.
- pnpm has a 7-day minimum release age policy (`.npmrc`); newly published packages may not resolve during `pnpm install --frozen-lockfile`.
- The `sharp` package build script is intentionally ignored (see pnpm warning). This is fine — it's an optional dependency.
- The `pyproject.toml` lists `kivy` but that's only for the legacy desktop GUI, not the web app path.
