"""FastAPI application exposing Vitalyx academic orientation predictions."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request

from app.artifacts import ArtifactLoadError, load_artifacts
from app.logging_config import configure_logging
from app.schemas import EvidenceCatalogResponse, EvidenceItem, FriendlyPredictionRequest, PathologyCatalogResponse, PathologyItem, PredictionResponse, RawPredictionRequest
from app.services import EvidenceTokenAdapter, InputValidationError, PredictionService, TYPE_NAMES
from app.settings import Settings


settings = Settings.from_environment()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.bundle = None
    app.state.prediction_service = None
    app.state.startup_error = None
    try:
        bundle = load_artifacts(settings.artifacts_path)
        app.state.bundle = bundle
        app.state.prediction_service = PredictionService(bundle)
        logger.info("application_ready", extra={"event": "application_ready", "artifact_version": bundle.artifact_version})
    except ArtifactLoadError as exc:
        app.state.startup_error = str(exc)
        logger.error("application_not_ready", extra={"event": "application_not_ready"})
    yield


app = FastAPI(
    title="Vitalyx Inference API",
    version="1.0.0",
    description="Academic synthetic-patient orientation API. It is not a clinical decision system.",
    lifespan=lifespan,
)


def service_or_503(request: Request) -> PredictionService:
    service = request.app.state.prediction_service
    if service is None:
        raise HTTPException(status_code=503, detail={"status": "not_ready", "reason": request.app.state.startup_error or "artifacts are not loaded"})
    return service


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["Health"])
def ready(request: Request) -> dict[str, int | bool | str]:
    bundle = request.app.state.bundle
    if bundle is None:
        raise HTTPException(status_code=503, detail={"status": "not_ready", "reason": request.app.state.startup_error or "artifacts are not loaded"})
    return {"status": "ready", "model_loaded": True, "feature_count": len(bundle.preprocessing["schema"]["feature_names"]), "class_count": len(bundle.preprocessing["class_names"])}


@app.get("/api/v1/model", tags=["Catalogs"])
def model_information(request: Request) -> dict[str, object]:
    bundle = service_or_503(request).bundle
    policy = bundle.inference_policy
    return {"name": bundle.model_config["model_name"], "feature_count": bundle.model_config["feature_count"], "class_count": bundle.model_config["class_count"], "low_confidence_threshold": policy["low_confidence_threshold"], "valid_age_range": policy["valid_age_range"], "accepted_sexes": policy["accepted_sexes"], "disclaimer": policy["disclaimer"]}


@app.get("/api/v1/evidences", response_model=EvidenceCatalogResponse, tags=["Catalogs"])
def evidence_catalog(request: Request, type: Literal["boolean", "single_choice", "multiple_choice"] | None = None, is_antecedent: bool | None = None, search: str | None = Query(default=None, max_length=200)) -> dict[str, object]:
    metadata = service_or_503(request).bundle.evidence_metadata
    needle = (search or "").casefold()
    items = []
    for evidence_id, item in metadata.items():
        public_type = TYPE_NAMES[item["data_type"]]
        if type and public_type != type: continue
        if is_antecedent is not None and bool(item["is_antecedent"]) != is_antecedent: continue
        if needle and needle not in evidence_id.casefold() and needle not in item["question"].casefold(): continue
        items.append(EvidenceItem(id=evidence_id, type=public_type, question=item["question"], is_antecedent=item["is_antecedent"], default_values=item["default_values"], allowed_values=item["allowed_values"]))
    return {"items": items, "total": len(items)}


@app.get("/api/v1/pathologies", response_model=PathologyCatalogResponse, tags=["Catalogs"])
def pathology_catalog(request: Request) -> dict[str, object]:
    bundle = service_or_503(request).bundle
    items = []
    for name in bundle.preprocessing["class_names"]:
        metadata = bundle.conditions_metadata.get(name, {})
        items.append(PathologyItem(id=name, name=metadata.get("cond-name-eng", name), icd10_id=metadata.get("icd10-id")))
    return {"items": items, "total": len(items)}


def _predict(request: Request, age: float, sex: str, tokens: list[str], top_k: int) -> dict[str, object]:
    try:
        return service_or_503(request).predict(age, sex, tokens, top_k)
    except InputValidationError as exc:
        logger.info("input_validation_failed", extra={"event": "input_validation_failed"})
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/predictions", response_model=PredictionResponse, tags=["Predictions"])
def friendly_prediction(request: Request, payload: FriendlyPredictionRequest) -> dict[str, object]:
    service = service_or_503(request)
    try:
        tokens = EvidenceTokenAdapter(service.bundle.evidence_metadata).friendly_to_tokens([answer.model_dump() for answer in payload.answers])
    except InputValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _predict(request, payload.age, payload.sex, tokens, payload.top_k)


@app.post("/api/v1/predictions/raw", response_model=PredictionResponse, tags=["Predictions"])
def raw_prediction(request: Request, payload: RawPredictionRequest) -> dict[str, object]:
    return _predict(request, payload.age, payload.sex, payload.evidences, payload.top_k)
