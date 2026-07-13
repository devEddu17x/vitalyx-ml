"""Safe loading and integrity validation for exported Vitalyx artifacts."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import tensorflow as tf


logger = logging.getLogger(__name__)

REQUIRED_ARTIFACTS = (
    "vitalyx_e01.keras",
    "preprocessing_metadata.json",
    "evidence_metadata.json",
    "conditions_metadata.json",
    "inference_policy.json",
    "model_config.json",
)


class ArtifactLoadError(RuntimeError):
    """Raised when artifacts are missing or mutually incompatible."""


@dataclass
class ArtifactBundle:
    model: tf.keras.Model
    preprocessing: dict[str, Any]
    evidence_metadata: dict[str, dict[str, Any]]
    conditions_metadata: dict[str, dict[str, Any]]
    inference_policy: dict[str, Any]
    model_config: dict[str, Any]
    artifact_version: str


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactLoadError(f"Cannot read artifact {path.name}: {exc}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1_048_576), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_preprocessing(metadata: dict[str, Any]) -> dict[str, Any]:
    schema = metadata.get("schema")
    if not isinstance(schema, dict):
        raise ArtifactLoadError("preprocessing_metadata.json has no schema object")
    for key in ("binary_indices", "sex_indices"):
        schema[key] = {str(name): int(index) for name, index in schema[key].items()}
    for key in ("categorical_indices", "multiselect_indices"):
        schema[key] = {
            str(code): {str(value): int(index) for value, index in values.items()}
            for code, values in schema[key].items()
        }
    schema["default_feature_values"] = {
        int(index): np.float32(value) for index, value in schema["default_feature_values"].items()
    }
    metadata["class_names"] = [str(name) for name in metadata["class_names"]]
    return metadata


def _verify_manifest(root: Path) -> str:
    manifest_path = root / "artifact_manifest.json"
    if not manifest_path.exists():
        logger.warning("artifact_manifest_missing", extra={"event": "artifact_manifest_missing"})
        return "manifest-unavailable"
    manifest = _read_json(manifest_path)
    for item in manifest.get("files", []):
        candidate = root / item.get("file", "")
        expected_hash = item.get("sha256")
        if expected_hash and candidate.exists() and _sha256(candidate) != expected_hash:
            raise ArtifactLoadError(f"SHA-256 mismatch for {candidate.name}")
    return str(manifest.get("generated_at_utc") or manifest.get("dataset_version") or "manifest-present")


def load_artifacts(root: Path) -> ArtifactBundle:
    """Loads the final E01 model once and validates its artifact contract."""
    root = Path(root)
    missing = [name for name in REQUIRED_ARTIFACTS if not (root / name).is_file()]
    if missing:
        raise ArtifactLoadError(f"Missing required artifacts: {', '.join(missing)}")
    artifact_version = _verify_manifest(root)
    preprocessing = _normalize_preprocessing(_read_json(root / "preprocessing_metadata.json"))
    evidence_metadata = _read_json(root / "evidence_metadata.json")
    conditions_metadata = _read_json(root / "conditions_metadata.json")
    inference_policy = _read_json(root / "inference_policy.json")
    model_config = _read_json(root / "model_config.json")
    model = tf.keras.models.load_model(root / "vitalyx_e01.keras", compile=False)

    feature_count = len(preprocessing["schema"]["feature_names"])
    class_count = len(preprocessing["class_names"])
    if feature_count != 975 or class_count != 49:
        raise ArtifactLoadError(f"Expected 975 features and 49 classes, got {feature_count} and {class_count}")
    if int(model_config.get("feature_count", feature_count)) != feature_count:
        raise ArtifactLoadError("Model configuration feature count does not match preprocessing metadata")
    if int(model_config.get("class_count", class_count)) != class_count:
        raise ArtifactLoadError("Model configuration class count does not match preprocessing metadata")

    probe = model(np.zeros((1, feature_count), dtype=np.float32), training=False).numpy()
    if probe.shape != (1, class_count) or not np.isfinite(probe).all() or not np.allclose(probe.sum(axis=1), 1.0, atol=1e-5):
        raise ArtifactLoadError("Model output is incompatible with the 49-class probability contract")
    logger.info("artifacts_loaded", extra={"event": "artifacts_loaded", "artifact_version": artifact_version})
    return ArtifactBundle(model, preprocessing, evidence_metadata, conditions_metadata, inference_policy, model_config, artifact_version)
