"""Artifact-backed token adaptation, preprocessing, and prediction services."""

from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np
from scipy import sparse

from app.artifacts import ArtifactBundle
from app.schemas import ACADEMIC_NOTICE


logger = logging.getLogger(__name__)
TYPE_NAMES = {"B": "boolean", "C": "single_choice", "M": "multiple_choice"}


class InputValidationError(ValueError):
    """A client input cannot be converted to a valid Vitalyx feature vector."""


def parse_raw_token(token: str, evidence_metadata: dict[str, dict[str, Any]]) -> tuple[str, str | None]:
    if not isinstance(token, str) or not token:
        raise InputValidationError("Evidence tokens must be non-empty strings")
    code, separator, raw_value = token.partition("_@_")
    if not code or (separator and not raw_value):
        raise InputValidationError(f"Malformed evidence token: {token!r}")
    entry = evidence_metadata.get(code)
    if entry is None:
        raise InputValidationError(f"Unknown evidence id: {code}")
    kind = entry["data_type"]
    if kind == "B" and separator:
        raise InputValidationError(f"Boolean evidence {code} does not accept a value")
    if kind in {"C", "M"}:
        if not separator:
            raise InputValidationError(f"Evidence {code} requires an explicit value")
        if raw_value not in set(entry["allowed_values"]):
            raise InputValidationError(f"Unsupported value for evidence {code}")
    return code, raw_value if separator else None


class EvidenceTokenAdapter:
    """Converts frontend-friendly answers to validated DDXPlus tokens."""

    def __init__(self, evidence_metadata: dict[str, dict[str, Any]]) -> None:
        self.evidence_metadata = evidence_metadata

    def friendly_to_tokens(self, answers: list[dict[str, Any]]) -> list[str]:
        tokens: list[str] = []
        seen: set[str] = set()
        for answer in answers:
            evidence_id = answer["evidence_id"]
            if evidence_id in seen:
                raise InputValidationError(f"Duplicate or contradictory answer for {evidence_id}")
            seen.add(evidence_id)
            entry = self.evidence_metadata.get(evidence_id)
            if entry is None:
                raise InputValidationError(f"Unknown evidence id: {evidence_id}")
            kind = entry["data_type"]
            present, value, values = answer.get("present"), answer.get("value"), answer.get("values")
            if kind == "B":
                if present is None or value is not None or values is not None:
                    raise InputValidationError(f"Boolean evidence {evidence_id} requires only present")
                if present:
                    tokens.append(evidence_id)
            elif kind == "C":
                if present is not None or values is not None or not value:
                    raise InputValidationError(f"Single-choice evidence {evidence_id} requires only value")
                tokens.append(f"{evidence_id}_@_{value}")
            elif kind == "M":
                if present is not None or value is not None or not isinstance(values, list) or not values:
                    raise InputValidationError(f"Multiple-choice evidence {evidence_id} requires non-empty values")
                if len(values) != len(set(values)):
                    raise InputValidationError(f"Multiple-choice evidence {evidence_id} has duplicate values")
                tokens.extend(f"{evidence_id}_@_{item}" for item in values)
            else:
                raise InputValidationError(f"Unsupported evidence type for {evidence_id}")
        if not tokens:
            raise InputValidationError("Answers produce no observed evidence tokens")
        self.validate_raw_tokens(tokens)
        return tokens

    def validate_raw_tokens(self, tokens: list[str]) -> None:
        categorical_seen: set[str] = set()
        boolean_seen: set[str] = set()
        multiselect_seen: dict[str, set[str]] = {}
        for token in tokens:
            code, raw_value = parse_raw_token(token, self.evidence_metadata)
            kind = self.evidence_metadata[code]["data_type"]
            if kind == "C":
                if code in categorical_seen:
                    raise InputValidationError(f"Duplicate categorical evidence: {code}")
                categorical_seen.add(code)
            elif kind == "B":
                if code in boolean_seen:
                    raise InputValidationError(f"Duplicate boolean evidence: {code}")
                boolean_seen.add(code)
            else:
                values = multiselect_seen.setdefault(code, set())
                if raw_value in values:
                    raise InputValidationError(f"Duplicate multiple-choice value for {code}")
                values.add(raw_value or "")


class VitalyxPreprocessor:
    """The only feature transformation implementation used by both endpoints."""

    def __init__(self, bundle: ArtifactBundle) -> None:
        self.metadata = bundle.preprocessing
        self.schema = bundle.preprocessing["schema"]
        self.adapter = EvidenceTokenAdapter(bundle.evidence_metadata)

    def transform(self, age: float, sex: str, tokens: list[str]) -> sparse.csr_matrix:
        if isinstance(age, bool) or not np.isfinite(float(age)):
            raise InputValidationError("Age must be a finite number")
        age = float(age)
        if not self.metadata["age_min"] <= age <= self.metadata["age_max"]:
            raise InputValidationError("Age is outside the artifact-supported range")
        sex = str(sex)
        if sex not in self.schema["sex_indices"]:
            raise InputValidationError("Sex is not accepted by the artifact")
        self.adapter.validate_raw_tokens(tokens)
        values: dict[int, np.float32] = dict(self.schema["default_feature_values"])
        explicit_multiselect: set[str] = set()
        for token in tokens:
            code, raw_value = parse_raw_token(token, self.adapter.evidence_metadata)
            kind = self.adapter.evidence_metadata[code]["data_type"]
            if kind == "B":
                values[self.schema["binary_indices"][code]] = np.float32(1)
            elif kind == "C":
                for index in self.schema["categorical_indices"][code].values():
                    values.pop(index, None)
                values[self.schema["categorical_indices"][code][raw_value]] = np.float32(1)
            else:
                if code not in explicit_multiselect:
                    for default in self.schema["evidence_defaults"][code]:
                        index = self.schema["multiselect_indices"][code].get(default)
                        if index is not None:
                            values.pop(index, None)
                    explicit_multiselect.add(code)
                values[self.schema["multiselect_indices"][code][raw_value]] = np.float32(1)
        normalized_age = np.float32((age - self.metadata["age_mean"]) / self.metadata["age_std"])
        if normalized_age != 0:
            values[0] = normalized_age
        values[self.schema["sex_indices"][sex]] = np.float32(1)
        return sparse.coo_matrix(
            (np.asarray(list(values.values()), dtype=np.float32), (np.zeros(len(values), dtype=np.int32), np.asarray(list(values), dtype=np.int32))),
            shape=(1, len(self.schema["feature_names"])),
            dtype=np.float32,
        ).tocsr()


class PredictionService:
    """Coordinates shared preprocessing, TensorFlow inference, and response mapping."""

    def __init__(self, bundle: ArtifactBundle) -> None:
        self.bundle = bundle
        self.preprocessor = VitalyxPreprocessor(bundle)

    def predict(self, age: float, sex: str, tokens: list[str], top_k: int) -> dict[str, Any]:
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 49:
            raise InputValidationError("top_k must be an integer from 1 to 49")
        started = time.perf_counter()
        matrix = self.preprocessor.transform(age, sex, tokens)
        probabilities = self.bundle.model(matrix.toarray().astype(np.float32, copy=False), training=False).numpy()[0]
        if probabilities.shape != (49,) or not np.isfinite(probabilities).all() or not np.isclose(probabilities.sum(), 1.0, atol=1e-5):
            raise RuntimeError("Model returned invalid probabilities")
        order = np.argsort(-probabilities)[:top_k]
        maximum_probability = float(probabilities[order[0]])
        threshold = float(self.bundle.inference_policy["low_confidence_threshold"])
        response = {
            "predictions": [{"rank": rank, "pathology": self.bundle.preprocessing["class_names"][index], "probability": float(probabilities[index])} for rank, index in enumerate(order, 1)],
            "confidence": {"maximum_probability": maximum_probability, "low_confidence": maximum_probability < threshold, "threshold": threshold},
            "input_summary": {"age": float(age), "sex": str(sex), "answer_count": len(tokens), "generated_token_count": len(tokens)},
            "model": {"name": str(self.bundle.model_config["model_name"])},
            "disclaimer": ACADEMIC_NOTICE,
        }
        logger.info("inference_completed", extra={"event": "inference_completed", "duration_ms": round((time.perf_counter() - started) * 1000, 2), "generated_token_count": len(tokens), "low_confidence": response["confidence"]["low_confidence"]})
        return response
