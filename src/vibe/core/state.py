"""상태 관리 (.vibe/state.json)."""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from vibe.core.exceptions import StateError

VIBE_DIR = ".vibe"
STATE_FILE = "state.json"


class PhaseStatus(str, Enum):
    """Phase 상태."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class LastAction(BaseModel):
    """마지막 작업 정보."""

    command: str
    timestamp: datetime
    files_created: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    git_commit: Optional[str] = None


class VibeState(BaseModel):
    """프로젝트 상태."""

    current_phase: int = Field(ge=0, le=4)  # Phase 0-4 (Test 포함)
    phase_status: dict[str, PhaseStatus]
    last_action: Optional[LastAction] = None
    git_enabled: bool = False
    dual_mode_active: bool = True  # 듀얼 모델 활성화 여부
    created_at: datetime
    updated_at: datetime = Field(default_factory=datetime.now)

    def save(self, path: Optional[Path] = None) -> None:
        """상태 저장."""
        if path is None:
            path = Path.cwd() / VIBE_DIR / STATE_FILE
        path.parent.mkdir(parents=True, exist_ok=True)

        self.updated_at = datetime.now()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

    def advance_phase(self) -> None:
        """다음 Phase로 진행."""
        if self.current_phase < 4:
            self.phase_status[str(self.current_phase)] = PhaseStatus.COMPLETED
            self.current_phase += 1
            self.phase_status[str(self.current_phase)] = PhaseStatus.IN_PROGRESS

    def is_phase_complete(self, phase: int) -> bool:
        """Phase 완료 여부 확인."""
        return self.phase_status.get(str(phase)) == PhaseStatus.COMPLETED


def load_state(path: Optional[Path] = None) -> VibeState:
    """상태 로드."""
    if path is None:
        path = Path.cwd() / VIBE_DIR / STATE_FILE

    if not path.exists():
        raise StateError(f"상태 파일을 찾을 수 없습니다: {path}", code="E003")

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return VibeState(**data)
    except Exception as e:
        raise StateError(f"상태 파일 파싱 오류: {e}", code="E003") from e


def create_initial_state(dual_mode: bool = True) -> VibeState:
    """초기 상태 생성."""
    return VibeState(
        current_phase=0,
        phase_status={
            "0": PhaseStatus.IN_PROGRESS,
            "1": PhaseStatus.PENDING,
            "2": PhaseStatus.PENDING,
            "3": PhaseStatus.PENDING,
            "4": PhaseStatus.PENDING,
        },
        dual_mode_active=dual_mode,
        created_at=datetime.now(),
    )
