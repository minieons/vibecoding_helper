"""vibe plan 명령어 - 기획 단계."""

import re
from pathlib import Path

import typer

from vibe.cli.ui.console import console
from vibe.cli.ui.display import print_error, print_info, print_warning
from vibe.cli.ui.progress import spinner
from vibe.cli.ui.prompts import confirm, text_input


def plan(
    ctx: typer.Context,
    review: bool = typer.Option(
        False, "--review", "-r", help="기존 PRD 검토 및 수정 모드"
    ),
) -> None:
    """기획 단계 - PRD.md, USER_STORIES.md 생성."""
    import asyncio

    from vibe.core.config import load_config
    from vibe.core.exceptions import PhaseError, VibeError
    from vibe.core.state import PhaseStatus, load_state
    from vibe.handlers.file import write_file

    async def run_plan() -> None:
        try:
            # 설정 및 상태 로드
            config = load_config()
            state = load_state()

            # Phase 확인
            if state.current_phase < 1 and not state.is_phase_complete(0):
                raise PhaseError(
                    "먼저 'vibe init'으로 프로젝트를 초기화해주세요.",
                    code="E040"
                )

            console.print("\n[bold blue]📋 Phase 1: 기획[/bold blue]\n")

            # 리뷰 모드
            if review:
                await _review_existing_docs()
                return

            # 기존 문서 확인
            prd_path = Path.cwd() / "PRD.md"
            if prd_path.exists():
                print_warning("PRD.md가 이미 존재합니다.")
                if not confirm("새로 생성하시겠습니까?", default=False):
                    print_info("기존 문서를 유지합니다. --review 옵션으로 검토할 수 있습니다.")
                    raise typer.Exit(0)

            # 컨텍스트 로드
            context = _load_planning_context()
            console.print("[dim]로드된 컨텍스트: TECH_STACK.md, RULES.md[/dim]")

            # 추가 요구사항 입력
            console.print("\n[cyan]프로젝트에 대해 더 알려주세요 (선택사항):[/cyan]")
            additional_requirements = text_input(
                "핵심 기능이나 요구사항",
                default=""
            )

            # AI로 PRD, USER_STORIES 생성
            console.print("\n[bold]AI가 기획 문서를 생성합니다...[/bold]\n")

            prd_content, user_stories_content = await _generate_planning_docs(
                config=config,
                context=context,
                additional_requirements=additional_requirements,
            )

            # 파일 저장
            files_created = []

            with spinner("문서 저장 중..."):
                # PRD.md
                write_file(prd_path, prd_content)
                files_created.append("PRD.md")

                # USER_STORIES.md
                user_stories_path = Path.cwd() / "USER_STORIES.md"
                write_file(user_stories_path, user_stories_content)
                files_created.append("USER_STORIES.md")

            # 상태 업데이트
            if state.current_phase == 0:
                state.advance_phase()
            state.phase_status["1"] = PhaseStatus.COMPLETED
            state.save()

            # 결과 출력
            console.print("\n[bold green]✓ 기획 완료![/bold green]\n")

            console.print("[bold]생성된 문서:[/bold]")
            for f in files_created:
                console.print(f"  • {f}")

            console.print("\n[bold]다음 단계:[/bold]")
            console.print("  1. PRD.md와 USER_STORIES.md를 검토하세요")
            console.print("  2. [cyan]vibe design[/cyan]으로 설계 단계를 시작하세요")

        except VibeError as e:
            print_error(f"{e.message}")
            if e.code:
                console.print(f"[dim]에러 코드: {e.code}[/dim]")
            raise typer.Exit(1)

    asyncio.run(run_plan())


def _load_planning_context() -> str:
    """기획에 필요한 컨텍스트 로드."""
    from vibe.handlers.file import read_file

    context_parts = []

    # TECH_STACK.md
    tech_stack_path = Path.cwd() / "TECH_STACK.md"
    if tech_stack_path.exists():
        content = read_file(tech_stack_path)
        context_parts.append(f"## TECH_STACK.md\n{content}")

    # RULES.md
    rules_path = Path.cwd() / "RULES.md"
    if rules_path.exists():
        content = read_file(rules_path)
        context_parts.append(f"## RULES.md\n{content}")

    return "\n\n---\n\n".join(context_parts)


async def _review_existing_docs() -> None:
    """기존 문서 검토 모드."""
    from vibe.handlers.file import read_file

    prd_path = Path.cwd() / "PRD.md"
    user_stories_path = Path.cwd() / "USER_STORIES.md"

    if not prd_path.exists():
        print_error("PRD.md가 없습니다. 먼저 'vibe plan'을 실행하세요.")
        raise typer.Exit(1)

    console.print("\n[bold]현재 PRD 요약:[/bold]")

    prd_content = read_file(prd_path)
    # 첫 20줄만 표시
    lines = prd_content.split("\n")[:20]
    for line in lines:
        console.print(f"  {line}")

    if len(prd_content.split("\n")) > 20:
        console.print("  ...")

    console.print("\n[dim]전체 내용은 PRD.md 파일을 직접 확인하세요.[/dim]")


async def _generate_planning_docs(
    config,
    context: str,
    additional_requirements: str,
) -> tuple[str, str]:
    """AI를 사용하여 기획 문서 생성."""
    from vibe.core.context import Message
    from vibe.prompts.loader import load_phase_prompt

    # 프롬프트 로드
    try:
        phase_prompt = load_phase_prompt(1)
        phase_prompt = phase_prompt.format(context=context)
    except (FileNotFoundError, KeyError):
        phase_prompt = """기획 단계를 수행합니다.
PRD.md와 USER_STORIES.md를 생성해주세요."""

    user_message = f"""프로젝트 컨텍스트:
{context}

추가 요구사항: {additional_requirements or '없음'}

위 정보를 바탕으로 PRD.md와 USER_STORIES.md를 생성해주세요.

PRD.md에는:
- 프로젝트 개요
- 핵심 기능 목록
- 대상 사용자
- 성공 지표
- MVP 범위
- 제외 항목

USER_STORIES.md에는:
- Epic 별로 그룹화된 User Stories
- MoSCoW 우선순위 (Must/Should/Could/Won't)
- 각 스토리의 수용 기준

각 문서를 마크다운 코드 블록으로 제공해주세요:
```markdown:PRD.md
(내용)
```

```markdown:USER_STORIES.md
(내용)
```"""

    messages = [Message(role="user", content=user_message)]

    if config.dual_mode.enabled:
        # 듀얼 모드: Gemini(분석) + Claude(작성)
        from vibe.providers.orchestrator import create_orchestrator

        orchestrator = create_orchestrator(config.dual_mode)

        with spinner("Gemini가 컨텍스트를 분석하고 Claude가 문서를 작성 중..."):
            result = await orchestrator.execute_phase1_plan(
                messages=messages,
                system=phase_prompt,
                external_context=context,
            )
        response_content = result.content
    else:
        # 단일 모드
        from vibe.providers.factory import create_provider

        provider = create_provider(config.provider)
        with spinner("AI가 기획 문서를 생성 중..."):
            response = await provider.generate(
                messages=messages,
                system=phase_prompt,
                max_tokens=8192,
            )
        response_content = response.content

    # 응답에서 문서 추출
    prd = _extract_markdown_block(response_content, "PRD.md")
    user_stories = _extract_markdown_block(response_content, "USER_STORIES.md")

    # 기본값 제공
    if not prd:
        prd = _default_prd()

    if not user_stories:
        user_stories = _default_user_stories()

    return prd, user_stories


def _extract_markdown_block(content: str, filename: str) -> str:
    """마크다운 코드 블록에서 특정 파일 내용 추출."""
    # 패턴: ```markdown:FILENAME ... ```
    pattern = rf'```markdown:{re.escape(filename)}\s*\n(.*?)```'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        return match.group(1).strip()

    # 대안: ```FILENAME ... ``` 형식
    pattern2 = rf'```{re.escape(filename)}\s*\n(.*?)```'
    match2 = re.search(pattern2, content, re.DOTALL)

    if match2:
        return match2.group(1).strip()

    return ""


def _default_prd() -> str:
    """기본 PRD 내용."""
    return """# PRD (Product Requirements Document)

## 1. 개요
(프로젝트 설명)

## 2. 핵심 기능
- [ ] 기능 1
- [ ] 기능 2

## 3. 대상 사용자
- 주요 사용자 그룹

## 4. 성공 지표
- 지표 1
- 지표 2

## 5. MVP 범위
### 포함
- 기능 A

### 제외
- 기능 B (후속 버전)

## 6. 일정
- Phase 1: 기획
- Phase 2: 설계
- Phase 3: 구현
- Phase 4: 테스트
"""


def _default_user_stories() -> str:
    """기본 User Stories 내용."""
    return """# User Stories

## Epic 1: 핵심 기능

### US-001: 기본 기능
**우선순위**: Must
**역할**: 사용자로서
**목표**: 기본 기능을 사용하고 싶다
**이유**: 핵심 가치를 얻기 위해

**수용 기준**:
- [ ] 조건 1
- [ ] 조건 2

---

## 우선순위 요약

| ID | 제목 | 우선순위 |
|----|------|---------|
| US-001 | 기본 기능 | Must |
"""
