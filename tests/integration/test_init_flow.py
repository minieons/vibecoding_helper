"""init 플로우 통합 테스트."""

from pathlib import Path

import pytest

from vibe.core.config import VibeConfig, load_config
from vibe.core.state import PhaseStatus, create_initial_state, load_state


class TestInitFlow:
    """init 명령어 플로우 테스트."""

    @pytest.fixture
    def project_dir(self, tmp_path: Path) -> Path:
        """프로젝트 디렉토리."""
        project = tmp_path / "new_project"
        project.mkdir()
        return project

    def test_create_project_structure(self, project_dir: Path, monkeypatch):
        """프로젝트 구조 생성."""
        monkeypatch.chdir(project_dir)

        # .vibe 디렉토리 생성
        vibe_dir = project_dir / ".vibe"
        vibe_dir.mkdir()

        # 설정 파일 생성
        config = VibeConfig(
            project_name="test-project",
            project_type="cli",
        )
        config.save()

        # 상태 파일 생성
        state = create_initial_state()
        state.save()

        # 검증
        assert (vibe_dir / "config.yaml").exists()
        assert (vibe_dir / "state.json").exists()

        loaded_config = load_config()
        assert loaded_config.project_name == "test-project"

        loaded_state = load_state()
        assert loaded_state.current_phase == 0

    def test_config_state_consistency(self, project_dir: Path, monkeypatch):
        """설정과 상태 일관성."""
        monkeypatch.chdir(project_dir)
        vibe_dir = project_dir / ".vibe"
        vibe_dir.mkdir()

        # 듀얼 모드 활성화 설정
        config = VibeConfig(
            project_name="dual-test",
        )
        config.dual_mode.enabled = True
        config.save()

        # 상태도 듀얼 모드로
        state = create_initial_state(dual_mode=True)
        state.save()

        loaded_config = load_config()
        loaded_state = load_state()

        assert loaded_config.dual_mode.enabled == loaded_state.dual_mode_active

    def test_phase_progression(self, project_dir: Path, monkeypatch):
        """Phase 진행 시뮬레이션."""
        monkeypatch.chdir(project_dir)
        vibe_dir = project_dir / ".vibe"
        vibe_dir.mkdir()

        config = VibeConfig(project_name="phase-test")
        config.save()

        state = create_initial_state()
        state.save()

        # Phase 0 -> 1
        state.advance_phase()
        state.save()

        loaded = load_state()
        assert loaded.current_phase == 1
        assert loaded.is_phase_complete(0) is True
        assert loaded.phase_status["1"] == PhaseStatus.IN_PROGRESS

    def test_multiple_save_load_cycles(self, project_dir: Path, monkeypatch):
        """여러 번 저장/로드 사이클."""
        monkeypatch.chdir(project_dir)
        vibe_dir = project_dir / ".vibe"
        vibe_dir.mkdir()

        # 첫 번째 저장
        config = VibeConfig(project_name="cycle-test", language="ko")
        config.save()

        # 로드 후 수정
        loaded = load_config()
        assert loaded.language == "ko"

        # 새 설정으로 덮어쓰기
        new_config = VibeConfig(project_name="cycle-test", language="en")
        new_config.save()

        # 다시 로드
        reloaded = load_config()
        assert reloaded.language == "en"


class TestDocumentGeneration:
    """문서 생성 플로우 테스트."""

    @pytest.fixture
    def initialized_project(self, tmp_path: Path, monkeypatch) -> Path:
        """초기화된 프로젝트."""
        project = tmp_path / "init_project"
        project.mkdir()
        monkeypatch.chdir(project)

        vibe_dir = project / ".vibe"
        vibe_dir.mkdir()

        config = VibeConfig(project_name="doc-test")
        config.save()

        state = create_initial_state()
        state.save()

        return project

    def test_tech_stack_creation(self, initialized_project: Path):
        """TECH_STACK.md 생성 시뮬레이션."""
        tech_stack = initialized_project / "TECH_STACK.md"
        tech_stack.write_text(
            """# Tech Stack

## Language
- Python 3.11

## Framework
- Typer
""",
            encoding="utf-8",
        )

        assert tech_stack.exists()
        content = tech_stack.read_text(encoding="utf-8")
        assert "Python" in content

    def test_rules_creation(self, initialized_project: Path):
        """RULES.md 생성 시뮬레이션."""
        rules = initialized_project / "RULES.md"
        rules.write_text(
            """# Coding Rules

## Style
- Use type hints
- Follow PEP 8
""",
            encoding="utf-8",
        )

        assert rules.exists()
        content = rules.read_text(encoding="utf-8")
        assert "type hints" in content

    def test_full_init_artifacts(self, initialized_project: Path):
        """Phase 0 완료 후 산출물."""
        # Phase 0 산출물 생성
        (initialized_project / "TECH_STACK.md").write_text("# Tech Stack", encoding="utf-8")
        (initialized_project / "RULES.md").write_text("# Rules", encoding="utf-8")

        # 상태 업데이트
        state = load_state()
        state.advance_phase()  # Phase 0 -> 1
        state.save()

        # 검증
        assert (initialized_project / "TECH_STACK.md").exists()
        assert (initialized_project / "RULES.md").exists()
        assert load_state().current_phase == 1


class TestErrorHandling:
    """에러 처리 테스트."""

    def test_uninitialized_project(self, tmp_path: Path, monkeypatch):
        """초기화되지 않은 프로젝트."""
        monkeypatch.chdir(tmp_path)

        from vibe.core.exceptions import ConfigError, StateError

        with pytest.raises(ConfigError):
            load_config()

        with pytest.raises(StateError):
            load_state()

    def test_corrupted_config(self, tmp_path: Path, monkeypatch):
        """손상된 설정 파일."""
        monkeypatch.chdir(tmp_path)
        vibe_dir = tmp_path / ".vibe"
        vibe_dir.mkdir()

        config_file = vibe_dir / "config.yaml"
        config_file.write_text("invalid: [yaml: content", encoding="utf-8")

        from vibe.core.exceptions import ConfigError

        with pytest.raises(ConfigError):
            load_config()

    def test_corrupted_state(self, tmp_path: Path, monkeypatch):
        """손상된 상태 파일."""
        monkeypatch.chdir(tmp_path)
        vibe_dir = tmp_path / ".vibe"
        vibe_dir.mkdir()

        state_file = vibe_dir / "state.json"
        state_file.write_text("{not valid json", encoding="utf-8")

        from vibe.core.exceptions import StateError

        with pytest.raises(StateError):
            load_state()
