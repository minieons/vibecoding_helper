"""vibe design 명령어 - 설계 단계."""

import re
from pathlib import Path

import typer

from vibe.cli.ui.console import console
from vibe.cli.ui.display import print_error, print_info, print_warning
from vibe.cli.ui.progress import spinner
from vibe.cli.ui.prompts import confirm


def design(
    ctx: typer.Context,
    skip_review: bool = typer.Option(
        False, "--skip-review", help="생성 후 검토 건너뛰기"
    ),
) -> None:
    """설계 단계 - TREE.md, SCHEMA.md 생성."""
    import asyncio

    from vibe.core.config import load_config
    from vibe.core.exceptions import PhaseError, VibeError
    from vibe.core.state import PhaseStatus, load_state
    from vibe.handlers.file import write_file

    async def run_design() -> None:
        try:
            # 설정 및 상태 로드
            config = load_config()
            state = load_state()

            # Phase 확인
            if not state.is_phase_complete(1):
                raise PhaseError(
                    "먼저 'vibe plan'으로 기획 단계를 완료해주세요.",
                    code="E040"
                )

            console.print("\n[bold blue]🏗️ Phase 2: 설계[/bold blue]\n")

            # 기존 문서 확인
            tree_path = Path.cwd() / "TREE.md"
            if tree_path.exists():
                print_warning("TREE.md가 이미 존재합니다.")
                if not confirm("새로 생성하시겠습니까?", default=False):
                    print_info("기존 문서를 유지합니다.")
                    raise typer.Exit(0)

            # 컨텍스트 로드
            context = _load_design_context()
            console.print("[dim]로드된 컨텍스트: TECH_STACK.md, RULES.md, PRD.md[/dim]")

            # 라이브러리 목록 추출 (Gemini 검증용)
            libraries = _extract_libraries_from_tech_stack()

            # AI로 TREE, SCHEMA 생성
            console.print("\n[bold]AI가 설계 문서를 생성합니다...[/bold]\n")

            tree_content, schema_content = await _generate_design_docs(
                config=config,
                context=context,
                libraries=libraries,
            )

            # 파일 저장
            files_created = []

            with spinner("문서 저장 중..."):
                # TREE.md
                write_file(tree_path, tree_content)
                files_created.append("TREE.md")

                # SCHEMA.md
                schema_path = Path.cwd() / "SCHEMA.md"
                write_file(schema_path, schema_content)
                files_created.append("SCHEMA.md")

            # 상태 업데이트
            if state.current_phase < 2:
                state.advance_phase()
            state.phase_status["2"] = PhaseStatus.COMPLETED
            state.save()

            # 결과 출력
            console.print("\n[bold green]✓ 설계 완료![/bold green]\n")

            console.print("[bold]생성된 문서:[/bold]")
            for f in files_created:
                console.print(f"  • {f}")

            # 검토
            if not skip_review:
                console.print("\n[bold]TREE.md 미리보기:[/bold]")
                _preview_tree(tree_content)

            console.print("\n[bold]다음 단계:[/bold]")
            console.print("  1. TREE.md와 SCHEMA.md를 검토하세요")
            console.print("  2. [cyan]vibe scaffold[/cyan]로 프로젝트 구조를 생성하세요")

        except VibeError as e:
            print_error(f"{e.message}")
            if e.code:
                console.print(f"[dim]에러 코드: {e.code}[/dim]")
            raise typer.Exit(1)

    asyncio.run(run_design())


def _load_design_context() -> str:
    """설계에 필요한 컨텍스트 로드."""
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

    # PRD.md
    prd_path = Path.cwd() / "PRD.md"
    if prd_path.exists():
        content = read_file(prd_path)
        context_parts.append(f"## PRD.md\n{content}")

    # USER_STORIES.md
    user_stories_path = Path.cwd() / "USER_STORIES.md"
    if user_stories_path.exists():
        content = read_file(user_stories_path)
        context_parts.append(f"## USER_STORIES.md\n{content}")

    return "\n\n---\n\n".join(context_parts)


def _extract_libraries_from_tech_stack() -> list[str]:
    """TECH_STACK.md에서 라이브러리 목록 추출."""
    from vibe.handlers.file import read_file

    tech_stack_path = Path.cwd() / "TECH_STACK.md"
    if not tech_stack_path.exists():
        return []

    content = read_file(tech_stack_path)
    libraries = []

    # 간단한 패턴: - 로 시작하는 라이브러리 이름
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            # "- FastAPI (웹 API)" -> "FastAPI"
            lib_name = line[2:].split("(")[0].split("-")[0].strip()
            if lib_name and not lib_name.startswith("#"):
                libraries.append(lib_name)

    return libraries[:10]  # 최대 10개


async def _generate_design_docs(
    config,
    context: str,
    libraries: list[str],
) -> tuple[str, str]:
    """AI를 사용하여 설계 문서 생성."""
    from vibe.core.context import Message
    from vibe.prompts.loader import load_phase_prompt

    # 프롬프트 로드
    try:
        phase_prompt = load_phase_prompt(2)
        phase_prompt = phase_prompt.format(context=context)
    except (FileNotFoundError, KeyError):
        phase_prompt = """설계 단계를 수행합니다.
TREE.md와 SCHEMA.md를 생성해주세요."""

    user_message = f"""프로젝트 컨텍스트:
{context}

위 정보를 바탕으로 TREE.md와 SCHEMA.md를 생성해주세요.

TREE.md에는:
- 전체 디렉토리 구조 (트리 형식)
- 각 디렉토리/파일의 용도 설명
- 테스트 디렉토리 포함

SCHEMA.md에는:
- 데이터 모델 정의 (Pydantic 스타일)
- API 엔드포인트 (해당 시)
- 설정 파일 형식
- 주요 인터페이스

각 문서를 마크다운 코드 블록으로 제공해주세요:
```markdown:TREE.md
(내용)
```

```markdown:SCHEMA.md
(내용)
```"""

    messages = [Message(role="user", content=user_message)]

    if config.dual_mode.enabled:
        # 듀얼 모드: Claude(설계) + Gemini(검증)
        from vibe.providers.orchestrator import create_orchestrator

        orchestrator = create_orchestrator(config.dual_mode)

        with spinner("Claude가 아키텍처를 설계하고 Gemini가 라이브러리를 검증 중..."):
            result = await orchestrator.execute_phase2_design(
                messages=messages,
                system=phase_prompt,
                libraries=libraries if libraries else None,
            )
        response_content = result.content
    else:
        # 단일 모드
        from vibe.providers.factory import create_provider

        provider = create_provider(config.provider)
        with spinner("AI가 설계 문서를 생성 중..."):
            response = await provider.generate(
                messages=messages,
                system=phase_prompt,
                max_tokens=8192,
            )
        response_content = response.content

    # 응답에서 문서 추출
    tree = _extract_markdown_block(response_content, "TREE.md")
    schema = _extract_markdown_block(response_content, "SCHEMA.md")

    # 기본값 제공
    if not tree:
        tree = _default_tree()

    if not schema:
        schema = _default_schema()

    return tree, schema


def _extract_markdown_block(content: str, filename: str) -> str:
    """마크다운 코드 블록에서 특정 파일 내용 추출."""
    pattern = rf'```markdown:{re.escape(filename)}\s*\n(.*?)```'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        return match.group(1).strip()

    pattern2 = rf'```{re.escape(filename)}\s*\n(.*?)```'
    match2 = re.search(pattern2, content, re.DOTALL)

    if match2:
        return match2.group(1).strip()

    return ""


def _preview_tree(content: str) -> None:
    """TREE.md 미리보기."""
    lines = content.split("\n")[:30]
    for line in lines:
        console.print(f"  {line}")
    if len(content.split("\n")) > 30:
        console.print("  ...")


def _default_tree() -> str:
    """기본 TREE.md 내용."""
    return """# 프로젝트 구조 (TREE.md)

```
project/
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py          # 엔트리포인트
│       ├── core/            # 핵심 비즈니스 로직
│       │   ├── __init__.py
│       │   └── config.py    # 설정
│       ├── models/          # 데이터 모델
│       │   └── __init__.py
│       └── utils/           # 유틸리티
│           └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   └── __init__.py
│   └── integration/
│       └── __init__.py
├── pyproject.toml
├── README.md
└── .gitignore
```

## 디렉토리 설명
- `src/app/`: 메인 애플리케이션 코드
- `tests/`: 테스트 코드
- `pyproject.toml`: 프로젝트 설정 및 의존성
"""


def _default_schema() -> str:
    """기본 SCHEMA.md 내용."""
    return """# 스키마 정의 (SCHEMA.md)

## 1. 데이터 모델

```python
from pydantic import BaseModel

class Config(BaseModel):
    \"\"\"애플리케이션 설정\"\"\"
    debug: bool = False
    log_level: str = "INFO"
```

## 2. 설정 파일

### config.yaml
```yaml
debug: false
log_level: INFO
```

## 3. 인터페이스

(필요 시 API 엔드포인트 또는 CLI 인터페이스 정의)
"""
