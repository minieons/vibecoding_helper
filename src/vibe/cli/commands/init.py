"""vibe init 명령어 - 프로젝트 초기화."""

import re
from pathlib import Path
from typing import Optional

import typer

from vibe.cli.ui.console import console
from vibe.cli.ui.display import print_error, print_warning
from vibe.cli.ui.progress import spinner
from vibe.cli.ui.prompts import confirm, select, text_input


def init(
    ctx: typer.Context,
    description: Optional[str] = typer.Argument(
        None, help="프로젝트 설명 (없으면 대화형)"
    ),
    project_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="프로젝트 유형 [backend|frontend|cli|library]"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="기존 설정 덮어쓰기"
    ),
) -> None:
    """프로젝트 초기화 - TECH_STACK.md, RULES.md 생성."""
    import asyncio

    from vibe.core.config import VIBE_DIR, DualModelConfig, VibeConfig
    from vibe.core.exceptions import VibeError
    from vibe.core.state import create_initial_state
    from vibe.handlers.file import write_file

    vibe_path = Path.cwd() / VIBE_DIR

    # 기존 설정 확인
    if vibe_path.exists() and not force:
        print_warning("이미 초기화된 프로젝트입니다.")
        if not confirm("기존 설정을 덮어쓰시겠습니까?", default=False):
            raise typer.Exit(0)

    console.print("\n[bold blue]🚀 Vibe Coding Helper - 프로젝트 초기화[/bold blue]\n")

    # 프로젝트 설명 입력
    if not description:
        description = text_input(
            "[cyan]프로젝트를 설명해주세요[/cyan]",
            default="새로운 프로젝트"
        )

    # 프로젝트 이름 추출 (첫 단어 또는 전체)
    project_name = _extract_project_name(description)
    console.print(f"[dim]프로젝트 이름: {project_name}[/dim]")

    # 프로젝트 유형 선택
    if not project_type:
        project_type = select(
            "[cyan]프로젝트 유형을 선택하세요:[/cyan]",
            ["backend", "frontend", "fullstack", "cli", "library"],
            default="backend"
        )

    # 듀얼 모드 사용 여부
    use_dual_mode = confirm(
        "[cyan]듀얼 모델 모드를 사용하시겠습니까? (Claude + Gemini 협업)[/cyan]",
        default=True
    )

    async def run_init() -> None:
        try:
            # AI로 TECH_STACK.md, RULES.md 생성
            console.print("\n[bold]AI가 프로젝트 설정을 생성합니다...[/bold]\n")

            tech_stack_content, rules_content = await _generate_initial_docs(
                description=description,
                project_type=project_type,
                use_dual_mode=use_dual_mode,
            )

            # 파일 저장
            files_created = []

            with spinner("파일 생성 중..."):
                # TECH_STACK.md
                tech_stack_path = Path.cwd() / "TECH_STACK.md"
                write_file(tech_stack_path, tech_stack_content)
                files_created.append("TECH_STACK.md")

                # RULES.md
                rules_path = Path.cwd() / "RULES.md"
                write_file(rules_path, rules_content)
                files_created.append("RULES.md")

                # 설정 파일 생성
                config = VibeConfig(
                    project_name=project_name,
                    project_type=project_type,
                    dual_mode=DualModelConfig(enabled=use_dual_mode),
                )
                config.save()
                files_created.append(".vibe/config.yaml")

                # 상태 파일 생성
                state = create_initial_state(dual_mode=use_dual_mode)
                state.save()
                files_created.append(".vibe/state.json")

            # 결과 출력
            console.print("\n[bold green]✓ 초기화 완료![/bold green]\n")

            console.print("[bold]생성된 파일:[/bold]")
            for f in files_created:
                console.print(f"  • {f}")

            console.print("\n[bold]다음 단계:[/bold]")
            console.print("  1. TECH_STACK.md와 RULES.md를 검토하세요")
            console.print("  2. [cyan]vibe plan[/cyan]으로 기획 단계를 시작하세요")

            if use_dual_mode:
                console.print("\n[dim]듀얼 모드 활성화: Claude(Main) + Gemini(Knowledge)[/dim]")

        except VibeError as e:
            print_error(f"{e.message}")
            if e.code:
                console.print(f"[dim]에러 코드: {e.code}[/dim]")
            raise typer.Exit(1)

    asyncio.run(run_init())


def _extract_project_name(description: str) -> str:
    """프로젝트 설명에서 이름 추출."""
    # 첫 번째 의미있는 단어 추출
    words = description.strip().split()
    if not words:
        return "my_project"

    # 한글/영어 첫 단어
    first_word = words[0].lower()

    # 특수문자 제거
    clean_name = re.sub(r'[^a-z0-9가-힣_-]', '', first_word)

    if not clean_name:
        return "my_project"

    return clean_name[:30]  # 최대 30자


async def _generate_initial_docs(
    description: str,
    project_type: str,
    use_dual_mode: bool,
) -> tuple[str, str]:
    """AI를 사용하여 초기 문서 생성."""
    from vibe.core.context import Message
    from vibe.prompts.loader import load_phase_prompt

    # 프롬프트 로드
    try:
        phase_prompt = load_phase_prompt(0)
    except FileNotFoundError:
        phase_prompt = """프로젝트 초기화를 수행합니다.
TECH_STACK.md와 RULES.md를 생성해주세요."""

    user_message = f"""프로젝트 설명: {description}
프로젝트 유형: {project_type}

위 정보를 바탕으로 TECH_STACK.md와 RULES.md를 생성해주세요.

TECH_STACK.md에는:
- 권장 기술 스택 (언어, 프레임워크, 라이브러리)
- 개발 도구 (패키지 매니저, 린터 등)
- 테스트 도구

RULES.md에는:
- 코딩 컨벤션
- 네이밍 규칙
- 파일 구조 규칙
- 에러 처리 패턴

각 문서를 마크다운 코드 블록으로 제공해주세요:
```markdown:TECH_STACK.md
(내용)
```

```markdown:RULES.md
(내용)
```"""

    messages = [Message(role="user", content=user_message)]

    if use_dual_mode:
        # 듀얼 모드: Gemini 사용 (Phase 0은 Gemini 단독)
        from vibe.core.config import DualModelConfig
        from vibe.providers.orchestrator import create_orchestrator

        config = DualModelConfig(enabled=True)
        orchestrator = create_orchestrator(config)

        with spinner("Gemini가 프로젝트를 분석 중..."):
            result = await orchestrator.execute_phase0_init(
                messages=messages,
                system=phase_prompt,
            )
        response_content = result.content
    else:
        # 단일 모드: 기본 Provider 사용
        from vibe.providers.factory import create_provider

        provider = create_provider("anthropic")
        with spinner("AI가 프로젝트를 분석 중..."):
            response = await provider.generate(
                messages=messages,
                system=phase_prompt,
                max_tokens=4096,
            )
        response_content = response.content

    # 응답에서 문서 추출
    tech_stack = _extract_markdown_block(response_content, "TECH_STACK.md")
    rules = _extract_markdown_block(response_content, "RULES.md")

    # 기본값 제공 (AI가 형식을 지키지 않은 경우)
    if not tech_stack:
        tech_stack = _default_tech_stack(project_type)

    if not rules:
        rules = _default_rules()

    return tech_stack, rules


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


def _default_tech_stack(project_type: str) -> str:
    """기본 TECH_STACK.md 내용."""
    templates = {
        "backend": """# 기술 스택 (TECH_STACK.md)

## 언어
- Python 3.11+

## 프레임워크
- FastAPI (웹 API)
- Pydantic (데이터 검증)

## 데이터베이스
- PostgreSQL
- SQLAlchemy (ORM)

## 개발 도구
- uv (패키지 매니저)
- Ruff (린터/포매터)
- pytest (테스트)

## 기타
- Docker (컨테이너)
- GitHub Actions (CI/CD)
""",
        "frontend": """# 기술 스택 (TECH_STACK.md)

## 언어
- TypeScript 5.x

## 프레임워크
- React 18+ / Next.js 14+
- TailwindCSS

## 상태관리
- Zustand 또는 React Query

## 개발 도구
- pnpm (패키지 매니저)
- ESLint + Prettier
- Vitest (테스트)
""",
        "cli": """# 기술 스택 (TECH_STACK.md)

## 언어
- Python 3.11+

## 프레임워크
- Typer (CLI)
- Rich (터미널 UI)

## 개발 도구
- uv (패키지 매니저)
- Ruff (린터/포매터)
- pytest (테스트)
""",
        "library": """# 기술 스택 (TECH_STACK.md)

## 언어
- Python 3.11+

## 패키징
- pyproject.toml (PEP 621)
- Hatch 또는 uv

## 개발 도구
- Ruff (린터/포매터)
- pytest (테스트)
- mypy (타입 체크)
""",
    }
    return templates.get(project_type, templates["backend"])


def _default_rules() -> str:
    """기본 RULES.md 내용."""
    return """# 코딩 규칙 (RULES.md)

## 네이밍 컨벤션
- 클래스: PascalCase (예: `UserService`)
- 함수/변수: snake_case (예: `get_user_by_id`)
- 상수: UPPER_SNAKE_CASE (예: `MAX_RETRY_COUNT`)
- 프라이빗: 언더스코어 접두사 (예: `_internal_method`)

## 파일 구조
- 하나의 파일에 하나의 주요 클래스/기능
- 테스트 파일은 `test_` 접두사
- 유틸리티는 `utils/` 디렉토리

## 에러 처리
- 커스텀 예외 클래스 사용
- 에러 메시지는 사용자 친화적으로
- 로깅으로 디버그 정보 기록

## 문서화
- 모든 공개 함수에 docstring 작성
- 복잡한 로직에 인라인 주석

## 타입 힌트
- 모든 함수 시그니처에 타입 힌트 사용
- `from __future__ import annotations` 사용
"""
