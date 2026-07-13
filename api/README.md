# Vitalyx Inference API

Vitalyx is an academic inference API for a multiclass orientation model trained on the synthetic DDXPlus English v2 dataset. It returns possible pathologies for research and educational use only.

> The API is not a medical diagnosis tool and must not be used for automatic clinical decisions. External clinical validation would be required before any real-world use.

## Architecture

```text
HTTP DTO → answer/token validation → shared preprocessor → TensorFlow E01 model → JSON response
```

The service loads `vitalyx_artifacts/vitalyx_e01.keras` and JSON metadata once during application lifespan. It has no database, authentication, session state, datasets, or training code.

## Artifacts

Required files under `vitalyx_artifacts/`:

- `vitalyx_e01.keras`
- `preprocessing_metadata.json`
- `evidence_metadata.json`
- `conditions_metadata.json`
- `inference_policy.json`
- `model_config.json`

`artifact_manifest.json` is optional in the current package. If supplied, its file hashes are checked during startup.

## Run locally

Use Python 3.11 or the Docker image; TensorFlow is not supported by every local Python version.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
ARTIFACTS_PATH=./vitalyx_artifacts uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open Swagger at `http://localhost:8000/docs`.

Useful endpoints:

- `GET /health`
- `GET /ready`
- `GET /api/v1/model`
- `GET /api/v1/evidences?type=boolean&search=fever`
- `GET /api/v1/pathologies`
- `POST /api/v1/predictions`
- `POST /api/v1/predictions/raw`

Friendly request example:

```json
{
  "age": 32,
  "sex": "F",
  "answers": [
    {"evidence_id": "E_91", "present": true},
    {"evidence_id": "E_59", "value": "3"},
    {"evidence_id": "E_55", "values": ["V_89", "V_108"]}
  ],
  "top_k": 5
}
```

The frontend never needs to create `_@_` tokens. The raw endpoint exists only for integration tests and direct notebook-contract reproduction.

## Tests

```bash
pytest -q
```

Tests load only exported artifacts. They cover readiness, catalogs, friendly/raw equivalence, validation errors, vector shape, Top-K ordering, JSON responses, and an API E2E flow.

## Docker and ARM64

The Dockerfile uses the official multi-architecture `python:3.11-slim` base and does not assume `amd64`.

```bash
docker buildx build --platform linux/arm64 -t vitalyx-api:arm64 --load .
docker run --rm -p 8000:8000 -e PORT=8000 vitalyx-api:arm64
```

On an ARM64 VPS, validate with:

```bash
docker run --rm --platform linux/arm64 vitalyx-api:arm64 \
  python -c "import tensorflow as tf; print(tf.__version__); print(tf.keras.models.load_model('/app/vitalyx_artifacts/vitalyx_e01.keras').output_shape)"
```

If TensorFlow does not publish a compatible wheel for the VPS image at deployment time, capture the exact pip error before considering ONNX or TFLite. Do not silently substitute a different model format.

`compose.yaml` provides the minimal local service:

```bash
docker compose up --build
```

## Dokploy deployment

Configure Dokploy to clone this repository and use:

- **Build context:** repository root
- **Dockerfile:** `Dockerfile`
- **Container port:** `8000`
- **Health endpoint:** `/health` (use `/ready` for stricter readiness)
- **Target architecture:** `linux/arm64` / `aarch64`
- **Environment:** `PORT=8000`, `LOG_LEVEL=INFO`, `ARTIFACTS_PATH=/app/vitalyx_artifacts`, `APP_ENV=production`

Set the Dokploy reverse proxy to target port `8000`, then attach a domain and enable HTTPS in Dokploy. No domain-specific configuration is committed here.

Recommended starting resources are 2 vCPU, 4 GB RAM, and enough disk for the image and artifacts; adjust after observing TensorFlow startup and inference memory on the VPS.

## Limitations

The training data are synthetic, class separability may not reflect clinical reality, and probabilities are not clinical certainty. The API reports a low-confidence flag from the exported policy but does not recalibrate or modify the model.
