"""설정 로드/저장."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field

from vibe.core.exceptions import ConfigError

VIBE_DIR = ".vibe"
CONFIG_FILE = "config.yaml"


class DualModelConfig(BaseModel):
    """듀얼 모델 설정."""

    enabled: bool = True
    main_provider: Literal["anthropic", "openai"] = "anthropic"
    main_model: str = "claude-sonnet-4-20250514"
    knowledge_provider: Literal["google"] = "google"
    knowledge_model: str = "gemini-2.0-flash"


class VibeConfig(BaseModel):
    """프로젝트 설정."""

    project_name: str
    project_type: Literal["backend", "frontend", "fullstack", "cli", "library"] = (
        "backend"
    )

    # 듀얼 모델 설정
    dual_mode: DualModelConfig = Field(default_factory=DualModelConfig)

    # 레거시 호환 (단일 모델 모드)
    provider: Literal["anthropic", "google", "openai"] = "anthropic"
    model: Optional[str] = None

    auto_commit: bool = True
    language: Literal["ko", "en"] = "ko"
    token_budget: int = Field(default=100000, ge=1000, le=500000)

    model_config = ConfigDict(extra="forbid")

    def save(self, path: Optional[Path] = None) -> None:
        """설정 저장."""
        if path is None:
            path = Path.cwd() / VIBE_DIR / CONFIG_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(), f, allow_unicode=True, default_flow_style=False)


def load_config(path: Optional[Path] = None) -> VibeConfig:
    """설정 로드."""
    if path is None:
        path = Path.cwd() / VIBE_DIR / CONFIG_FILE

    if not path.exists():
        raise ConfigError(f"설정 파일을 찾을 수 없습니다: {path}", code="E001")

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return VibeConfig(**data)
    except Exception as e:
        raise ConfigError(f"설정 파일 파싱 오류: {e}", code="E002") from e


def get_api_key(provider: str) -> Optional[str]:
    """Provider별 API 키 가져오기."""
    env_map = {
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "openai": "OPENAI_API_KEY",
    }
    env_var = env_map.get(provider)
    return os.environ.get(env_var) if env_var else None
