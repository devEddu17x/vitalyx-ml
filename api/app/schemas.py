"""Pydantic DTOs exposed by the public HTTP contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ACADEMIC_NOTICE = (
    "Vitalyx was trained with synthetic patients for academic orientation only. "
    "It is not a medical diagnosis and must not drive automatic clinical decisions."
)


class BooleanAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence_id: str = Field(examples=["E_91"])
    present: bool | None = Field(default=None, description="Required for boolean evidence.")
    value: str | None = None
    values: list[str] | None = None


class FriendlyPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    age: float = Field(ge=0, description="Age validated again against the artifact range.", examples=[32])
    sex: str = Field(examples=["F"])
    answers: list[BooleanAnswer] = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=49)


class RawPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    age: float = Field(ge=0, examples=[32])
    sex: str = Field(examples=["F"])
    evidences: list[str] = Field(min_length=1, examples=[["E_91", "E_59_@_3"]])
    top_k: int = Field(default=5, ge=1, le=49)


class PredictionItem(BaseModel):
    rank: int
    pathology: str
    probability: float


class ConfidenceResponse(BaseModel):
    maximum_probability: float
    low_confidence: bool
    threshold: float


class PredictionResponse(BaseModel):
    predictions: list[PredictionItem]
    confidence: ConfidenceResponse
    input_summary: dict[str, int | float | str]
    model: dict[str, str]
    disclaimer: str = ACADEMIC_NOTICE


class EvidenceItem(BaseModel):
    id: str
    type: Literal["boolean", "single_choice", "multiple_choice"]
    question: str
    is_antecedent: bool
    default_values: list[str]
    allowed_values: list[str]


class EvidenceCatalogResponse(BaseModel):
    items: list[EvidenceItem]
    total: int


class PathologyItem(BaseModel):
    id: str
    name: str
    icd10_id: str | None = None


class PathologyCatalogResponse(BaseModel):
    items: list[PathologyItem]
    total: int
