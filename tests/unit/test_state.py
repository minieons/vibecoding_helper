"""state 모듈 테스트."""

from datetime import datetime
from pathlib import Path

import pytest

from vibe.core.exceptions import StateError
from vibe.core.state import (
    LastAction,
    PhaseStatus,
    VibeState,
    create_initial_state,
    load_state,
)


class TestPhaseStatus:
    """PhaseStatus 열거형 테스트."""

    def test_values(self):
        """값 검증."""
        assert PhaseStatus.PENDING.value == "pending"
        assert PhaseStatus.IN_PROGRESS.value == "in_progress"
        assert PhaseStatus.COMPLETED.value == "completed"


class TestLastAction:
    """LastAction 모델 테스트."""

    def test_create(self):
        """생성 테스트."""
        action = LastAction(
            command="vibe init",
            timestamp=datetime.now(),
            files_created=["TECH_STACK.md"],
            files_modified=["README.md"],
            git_commit="abc123",
        )
        assert action.command == "vibe init"
        assert len(action.files_created) == 1
        assert action.git_commit == "abc123"

    def test_defaults(self):
        """기본값 테스트."""
        action = LastAction(command="test", timestamp=datetime.now())
        assert action.files_created == []
        assert action.files_modified == []
        assert action.git_commit is None


class TestVibeState:
    """VibeState 모델 테스트."""

    def test_create(self):
        """생성 테스트."""
        state = VibeState(
            current_phase=0,
            phase_status={"0": PhaseStatus.IN_PROGRESS},
            created_at=datetime.now(),
        )
        assert state.current_phase == 0
        assert state.git_enabled is False
        assert state.dual_mode_active is True

    def test_phase_range_validation(self):
        """Phase 범위 검증."""
        # 유효한 범위
        for phase in range(5):
            state = VibeState(
                current_phase=phase,
                phase_status={str(phase): PhaseStatus.IN_PROGRESS},
                created_at=datetime.now(),
            )
            assert state.current_phase == phase

        # 범위 초과
        with pytest.raises(ValueError):
            VibeState(
                current_phase=5,
                phase_status={"5": PhaseStatus.IN_PROGRESS},
                created_at=datetime.now(),
            )

        with pytest.raises(ValueError):
            VibeState(
                current_phase=-1,
                phase_status={"-1": PhaseStatus.IN_PROGRESS},
                created_at=datetime.now(),
            )

    def test_advance_phase(self):
        """Phase 진행 테스트."""
        state = create_initial_state()
        assert state.current_phase == 0
        assert state.phase_status["0"] == PhaseStatus.IN_PROGRESS

        state.advance_phase()
        assert state.current_phase == 1
        assert state.phase_status["0"] == PhaseStatus.COMPLETED
        assert state.phase_status["1"] == PhaseStatus.IN_PROGRESS

        # 마지막 Phase까지 진행
        for _ in range(3):
            state.advance_phase()
        assert state.current_phase == 4

        # 더 이상 진행 불가
        state.advance_phase()
        assert state.current_phase == 4  # 변화 없음

    def test_is_phase_complete(self):
        """Phase 완료 여부 테스트."""
        state = create_initial_state()
        assert state.is_phase_complete(0) is False

        state.advance_phase()
        assert state.is_phase_complete(0) is True
        assert state.is_phase_complete(1) is False

    def test_save_and_load(self, temp_project: Path, vibe_dir: Path, monkeypatch):
        """저장 및 로드 테스트."""
        monkeypatch.chdir(temp_project)

        state = create_initial_state()
        state.git_enabled = True
        state.save()

        loaded = load_state()
        assert loaded.current_phase == 0
        assert loaded.git_enabled is True
        assert loaded.dual_mode_active is True


class TestCreateInitialState:
    """create_initial_state 함수 테스트."""

    def test_default(self):
        """기본 초기 상태."""
        state = create_initial_state()
        assert state.current_phase == 0
        assert state.phase_status["0"] == PhaseStatus.IN_PROGRESS
        assert state.phase_status["1"] == PhaseStatus.PENDING
        assert state.dual_mode_active is True

    def test_dual_mode_disabled(self):
        """듀얼 모드 비활성화."""
        state = create_initial_state(dual_mode=False)
        assert state.dual_mode_active is False


class TestLoadState:
    """load_state 함수 테스트."""

    def test_not_found(self, temp_project: Path, monkeypatch):
        """상태 파일 없음 테스트."""
        monkeypatch.chdir(temp_project)
        with pytest.raises(StateError) as exc_info:
            load_state()
        assert exc_info.value.code == "E003"

    def test_invalid_json(self, vibe_dir: Path, temp_project: Path, monkeypatch):
        """잘못된 JSON 파싱 오류 테스트."""
        monkeypatch.chdir(temp_project)
        state_file = vibe_dir / "state.json"
        state_file.write_text("{invalid json", encoding="utf-8")

        with pytest.raises(StateError) as exc_info:
            load_state()
        assert exc_info.value.code == "E003"
