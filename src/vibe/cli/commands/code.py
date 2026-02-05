"""vibe code 명령어 - 구현 단계."""

from pathlib import Path
from typing import Optional

import typer

from vibe.cli.ui.console import console
from vibe.cli.ui.display import print_error, print_success, print_warning
from vibe.cli.ui.progress import spinner


def code(
    ctx: typer.Context,
    task_id: Optional[str] = typer.Argument(
        None, help="작업 ID (없으면 다음 작업 자동 선택)"
    ),
    file: Optional[Path] = typer.Option(
        None, "--file", "-f", help="특정 파일만 처리"
    ),
    all_tasks: bool = typer.Option(
        False, "--all", "-a", help="모든 미완료 작업 연속 처리"
    ),
) -> None:
    """구현 단계 - TODO.md 기반 코드 생성."""
    import asyncio

    from vibe.core.config import load_config
    from vibe.core.exceptions import PhaseError, VibeError
    from vibe.core.state import load_state
    from vibe.handlers.file import read_file
    from vibe.handlers.parser import parse_todo

    async def run_code() -> None:
        try:
            # 설정 및 상태 로드
            config = load_config()
            state = load_state()

            # Phase 확인 (Phase 2 이상에서 실행 가능)
            if state.current_phase < 3:
                raise PhaseError(
                    "먼저 'vibe scaffold'로 스캐폴딩을 완료해주세요.",
                    code="E040"
                )

            console.print("\n[bold blue]💻 Phase 3: 구현[/bold blue]\n")

            # TODO.md 로드
            todo_path = Path.cwd() / "TODO.md"
            if not todo_path.exists():
                print_error("TODO.md를 찾을 수 없습니다.")
                raise typer.Exit(1)

            todo_content = read_file(todo_path)
            todo_list = parse_todo(todo_content)

            # 진행 상황 표시
            completed, total = todo_list.get_progress()
            console.print(f"[dim]진행률: {completed}/{total} ({completed*100//total if total else 0}%)[/dim]")

            # 특정 파일 모드
            if file:
                await _code_single_file(config, file)
                return

            # 작업 선택
            if task_id:
                task = todo_list.get_task(task_id)
                if not task:
                    print_error(f"작업을 찾을 수 없습니다: {task_id}")
                    raise typer.Exit(1)
            else:
                task = todo_list.get_next_task()
                if not task:
                    print_success("모든 작업이 완료되었습니다!")
                    raise typer.Exit(0)

            # 연속 처리 모드
            if all_tasks:
                await _code_all_tasks(config, todo_list, todo_path)
            else:
                await _code_single_task(config, task, todo_list, todo_path)

        except VibeError as e:
            print_error(f"{e.message}")
            if e.code:
                console.print(f"[dim]에러 코드: {e.code}[/dim]")
            raise typer.Exit(1)

    asyncio.run(run_code())


async def _code_single_task(config, task, todo_list, todo_path) -> None:
    """단일 작업 처리."""
    from vibe.core.context import load_dual_track_context

    console.print(f"\n[bold]작업: {task.id} - {task.title}[/bold]")

    if task.files:
        console.print(f"[dim]대상 파일: {', '.join(task.files)}[/dim]")

    # 컨텍스트 로드
    with spinner("컨텍스트 로드 중..."):
        dual_ctx = load_dual_track_context(include_codebase=True)

    # 코드 생성
    for file_path in task.files or [_guess_file_path(task)]:
        await _generate_code_for_file(
            config=config,
            file_path=file_path,
            task=task,
            dual_ctx=dual_ctx,
        )

    # 작업 완료 처리
    todo_list.mark_completed(task.id)

    # TODO.md 업데이트
    _update_todo_file(todo_path, task.id)

    print_success(f"작업 완료: {task.id}")


async def _code_all_tasks(config, todo_list, todo_path) -> None:
    """모든 미완료 작업 처리."""
    from vibe.core.context import load_dual_track_context

    task = todo_list.get_next_task()
    while task:
        console.print(f"\n[bold]작업: {task.id} - {task.title}[/bold]")

        # 컨텍스트 로드 (매번 새로)
        with spinner("컨텍스트 로드 중..."):
            dual_ctx = load_dual_track_context(include_codebase=True)

        for file_path in task.files or [_guess_file_path(task)]:
            await _generate_code_for_file(
                config=config,
                file_path=file_path,
                task=task,
                dual_ctx=dual_ctx,
            )

        todo_list.mark_completed(task.id)
        _update_todo_file(todo_path, task.id)
        print_success(f"작업 완료: {task.id}")

        task = todo_list.get_next_task()

    print_success("\n모든 작업이 완료되었습니다!")


async def _code_single_file(config, file_path: Path) -> None:
    """단일 파일 코드 생성."""
    from vibe.core.context import load_dual_track_context

    console.print(f"\n[bold]파일: {file_path}[/bold]")

    if not file_path.exists():
        print_warning(f"파일이 없습니다. 새로 생성합니다: {file_path}")

    with spinner("컨텍스트 로드 중..."):
        dual_ctx = load_dual_track_context(include_codebase=True)

    await _generate_code_for_file(
        config=config,
        file_path=str(file_path),
        task=None,
        dual_ctx=dual_ctx,
    )

    print_success(f"파일 생성 완료: {file_path}")


async def _generate_code_for_file(config, file_path: str, task, dual_ctx) -> None:
    """파일에 대한 코드 생성."""
    from vibe.core.context import Message
    from vibe.handlers.file import read_file, write_file
    from vibe.prompts.loader import load_phase_prompt

    # 기존 파일 내용
    full_path = Path.cwd() / file_path
    existing_content = ""
    if full_path.exists():
        try:
            existing_content = read_file(full_path)
        except Exception:
            pass

    # 프롬프트 구성
    try:
        phase_prompt = load_phase_prompt(3)
    except FileNotFoundError:
        phase_prompt = "코드를 생성해주세요."

    task_desc = ""
    if task:
        task_desc = f"""
작업 ID: {task.id}
작업 제목: {task.title}
작업 설명: {task.description or '없음'}
"""

    user_message = f"""다음 파일의 코드를 구현해주세요.

파일 경로: {file_path}
{task_desc}

## RULES.md (준수 필수)
{dual_ctx.hot.rules or '규칙 없음'}

## 기존 코드 (있는 경우)
```python
{existing_content or '# 새 파일'}
```

완성된 코드만 출력해주세요. 마크다운 코드 블록 없이 순수 Python 코드만 반환하세요."""

    messages = [Message(role="user", content=user_message)]

    if config.dual_mode.enabled:
        from vibe.providers.orchestrator import create_orchestrator

        orchestrator = create_orchestrator(config.dual_mode)

        with spinner(f"Claude가 {Path(file_path).name}를 구현 중..."):
            result = await orchestrator.execute_phase3_code(
                messages=messages,
                system=phase_prompt,
                full_codebase=dual_ctx.cold.full_codebase,
            )
        generated_code = result.content
    else:
        from vibe.providers.factory import create_provider

        provider = create_provider(config.provider)
        with spinner(f"AI가 {Path(file_path).name}를 구현 중..."):
            response = await provider.generate(
                messages=messages,
                system=phase_prompt,
                max_tokens=8192,
            )
        generated_code = response.content

    # 코드 정리 (마크다운 코드 블록 제거)
    generated_code = _clean_code_output(generated_code)

    # 파일 저장
    write_file(full_path, generated_code)
    console.print(f"  [green]✓[/green] {file_path}")

    # 자동 검증
    await _verify_generated_code(config, full_path, dual_ctx)


async def _verify_generated_code(config, file_path: Path, dual_ctx) -> None:
    """생성된 코드 검증 및 Self-Healing."""
    from vibe.core.workflow import verify_and_heal
    from vibe.verifiers.factory import is_supported

    if not is_supported(file_path):
        return

    def on_status(msg: str) -> None:
        """상태 메시지 출력."""
        if "통과" in msg or "성공" in msg:
            console.print(f"  [green]✓[/green] {msg}")
        elif "실패" in msg or "오류" in msg:
            console.print(f"  [red]✗[/red] {msg}")
        elif "시도" in msg:
            console.print(f"  [yellow]→[/yellow] {msg}")
        else:
            console.print(f"  [dim]{msg}[/dim]")

    # 모듈화된 Self-Healing 워크플로우 사용
    if config.dual_mode.enabled:
        success, healing_result = await verify_and_heal(
            file_path=file_path,
            dual_config=config.dual_mode,
            dual_ctx=dual_ctx,
            on_status=on_status,
        )

        # 실패 시 에러 상세 표시
        if not success and healing_result:
            for error in healing_result.remaining_errors[:3]:
                console.print(f"    [red]•[/red] {error}")
    else:
        # 듀얼 모드 비활성화 시 검증만 수행
        from vibe.verifiers import VerifyLevel, get_verifier, verify_file

        results = verify_file(file_path, level=VerifyLevel.SYNTAX)
        verifier = get_verifier(file_path)

        if verifier.is_all_passed(results):
            on_status("문법 검증 통과")
            lint_results = verify_file(file_path, level=VerifyLevel.LINT, fix=True)
            if lint_results and lint_results[0].fix_applied:
                on_status("린트 자동 수정 적용")
        else:
            on_status("문법 오류 발견 - 수동 수정 필요")
            for result in results:
                for issue in result.issues[:3]:
                    console.print(f"    [red]•[/red] {issue.message}")


def _clean_code_output(content: str) -> str:
    """AI 출력에서 순수 코드 추출."""
    import re

    # 마크다운 코드 블록 제거
    pattern = r'```(?:python)?\s*\n(.*?)```'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 코드 블록이 없으면 그대로 반환
    return content.strip()


def _guess_file_path(task) -> str:
    """작업에서 파일 경로 추측."""
    # 제목에서 파일명 추출 시도
    title_lower = task.title.lower()

    if "config" in title_lower:
        return "src/app/core/config.py"
    elif "model" in title_lower:
        return "src/app/models/__init__.py"
    elif "main" in title_lower:
        return "src/app/main.py"

    return f"src/app/{task.id.lower().replace('-', '_')}.py"


def _update_todo_file(todo_path: Path, task_id: str) -> None:
    """TODO.md에서 작업 완료 체크."""
    import re

    from vibe.handlers.file import read_file, write_file

    content = read_file(todo_path)

    # - [ ] TASK-ID: -> - [x] TASK-ID:
    pattern = rf'(- \[) \](\s+{re.escape(task_id)}:)'
    replacement = r'\1x\2'

    new_content = re.sub(pattern, replacement, content)
    write_file(todo_path, new_content)
