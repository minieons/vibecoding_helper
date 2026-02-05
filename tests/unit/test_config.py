"""config 모듈 테스트."""

from pathlib import Path

import pytest

from vibe.core.config import (
    DualModelConfig,
    VibeConfig,
    get_api_key,
    load_config,
)
from vibe.core.exceptions import ConfigError


class TestDualModelConfig:
    """DualModelConfig 테스트."""

    def test_defaults(self):
        """기본값 테스트."""
        config = DualModelConfig()
        assert config.enabled is True
        assert config.main_provider == "anthropic"
        assert config.main_model == "claude-sonnet-4-20250514"
        assert config.knowledge_provider == "google"
        assert config.knowledge_model == "gemini-2.0-flash"

    def test_custom_values(self):
        """커스텀 값 테스트."""
        config = DualModelConfig(
            enabled=False,
            main_provider="openai",
            main_model="gpt-5",
        )
        assert config.enabled is False
        assert config.main_provider == "openai"
        assert config.main_model == "gpt-5"


class TestVibeConfig:
    """VibeConfig 테스트."""

    def test_defaults(self):
        """기본값 테스트."""
        config = VibeConfig(project_name="test")
        assert config.project_type == "backend"
        assert config.provider == "anthropic"
        assert config.auto_commit is True
        assert config.language == "ko"
        assert config.token_budget == 100000
        assert config.dual_mode.enabled is True

    def test_custom_values(self):
        """커스텀 값 테스트."""
        config = VibeConfig(
            project_name="my-app",
            project_type="cli",
            provider="google",
            auto_commit=False,
        )
        assert config.project_name == "my-app"
        assert config.project_type == "cli"
        assert config.provider == "google"
        assert config.auto_commit is False

    def test_token_budget_validation(self):
        """토큰 예산 범위 검증."""
        # 최소값
        config = VibeConfig(project_name="test", token_budget=1000)
        assert config.token_budget == 1000

        # 최대값
        config = VibeConfig(project_name="test", token_budget=500000)
        assert config.token_budget == 500000

        # 범위 초과
        with pytest.raises(ValueError):
            VibeConfig(project_name="test", token_budget=999)

        with pytest.raises(ValueError):
            VibeConfig(project_name="test", token_budget=500001)

    def test_project_types(self):
        """프로젝트 타입 검증."""
        valid_types = ["backend", "frontend", "fullstack", "cli", "library"]
        for ptype in valid_types:
            config = VibeConfig(project_name="test", project_type=ptype)
            assert config.project_type == ptype

    def test_save_and_load(self, temp_project: Path, vibe_dir: Path, monkeypatch):
        """저장 및 로드 테스트."""
        monkeypatch.chdir(temp_project)

        config = VibeConfig(
            project_name="save-test",
            project_type="frontend",
            language="en",
        )
        config.save()

        loaded = load_config()
        assert loaded.project_name == "save-test"
        assert loaded.project_type == "frontend"
        assert loaded.language == "en"


class TestLoadConfig:
    """load_config 함수 테스트."""

    def test_success(self, sample_config: Path, temp_project: Path, monkeypatch):
        """설정 로드 성공 테스트."""
        monkeypatch.chdir(temp_project)
        config = load_config()
        assert config.project_name == "test-project"
        assert config.project_type == "cli"

    def test_not_found(self, temp_project: Path, monkeypatch):
        """설정 파일 없음 테스트."""
        monkeypatch.chdir(temp_project)
        with pytest.raises(ConfigError) as exc_info:
            load_config()
        assert exc_info.value.code == "E001"

    def test_invalid_yaml(self, vibe_dir: Path, temp_project: Path, monkeypatch):
        """잘못된 YAML 파싱 오류 테스트."""
        monkeypatch.chdir(temp_project)
        config_file = vibe_dir / "config.yaml"
        config_file.write_text("invalid: yaml: content: [", encoding="utf-8")

        with pytest.raises(ConfigError) as exc_info:
            load_config()
        assert exc_info.value.code == "E002"


class TestGetApiKey:
    """get_api_key 함수 테스트."""

    def test_anthropic_key(self, monkeypatch):
        """Anthropic API 키 가져오기."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
        assert get_api_key("anthropic") == "test-anthropic-key"

    def test_google_key(self, monkeypatch):
        """Google API 키 가져오기."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
        assert get_api_key("google") == "test-google-key"

    def test_openai_key(self, monkeypatch):
        """OpenAI API 키 가져오기."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        assert get_api_key("openai") == "test-openai-key"

    def test_unknown_provider(self):
        """알 수 없는 Provider."""
        assert get_api_key("unknown") is None

    def test_missing_key(self, monkeypatch):
        """키가 설정되지 않은 경우."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        assert get_api_key("anthropic") is None
