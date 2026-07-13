# Vitalyx UI

Single-page academic interface for the Vitalyx pathology-orientation API. The model uses synthetic patient data and does not provide medical diagnoses.

## Local development

```bash
cp .env.example .env
pnpm install
pnpm dev
```

Set `VITE_API_URL=http://localhost:8000` in `.env` when the API runs locally. Vite exposes the UI at `http://localhost:5173`.

## Production build

```bash
pnpm build
```

`VITE_API_URL` is embedded at build time, not read dynamically by the static application.

## Human-readable evidence values

The API retains DDXPlus technical values such as `V_89` to preserve model compatibility. Before a UI build, generate the compact English label catalog from the local source file:

```bash
pnpm generate:evidence-labels
```

This produces `public/evidence-labels.json`. The generated file is served with the UI; the larger `release_evidences.json` source is excluded from the production Docker context.

## Docker

```bash
docker build \
  --build-arg VITE_API_URL=https://api.vitalyx.eddux.dev \
  -t vitalyx-ui:local .

docker run --rm -p 8080:80 vitalyx-ui:local
```

The image uses official multi-architecture Node and Nginx images and is suitable for a native `linux/arm64` build. The server listens on port `80`.

## Dokploy

Configure Dokploy to build this directory with its `Dockerfile`, expose container port `80`, and pass `VITE_API_URL=https://api.vitalyx.eddux.dev` as a **build argument**. Point the frontend domain to the deployed container. The API must allow the frontend origin through CORS.

## API contract

The UI loads `GET /api/v1/evidences` and sends only the friendly `POST /api/v1/predictions` request. It never builds raw `_@_` evidence tokens in the browser.
