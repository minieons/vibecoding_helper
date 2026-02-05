"""Phase별 워크플로우 오케스트레이션."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from vibe.core.context import Message, ProjectContext, load_project_context
from vibe.core.exceptions import PhaseError
from vibe.core.state import VibeState

if TYPE_CHECKING:
    from vibe.core.config import DualModelConfig
    from vibe.core.context import DualTrackContext
    from vibe.providers.base import AIProvider
    from vibe.verifiers.base import VerifyResult


PHASE_NAMES = {
    0: "초기화 (Initialization)",
    1: "기획 (Planning)",
    2: "설계 (Design)",
    3: "구현 (Implementation)",
    4: "테스트 (Test)",
}


@dataclass
class HealingResult:
    """Self-Healing 결과."""

    success: bool
    """수정 성공 여부."""

    attempts: int
    """시도 횟수."""

    original_errors: list[str] = field(default_factory=list)
    """원본 에러 목록."""

    remaining_errors: list[str] = field(default_factory=list)
    """수정 후 남은 에러 목록."""

    fixed_code: Optional[str] = None
    """수정된 코드."""


class SelfHealingWorkflow:
    """Self-Healing 워크플로우.

    코드 검증 실패 시 자동으로 AI에게 수정을 요청하고
    재검증하는 워크플로우입니다.

    Attributes:
        max_attempts: 최대 재시도 횟수 (기본: 2)
        on_attempt: 시도 시 콜백 (메시지 표시용)
        on_success: 성공 시 콜백
        on_failure: 실패 시 콜백
    """

    def __init__(
        self,
        dual_config: DualModelConfig,
        max_attempts: int = 2,
        on_attempt: Callable[[int, str], None] | None = None,
        on_success: Callable[[HealingResult], None] | None = None,
        on_failure: Callable[[HealingResult], None] | None = None,
    ):
        self.dual_config = dual_config
        self.max_attempts = max_attempts
        self.on_attempt = on_attempt
        self.on_success = on_success
        self.on_failure = on_failure

        self._orchestrator = None

    async def heal(
        self,
        file_path: Path,
        verify_results: list[VerifyResult],
        dual_ctx: DualTrackContext,
    ) -> HealingResult:
        """코드 수정 시도.

        Args:
            file_path: 수정할 파일 경로
            verify_results: 검증 결과
            dual_ctx: Dual-Track 컨텍스트

        Returns:
            HealingResult: 수정 결과
        """
        from vibe.handlers.file import read_file, write_file
        from vibe.verifiers import VerifyLevel, get_verifier, verify_file

        # 원본 에러 수집
        original_errors = self._collect_errors(verify_results)

        result = HealingResult(
            success=False,
            attempts=0,
            original_errors=original_errors,
        )

        # 파일 확장자로 언어 판단
        language = self._detect_language(file_path)

        for attempt in range(1, self.max_attempts + 1):
            result.attempts = attempt

            if self.on_attempt:
                self.on_attempt(attempt, f"Self-Healing 시도 {attempt}/{self.max_attempts}")

            # 현재 코드 읽기
            current_code = read_file(file_path)

            # AI에게 수정 요청
            fix_prompt = self._build_fix_prompt(
                code=current_code,
                errors=original_errors if attempt == 1 else result.remaining_errors,
                language=language,
            )

            fixed_code = await self._request_fix(fix_prompt, dual_ctx)

            if not fixed_code:
                continue

            # 수정된 코드 저장
            write_file(file_path, fixed_code)
            result.fixed_code = fixed_code

            # 재검증
            new_results = verify_file(file_path, level=VerifyLevel.SYNTAX)
            verifier = get_verifier(file_path)

            if verifier.is_all_passed(new_results):
                result.success = True
                result.remaining_errors = []

                if self.on_success:
                    self.on_success(result)

                return result
            else:
                # 남은 에러 수집
                result.remaining_errors = self._collect_errors(new_results)

        # 최대 시도 초과
        if self.on_failure:
            self.on_failure(result)

        return result

    async def _request_fix(
        self,
        prompt: str,
        dual_ctx: DualTrackContext,
    ) -> Optional[str]:
        """AI에게 수정 요청."""
        from vibe.providers.orchestrator import create_orchestrator

        if self._orchestrator is None:
            self._orchestrator = create_orchestrator(self.dual_config)

        messages = [Message(role="user", content=prompt)]

        try:
            result = await self._orchestrator.execute_phase3_code(
                messages=messages,
                full_codebase=dual_ctx.cold.full_codebase if dual_ctx.cold else None,
                max_retries=1,
            )
            return self._clean_code_output(result.content)
        except Exception:
            return None

    def _build_fix_prompt(
        self,
        code: str,
        errors: list[str],
        language: str,
    ) -> str:
        """수정 요청 프롬프트 생성."""
        error_list = "\n".join(f"- {e}" for e in errors[:10])

        return f"""다음 {language} 코드에 오류가 있습니다. 수정해주세요.

## 현재 코드
```{language.lower()}
{code}
```

## 발견된 오류
{error_list}

## 요청
1. 위 오류를 수정한 완전한 코드를 반환하세요.
2. 마크다운 코드 블록 없이 순수 {language} 코드만 반환하세요.
3. 기존 로직은 유지하면서 오류만 수정하세요.
4. 주석이나 설명 없이 코드만 반환하세요.
"""

    def _collect_errors(self, verify_results: list[VerifyResult]) -> list[str]:
        """검증 결과에서 에러 메시지 수집."""
        errors = []
        for result in verify_results:
            for issue in result.issues:
                if issue.line:
                    errors.append(f"Line {issue.line}: {issue.message}")
                else:
                    errors.append(issue.message)
        return errors

    def _detect_language(self, file_path: Path) -> str:
        """파일 확장자로 언어 감지."""
        suffix = file_path.suffix.lower()
        language_map = {
            ".py": "Python",
            ".pyi": "Python",
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".js": "JavaScript",
            ".jsx": "JavaScript",
            ".java": "Java",
            ".dart": "Dart",
        }
        return language_map.get(suffix, "code")

    def _clean_code_output(self, content: str) -> str:
        """AI 출력에서 순수 코드 추출."""
        # 마크다운 코드 블록 제거
        pattern = r'```(?:\w+)?\s*\n(.*?)```'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return content.strip()


async def verify_and_heal(
    file_path: Path,
    dual_config: DualModelConfig,
    dual_ctx: DualTrackContext,
    on_status: Callable[[str], None] | None = None,
) -> tuple[bool, Optional[HealingResult]]:
    """코드 검증 및 필요시 Self-Healing 실행.

    편의 함수로, 검증과 Self-Healing을 한 번에 처리합니다.

    Args:
        file_path: 검증할 파일 경로
        dual_config: 듀얼 모델 설정
        dual_ctx: Dual-Track 컨텍스트
        on_status: 상태 메시지 콜백

    Returns:
        (검증 통과 여부, HealingResult 또는 None)
    """
    from vibe.verifiers import VerifyLevel, get_verifier, verify_file
    from vibe.verifiers.factory import is_supported

    if not is_supported(file_path):
        return True, None

    if on_status:
        on_status("검증 중...")

    # 문법 검사
    results = verify_file(file_path, level=VerifyLevel.SYNTAX)
    verifier = get_verifier(file_path)

    if verifier.is_all_passed(results):
        if on_status:
            on_status("문법 검증 통과")

        # 린트 자동 수정
        lint_results = verify_file(file_path, level=VerifyLevel.LINT, fix=True)
        if lint_results and lint_results[0].fix_applied:
            if on_status:
                on_status("린트 자동 수정 적용")

        return True, None

    # Self-Healing 필요
    if on_status:
        on_status("문법 오류 발견 - Self-Healing 시작")

    healing = SelfHealingWorkflow(
        dual_config=dual_config,
        on_attempt=lambda n, msg: on_status(msg) if on_status else None,
    )

    healing_result = await healing.heal(file_path, results, dual_ctx)

    if healing_result.success:
        if on_status:
            on_status("Self-Healing 성공")
    else:
        if on_status:
            on_status("Self-Healing 실패 - 수동 수정 필요")

    return healing_result.success, healing_result


class WorkflowManager:
    """워크플로우 관리자."""

    def __init__(self, state: VibeState, provider: AIProvider):
        self.state = state
        self.provider = provider

    def can_proceed_to_phase(self, target_phase: int) -> bool:
        """특정 Phase로 진행 가능한지 확인."""
        if target_phase == 0:
            return True
        return self.state.is_phase_complete(target_phase - 1)

    def ensure_phase_ready(self, required_phase: int) -> None:
        """필요한 Phase가 완료되었는지 확인."""
        if required_phase > 0 and not self.state.is_phase_complete(required_phase - 1):
            prev_name = PHASE_NAMES.get(required_phase - 1, f"Phase {required_phase - 1}")
            raise PhaseError(
                f"'{prev_name}'이(가) 완료되지 않았습니다. 먼저 완료해주세요.",
                code="E040",
            )

    def get_context_for_phase(self, phase: int) -> ProjectContext:
        """Phase별 필요한 컨텍스트 로드."""
        ctx = load_project_context()

        # Phase별로 필요한 문서만 포함
        if phase == 0:
            # 초기화: 컨텍스트 없음
            return ProjectContext()
        elif phase == 1:
            # 기획: TECH_STACK, RULES
            return ProjectContext(
                tech_stack=ctx.tech_stack,
                rules=ctx.rules,
            )
        elif phase == 2:
            # 설계: TECH_STACK, RULES, PRD
            return ProjectContext(
                tech_stack=ctx.tech_stack,
                rules=ctx.rules,
                prd=ctx.prd,
            )
        elif phase == 3:
            # 구현: 전체
            return ctx

        return ctx
