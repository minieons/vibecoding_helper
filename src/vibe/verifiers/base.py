"""언어별 검증기 기본 클래스."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class VerifyLevel(str, Enum):
    """검증 레벨."""

    SYNTAX = "syntax"      # 문법 검사
    TYPES = "types"        # 타입 검사
    LINT = "lint"          # 린트 검사
    TEST = "test"          # 테스트 실행
    ALL = "all"            # 모든 검사


@dataclass
class VerifyIssue:
    """검증 이슈."""

    level: str              # error, warning, info
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    rule: Optional[str] = None  # 린트 규칙 ID

    def __str__(self) -> str:
        location = ""
        if self.file:
            location = f"{self.file}"
            if self.line:
                location += f":{self.line}"
                if self.column:
                    location += f":{self.column}"
            location += " - "

        rule_str = f" [{self.rule}]" if self.rule else ""
        return f"{location}{self.level.upper()}: {self.message}{rule_str}"


@dataclass
class VerifyResult:
    """검증 결과."""

    success: bool
    check_type: VerifyLevel
    issues: list[VerifyIssue] = field(default_factory=list)
    output: str = ""
    fix_applied: bool = False

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "warning")

    def __str__(self) -> str:
        status = "✓ PASS" if self.success else "✗ FAIL"
        return f"{self.check_type.value}: {status} ({self.error_count} errors, {self.warning_count} warnings)"


class LanguageVerifier(ABC):
    """언어별 검증기 추상 클래스.

    각 언어별로 이 클래스를 상속하여 구현합니다.
    """

    # 지원하는 파일 확장자
    extensions: list[str] = []

    # 언어 이름
    language: str = "unknown"

    @abstractmethod
    def check_syntax(self, file_path: Path) -> VerifyResult:
        """문법 검사.

        가장 기본적인 검사. 파일이 올바른 문법인지 확인.
        """
        ...

    @abstractmethod
    def check_types(self, file_path: Path) -> VerifyResult:
        """타입 검사.

        정적 타입 분석. Python의 mypy, TypeScript의 tsc 등.
        """
        ...

    @abstractmethod
    def check_lint(self, file_path: Path, fix: bool = False) -> VerifyResult:
        """린트 검사.

        코드 스타일 및 잠재적 버그 검사.
        fix=True면 자동 수정 시도.
        """
        ...

    @abstractmethod
    def run_tests(self, file_path: Path) -> VerifyResult:
        """관련 테스트 실행.

        파일과 관련된 테스트를 찾아 실행.
        """
        ...

    def verify_all(
        self,
        file_path: Path,
        fix: bool = False,
        skip_tests: bool = False,
    ) -> list[VerifyResult]:
        """모든 검증 실행."""
        results = []

        # 1. 문법 검사 (필수)
        syntax_result = self.check_syntax(file_path)
        results.append(syntax_result)

        # 문법 오류가 있으면 다음 단계 스킵
        if not syntax_result.success:
            return results

        # 2. 타입 검사
        type_result = self.check_types(file_path)
        results.append(type_result)

        # 3. 린트 검사
        lint_result = self.check_lint(file_path, fix=fix)
        results.append(lint_result)

        # 4. 테스트 (선택적)
        if not skip_tests:
            test_result = self.run_tests(file_path)
            results.append(test_result)

        return results

    def is_all_passed(self, results: list[VerifyResult]) -> bool:
        """모든 검증 통과 여부."""
        return all(r.success for r in results)

    def get_summary(self, results: list[VerifyResult]) -> str:
        """검증 결과 요약."""
        lines = [f"== {self.language} 검증 결과 =="]

        total_errors = 0
        total_warnings = 0

        for result in results:
            lines.append(str(result))
            total_errors += result.error_count
            total_warnings += result.warning_count

        lines.append("")
        lines.append(f"총 {total_errors} 에러, {total_warnings} 경고")

        return "\n".join(lines)


class NullVerifier(LanguageVerifier):
    """지원하지 않는 언어용 Null 검증기."""

    language = "unknown"
    extensions = []

    def check_syntax(self, file_path: Path) -> VerifyResult:
        return VerifyResult(
            success=True,
            check_type=VerifyLevel.SYNTAX,
            output="지원하지 않는 파일 형식입니다.",
        )

    def check_types(self, file_path: Path) -> VerifyResult:
        return VerifyResult(
            success=True,
            check_type=VerifyLevel.TYPES,
            output="지원하지 않는 파일 형식입니다.",
        )

    def check_lint(self, file_path: Path, fix: bool = False) -> VerifyResult:
        return VerifyResult(
            success=True,
            check_type=VerifyLevel.LINT,
            output="지원하지 않는 파일 형식입니다.",
        )

    def run_tests(self, file_path: Path) -> VerifyResult:
        return VerifyResult(
            success=True,
            check_type=VerifyLevel.TEST,
            output="지원하지 않는 파일 형식입니다.",
        )
