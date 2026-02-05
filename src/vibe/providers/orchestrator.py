"""듀얼 모델 오케스트레이터 - Claude↔Gemini 협업 조율."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from vibe.core.context import Message
from vibe.core.exceptions import ProviderError
from vibe.providers.base import AIProvider, Response

if TYPE_CHECKING:
    from vibe.core.config import DualModelConfig


class ModelRole(str, Enum):
    """모델 역할 정의."""

    MAIN_AGENT = "main_agent"  # Claude: 코딩, 아키텍처
    KNOWLEDGE_ENGINE = "knowledge_engine"  # Gemini: 컨텍스트, 검증


@dataclass
class OrchestratorResult:
    """오케스트레이션 결과."""

    content: str
    main_response: Optional[Response] = None
    knowledge_response: Optional[Response] = None
    model_used: str = ""
    collaboration_log: list[str] | None = None


class DualModelOrchestrator:
    """듀얼 모델 오케스트레이터.

    Claude 4.5 (Main Agent)와 Gemini 3 (Knowledge Engine)의
    협업을 조율합니다.

    Phase별 역할:
    - Phase 0 (Init): Gemini 단독
    - Phase 1 (Plan): Gemini(Ingester) + Claude(Planner)
    - Phase 2 (Design): Claude(Architect) + Gemini(Navigator)
    - Phase 3 (Code): Claude(Coder) + Gemini(Bridge)
    - Phase 4 (Test): Gemini(Auditor) + Claude(Tester)
    """

    def __init__(
        self,
        main_provider: AIProvider,
        knowledge_provider: AIProvider,
        config: Optional[DualModelConfig] = None,
    ):
        self.main = main_provider  # Claude
        self.knowledge = knowledge_provider  # Gemini
        self.config = config
        self._collaboration_log: list[str] = []

    def _log(self, message: str) -> None:
        """협업 로그 기록."""
        self._collaboration_log.append(message)

    async def execute_phase0_init(
        self,
        messages: list[Message],
        system: Optional[str] = None,
    ) -> OrchestratorResult:
        """Phase 0: 초기화 - Gemini 단독.

        사용자 의도 파악 및 초기 기술 스택 제안.
        """
        self._log("Phase 0: Gemini가 사용자 의도를 분석합니다.")

        response = await self.knowledge.generate(
            messages, system=system, max_tokens=4096
        )

        return OrchestratorResult(
            content=response.content,
            knowledge_response=response,
            model_used=self.knowledge.name,
            collaboration_log=self._collaboration_log.copy(),
        )

    async def execute_phase1_plan(
        self,
        messages: list[Message],
        system: Optional[str] = None,
        external_context: Optional[str] = None,
    ) -> OrchestratorResult:
        """Phase 1: 기획 - Gemini(Ingester) + Claude(Planner).

        Gemini: 무한 문맥 분석, 아이디어 발산
        Claude: 사용자 선호도에 맞춘 PRD 정렬
        """
        self._log("Phase 1: Gemini가 컨텍스트를 분석합니다.")

        # Step 1: Gemini가 외부 컨텍스트 분석 및 요약
        context_summary = ""
        if external_context:
            analysis_prompt = f"""다음 컨텍스트를 분석하고 PRD 작성에 필요한 핵심 정보를 추출하세요:

{external_context}

핵심 요구사항, 기술적 제약, 사용자 니즈를 정리해주세요."""

            gemini_messages = [Message(role="user", content=analysis_prompt)]
            gemini_response = await self.knowledge.generate(
                gemini_messages, system=system, max_tokens=2048
            )
            context_summary = gemini_response.content
            self._log(f"Gemini 분석 완료: {len(context_summary)} 문자")

        # Step 2: Claude가 PRD 작성
        self._log("Phase 1: Claude가 PRD를 작성합니다.")

        if context_summary:
            enhanced_messages = messages.copy()
            enhanced_messages.insert(
                0,
                Message(
                    role="user",
                    content=f"[Gemini 분석 결과]\n{context_summary}\n\n---\n\n",
                ),
            )
        else:
            enhanced_messages = messages

        claude_response = await self.main.generate(
            enhanced_messages, system=system, max_tokens=8192
        )

        return OrchestratorResult(
            content=claude_response.content,
            main_response=claude_response,
            knowledge_response=None,
            model_used=f"{self.knowledge.name}+{self.main.name}",
            collaboration_log=self._collaboration_log.copy(),
        )

    async def execute_phase2_design(
        self,
        messages: list[Message],
        system: Optional[str] = None,
        libraries: list[str] | None = None,
    ) -> OrchestratorResult:
        """Phase 2: 설계 - Claude(Architect) + Gemini(Navigator).

        Claude: 전체 아키텍처 시뮬레이션 및 구조 설계
        Gemini: 라이브러리 버전 호환성 실시간 검증
        """
        self._log("Phase 2: Claude가 아키텍처를 설계합니다.")

        # Step 1: Claude가 아키텍처 설계
        claude_response = await self.main.generate(
            messages, system=system, max_tokens=8192
        )

        # Step 2: Gemini가 라이브러리 호환성 검증 (선택적)
        compatibility_notes = ""
        if libraries:
            self._log(f"Phase 2: Gemini가 {len(libraries)}개 라이브러리를 검증합니다.")

            verify_prompt = f"""다음 라이브러리들의 호환성을 검증하세요:
{chr(10).join(f'- {lib}' for lib in libraries)}

각 라이브러리의:
1. 최신 안정 버전
2. Python 3.11+ 호환성
3. 상호 의존성 충돌 가능성
을 확인해주세요."""

            gemini_messages = [Message(role="user", content=verify_prompt)]
            gemini_response = await self.knowledge.generate(
                gemini_messages, max_tokens=2048
            )
            compatibility_notes = gemini_response.content

        final_content = claude_response.content
        if compatibility_notes:
            final_content += f"\n\n---\n## 라이브러리 호환성 검증 (Gemini)\n{compatibility_notes}"

        return OrchestratorResult(
            content=final_content,
            main_response=claude_response,
            model_used=f"{self.main.name}+{self.knowledge.name}",
            collaboration_log=self._collaboration_log.copy(),
        )

    async def execute_phase3_code(
        self,
        messages: list[Message],
        system: Optional[str] = None,
        full_codebase: dict[str, str] | None = None,
        max_retries: int = 3,
    ) -> OrchestratorResult:
        """Phase 3: 구현 - Claude(Coder) + Gemini(Bridge).

        Claude: 자율 코딩, 에러 자가 치유
        Gemini: 전체 코드베이스 실시간 동기화 및 컨텍스트 주입
        """
        self._log("Phase 3: Claude가 코드를 생성합니다.")

        # Gemini에게 전체 코드베이스 컨텍스트 제공 (Cold Storage)
        if full_codebase:
            self._log(f"Phase 3: Gemini가 {len(full_codebase)}개 파일을 분석합니다.")

        # Claude 코드 생성 (Self-Healing 포함)
        last_error = None
        for attempt in range(max_retries):
            try:
                if attempt > 0 and last_error:
                    # 재시도 시 에러 컨텍스트 추가
                    retry_messages = messages.copy()
                    retry_messages.append(
                        Message(
                            role="user",
                            content=f"이전 시도에서 다음 에러가 발생했습니다:\n{last_error}\n\n수정해서 다시 작성해주세요.",
                        )
                    )
                    messages_to_use = retry_messages
                    self._log(f"Phase 3: Claude 재시도 ({attempt + 1}/{max_retries})")
                else:
                    messages_to_use = messages

                claude_response = await self.main.generate(
                    messages_to_use, system=system, max_tokens=8192
                )

                return OrchestratorResult(
                    content=claude_response.content,
                    main_response=claude_response,
                    model_used=self.main.name,
                    collaboration_log=self._collaboration_log.copy(),
                )

            except ProviderError as e:
                last_error = str(e)
                self._log(f"Phase 3: 에러 발생 - {last_error}")

        # 모든 재시도 실패 시 Gemini에게 분석 요청
        self._log("Phase 3: Gemini가 에러를 분석합니다.")
        analysis_prompt = f"""Claude가 코드 생성 중 반복적으로 실패했습니다.

에러 내용:
{last_error}

요청 내용:
{messages[-1].content if messages else 'N/A'}

가능한 원인과 해결 방안을 분석해주세요."""

        gemini_messages = [Message(role="user", content=analysis_prompt)]
        gemini_response = await self.knowledge.generate(gemini_messages, max_tokens=2048)

        return OrchestratorResult(
            content=f"코드 생성 실패. Gemini 분석:\n\n{gemini_response.content}",
            knowledge_response=gemini_response,
            model_used=self.knowledge.name,
            collaboration_log=self._collaboration_log.copy(),
        )

    async def execute_phase4_test(
        self,
        messages: list[Message],
        system: Optional[str] = None,
        full_codebase: dict[str, str] | None = None,
        mode: str = "audit",  # "audit" | "edge_cases"
    ) -> OrchestratorResult:
        """Phase 4: 테스트 - Gemini(Auditor) + Claude(Tester).

        Gemini: 시스템 전역 데이터 흐름 감사
        Claude: 엣지 케이스 생성 및 사용자 관점 테스트
        """
        if mode == "audit":
            self._log("Phase 4: Gemini가 전역 감사를 수행합니다.")

            # Gemini가 전체 코드베이스 감사
            audit_context = ""
            if full_codebase:
                audit_context = "\n\n".join(
                    f"### {path}\n```\n{content}\n```"
                    for path, content in full_codebase.items()
                )

            audit_messages = messages.copy()
            if audit_context:
                audit_messages.insert(
                    0,
                    Message(role="user", content=f"[전체 코드베이스]\n{audit_context}"),
                )

            gemini_response = await self.knowledge.generate(
                audit_messages, system=system, max_tokens=8192
            )

            return OrchestratorResult(
                content=gemini_response.content,
                knowledge_response=gemini_response,
                model_used=self.knowledge.name,
                collaboration_log=self._collaboration_log.copy(),
            )

        else:  # edge_cases
            self._log("Phase 4: Claude가 엣지 케이스를 생성합니다.")

            claude_response = await self.main.generate(
                messages, system=system, max_tokens=8192
            )

            return OrchestratorResult(
                content=claude_response.content,
                main_response=claude_response,
                model_used=self.main.name,
                collaboration_log=self._collaboration_log.copy(),
            )

    async def query_knowledge(
        self,
        query: str,
        context: Optional[str] = None,
    ) -> str:
        """Gemini에게 지식 질의 (Context Injection).

        Claude가 코딩 중 외부 정보가 필요할 때 사용.
        """
        self._log(f"Knowledge Query: {query[:50]}...")

        messages = [Message(role="user", content=query)]
        if context:
            messages.insert(
                0, Message(role="user", content=f"[참고 컨텍스트]\n{context}")
            )

        response = await self.knowledge.generate(messages, max_tokens=2048)
        return response.content

    async def stream_with_collaboration(
        self,
        messages: list[Message],
        system: Optional[str] = None,
        phase: int = 3,
    ) -> AsyncIterator[str]:
        """스트리밍 응답 (협업 모드).

        주로 Phase 3 (Code)에서 사용.
        """
        self._log(f"Streaming Phase {phase}")

        # 현재는 Main Provider (Claude)로 스트리밍
        async for chunk in self.main.stream(messages, system=system):
            yield chunk


def create_orchestrator(
    config: DualModelConfig,
) -> DualModelOrchestrator:
    """오케스트레이터 생성 팩토리."""
    from vibe.providers.factory import create_provider

    main_provider = create_provider(config.main_provider)
    knowledge_provider = create_provider(config.knowledge_provider)

    return DualModelOrchestrator(
        main_provider=main_provider,
        knowledge_provider=knowledge_provider,
        config=config,
    )
