"""커스텀 예외 클래스."""

from typing import Optional


class VibeError(Exception):
    """Vibe 기본 예외 클래스."""

    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code
        super().__init__(message)


class ConfigError(VibeError):
    """설정 관련 에러."""

    pass


class StateError(VibeError):
    """상태 관련 에러."""

    pass


class ProviderError(VibeError):
    """AI Provider 에러."""

    pass


class FileError(VibeError):
    """파일 시스템 에러."""

    pass


class GitError(VibeError):
    """Git 관련 에러."""

    pass


class PhaseError(VibeError):
    """Phase 진행 에러."""

    pass
