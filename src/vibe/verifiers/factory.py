"""검증기 팩토리."""

from __future__ import annotations

from pathlib import Path

from vibe.verifiers.base import (
    LanguageVerifier,
    NullVerifier,
    VerifyLevel,
    VerifyResult,
)
from vibe.verifiers.flutter import DartVerifier
from vibe.verifiers.java import JavaVerifier
from vibe.verifiers.python import PythonVerifier
from vibe.verifiers.typescript import JavaScriptVerifier, TypeScriptVerifier

# 확장자 -> 검증기 클래스 매핑
_VERIFIER_MAP: dict[str, type[LanguageVerifier]] = {
    # Python
    ".py": PythonVerifier,
    ".pyi": PythonVerifier,
    # TypeScript
    ".ts": TypeScriptVerifier,
    ".tsx": TypeScriptVerifier,
    # JavaScript
    ".js": JavaScriptVerifier,
    ".jsx": JavaScriptVerifier,
    ".mjs": JavaScriptVerifier,
    ".cjs": JavaScriptVerifier,
    # Java
    ".java": JavaVerifier,
    # Dart / Flutter
    ".dart": DartVerifier,
}

# 캐시된 검증기 인스턴스
_verifier_cache: dict[str, LanguageVerifier] = {}


def get_verifier(file_path: Path | str) -> LanguageVerifier:
    """파일 확장자에 맞는 검증기 반환.

    Args:
        file_path: 검증할 파일 경로

    Returns:
        해당 언어의 검증기 인스턴스
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    suffix = file_path.suffix.lower()

    # 캐시 확인
    if suffix in _verifier_cache:
        return _verifier_cache[suffix]

    # 검증기 클래스 찾기
    verifier_class = _VERIFIER_MAP.get(suffix, NullVerifier)

    # 인스턴스 생성 및 캐시
    verifier = verifier_class()
    _verifier_cache[suffix] = verifier

    return verifier


def verify_file(
    file_path: Path | str,
    level: VerifyLevel = VerifyLevel.ALL,
    fix: bool = False,
    skip_tests: bool = False,
) -> list[VerifyResult]:
    """파일 검증 실행.

    Args:
        file_path: 검증할 파일 경로
        level: 검증 레벨 (SYNTAX, TYPES, LINT, TEST, ALL)
        fix: 자동 수정 여부 (린트)
        skip_tests: 테스트 건너뛰기

    Returns:
        검증 결과 목록
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    if not file_path.exists():
        return [
            VerifyResult(
                success=False,
                check_type=VerifyLevel.SYNTAX,
                output=f"파일을 찾을 수 없습니다: {file_path}",
            )
        ]

    verifier = get_verifier(file_path)

    if level == VerifyLevel.ALL:
        return verifier.verify_all(file_path, fix=fix, skip_tests=skip_tests)
    elif level == VerifyLevel.SYNTAX:
        return [verifier.check_syntax(file_path)]
    elif level == VerifyLevel.TYPES:
        return [verifier.check_types(file_path)]
    elif level == VerifyLevel.LINT:
        return [verifier.check_lint(file_path, fix=fix)]
    elif level == VerifyLevel.TEST:
        return [verifier.run_tests(file_path)]
    else:
        return []


def get_supported_extensions() -> list[str]:
    """지원하는 파일 확장자 목록."""
    return list(_VERIFIER_MAP.keys())


def is_supported(file_path: Path | str) -> bool:
    """해당 파일이 검증 지원되는지 확인."""
    if isinstance(file_path, str):
        file_path = Path(file_path)

    return file_path.suffix.lower() in _VERIFIER_MAP


def register_verifier(extension: str, verifier_class: type[LanguageVerifier]) -> None:
    """새 검증기 등록.

    확장성을 위해 런타임에 검증기를 추가할 수 있습니다.

    Args:
        extension: 파일 확장자 (예: ".go")
        verifier_class: LanguageVerifier 서브클래스
    """
    _VERIFIER_MAP[extension.lower()] = verifier_class

    # 캐시 초기화
    if extension.lower() in _verifier_cache:
        del _verifier_cache[extension.lower()]
