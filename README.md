# Vitalyx

Vitalyx is an academic pathology-orientation project built with the synthetic DDXPlus English v2 dataset. It is for research and educational use only; it does not provide medical diagnoses or replace professional care.

## Repository structure

| Directory | Purpose |
| --- | --- |
| [`notebooks/`](notebooks/) | Data analysis, preprocessing, model development, evaluation, and artifact-generation notebook. The main notebook is [`Vitalyx.ipynb`](notebooks/Vitalyx.ipynb). |
| [`api/`](api/) | FastAPI inference service. It loads the exported Keras model and preprocessing metadata, then exposes health, catalog, and prediction endpoints. |
| [`ui/`](ui/) | React, Vite, TypeScript, Tailwind, and shadcn/ui single-page interface. It consumes the API friendly prediction endpoint. |

## Main flow

```text
notebooks/Vitalyx.ipynb
        ↓ exports model artifacts
api/vitalyx_artifacts/
        ↓ serves inference
api/ FastAPI service
        ↓ consumes REST endpoints
ui/ React single-page application
```

## Local development

Run the API from [`api/`](api/):

```bash
docker compose up --build
```

Run the UI from [`ui/`](ui/):

```bash
pnpm install
pnpm generate:evidence-labels
pnpm dev
```

For containerized UI development:

```bash
docker compose up --build
```

See the component-specific READMEs for endpoint, artifact, Docker, environment-variable, and deployment instructions.

## Dataset attribution

The repository includes a copy of the official DDXPlus English dataset, version 2, used exclusively for this academic project. The original data files have not been modified. See [`SOURCE.md`](SOURCE.md) for attribution, source, version, and licensing information.
