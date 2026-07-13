"""Shared integration fixture loading only exported artifacts."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


os.environ["ARTIFACTS_PATH"] = str(Path(__file__).resolve().parents[1] / "vitalyx_artifacts")
os.environ["APP_ENV"] = "test"

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
