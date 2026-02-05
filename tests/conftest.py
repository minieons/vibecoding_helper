"""pytest 공통 픽스처."""

from datetime import datetime
from pathlib import Path

import pytest


# ============================================================
# 디렉토리 픽스처
# ============================================================


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """임시 프로젝트 디렉토리."""
    project = tmp_path / "test_project"
    project.mkdir()
    return project


@pytest.fixture
def vibe_dir(temp_project: Path) -> Path:
    """.vibe 디렉토리."""
    vibe = temp_project / ".vibe"
    vibe.mkdir()
    return vibe


# ============================================================
# 설정 파일 픽스처
# ============================================================


@pytest.fixture
def sample_config(vibe_dir: Path) -> Path:
    """샘플 설정 파일."""
    config = vibe_dir / "config.yaml"
    config.write_text(
        """
project_name: test-project
project_type: cli
provider: anthropic
auto_commit: false
language: ko
token_budget: 50000
""",
        encoding="utf-8",
    )
    return config


@pytest.fixture
def sample_config_dual_mode(vibe_dir: Path) -> Path:
    """듀얼 모드 설정 파일."""
    config = vibe_dir / "config.yaml"
    config.write_text(
        """
project_name: dual-test
project_type: backend
dual_mode:
  enabled: true
  main_provider: anthropic
  main_model: claude-sonnet-4-20250514
  knowledge_provider: google
  knowledge_model: gemini-2.0-flash
provider: anthropic
language: ko
""",
        encoding="utf-8",
    )
    return config


# ============================================================
# 상태 파일 픽스처
# ============================================================


@pytest.fixture
def sample_state(vibe_dir: Path) -> Path:
    """샘플 상태 파일."""
    state = vibe_dir / "state.json"
    state.write_text(
        f"""{{
  "current_phase": 0,
  "phase_status": {{
    "0": "in_progress",
    "1": "pending",
    "2": "pending",
    "3": "pending",
    "4": "pending"
  }},
  "git_enabled": false,
  "dual_mode_active": true,
  "created_at": "{datetime.now().isoformat()}",
  "updated_at": "{datetime.now().isoformat()}"
}}""",
        encoding="utf-8",
    )
    return state


# ============================================================
# TODO 파일 픽스처
# ============================================================


@pytest.fixture
def sample_todo(temp_project: Path) -> Path:
    """샘플 TODO.md 파일."""
    todo = temp_project / "TODO.md"
    todo.write_text(
        """# TODO

## Phase 0
- [x] INIT-001: 프로젝트 초기화 (Must)
- [ ] INIT-002: 설정 파일 생성 (Should)

## Phase 1
- [ ] PLAN-001: PRD 작성 (Must)
- [ ] PLAN-002: User Story 작성 (Must)

## Phase 2
- [ ] DESIGN-001: TREE.md 작성 (Must)
""",
        encoding="utf-8",
    )
    return todo


# ============================================================
# TREE 파일 픽스처
# ============================================================


@pytest.fixture
def sample_tree(temp_project: Path) -> Path:
    """샘플 TREE.md 파일."""
    tree = temp_project / "TREE.md"
    tree.write_text(
        """# 프로젝트 구조

```
my_project/
├── src/
│   ├── __init__.py
│   ├── main.py
│   └── utils.py
├── tests/
│   └── test_main.py
├── pyproject.toml
└── README.md
```
""",
        encoding="utf-8",
    )
    return tree


# ============================================================
# 환경 변수 픽스처
# ============================================================


@pytest.fixture
def mock_api_keys(monkeypatch):
    """API 키 모킹."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")


@pytest.fixture
def no_api_keys(monkeypatch):
    """API 키 제거."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


# ============================================================
# 초기화된 프로젝트 픽스처
# ============================================================


@pytest.fixture
def initialized_project(temp_project: Path, sample_config: Path, sample_state: Path) -> Path:
    """완전히 초기화된 프로젝트."""
    # Phase 0 문서 생성
    (temp_project / "TECH_STACK.md").write_text("# Tech Stack\n", encoding="utf-8")
    (temp_project / "RULES.md").write_text("# Rules\n", encoding="utf-8")
    return temp_project
