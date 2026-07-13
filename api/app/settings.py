"""Runtime configuration for the Vitalyx API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Environment-derived settings with deployment-safe defaults."""

    port: int
    log_level: str
    artifacts_path: Path
    app_env: str
    cors_origins: tuple[str, ...]

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            port=int(os.getenv("PORT", "8000")),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            artifacts_path=Path(os.getenv("ARTIFACTS_PATH", "/app/vitalyx_artifacts")),
            app_env=os.getenv("APP_ENV", "production"),
            cors_origins=tuple(origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,https://vitalyx.eddux.dev").split(",") if origin.strip()),
        )
