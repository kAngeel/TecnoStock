# TecnoStock

Two independent apps with no root workspace, shared config, CI, or git repo at the root:

- `backend/` — Python 3.12 + FastAPI scaffold (uv-managed)
- `frontend/` — Angular 22 standalone app with SSR

Run commands from the relevant subdirectory; there are no root-level scripts.

## Frontend (`frontend/`)

Uses npm (pinned `npm@10.9.2`, `package-lock.json`) and Angular CLI 22.

```bash
npm install
npm start                  # ng serve, http://localhost:4200
npm run build              # production build -> dist/frontend/{browser,server}
npm test -- --watch=false  # Vitest via @angular/build:unit-test (Node + jsdom)
```

- Single spec file: `npm test -- --watch=false --include src/app/app.spec.ts`
- Filter by suite/test name: `npm test -- --watch=false --filter "^App"`
- SSR server after a build: `npm run serve:ssr:frontend`; honors `PORT` (default 4000).
- Prettier is configured (`.prettierrc`: width 100, single quotes, Angular HTML parser) but has no npm script and is not CI-enforced. Current scaffold files are not Prettier-clean, so format only files you touch: `npx prettier --write <files>`.
- Tests are Vitest, not Karma. The `ng test` launch config in `.vscode/launch.json` points at Karma's port 9876 and is stale.
- `tsconfig.json` does not enable `strict`; do not assume strict null checks.
- `src/main.ts` is the browser entry; `src/server.ts` is an Express SSR server. `app.routes.server.ts` prerenders every route, and `ng build` uses `outputMode: server`.
- `src/app/app.html` is the Angular CLI placeholder, `app.routes.ts` is empty, and `app.config.server.ts` only supplies the prerender config.

## Backend (`backend/`)

uv project (src layout) with Python fixed to 3.12 by `.python-version`. Use `uv`, not pip.

```bash
uv sync
uv run backend   # runs [project.scripts] backend = "backend:main"
```

- The only code is `src/backend/__init__.py`; `main()` just prints `Hello from backend!`.
- FastAPI and uvicorn are declared dependencies, but there is no FastAPI app, uvicorn entrypoint, routes, tests, lint, or typecheck yet. Do not assume an API exists or guess a `uvicorn` module path.
- Dependency changes must update `uv.lock`.
