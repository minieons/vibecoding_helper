"""vibe status 명령어 - 상태 확인."""

import json
from pathlib import Path

import typer

from vibe.cli.ui.console import console
from vibe.cli.ui.display import print_error, print_info


def status(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False, "--json", help="JSON 형식으로 출력"
    ),
) -> None:
    """현재 Phase 및 진행 상황 표시."""
    from vibe.core.config import VIBE_DIR, load_config
    from vibe.core.exceptions import VibeError
    from vibe.core.state import load_state
    from vibe.core.workflow import PHASE_NAMES
    from vibe.handlers.file import read_file
    from vibe.handlers.parser import parse_todo

    try:
        # 초기화 여부 확인
        vibe_path = Path.cwd() / VIBE_DIR
        if not vibe_path.exists():
            print_info("프로젝트가 초기화되지 않았습니다.")
            print_info("'vibe init'으로 시작하세요.")
            raise typer.Exit(0)

        config = load_config()
        state = load_state()

        # JSON 출력
        if json_output:
            output = {
                "project_name": config.project_name,
                "project_type": config.project_type,
                "current_phase": state.current_phase,
                "phase_name": PHASE_NAMES.get(state.current_phase, "Unknown"),
                "phase_status": {k: v.value for k, v in state.phase_status.items()},
                "dual_mode": config.dual_mode.enabled,
                "last_action": state.last_action.model_dump() if state.last_action else None,
            }

            # TODO 진행률
            todo_path = Path.cwd() / "TODO.md"
            if todo_path.exists():
                todo_content = read_file(todo_path)
                todo_list = parse_todo(todo_content)
                completed, total = todo_list.get_progress()
                output["todo_progress"] = {
                    "completed": completed,
                    "total": total,
                    "percentage": completed * 100 // total if total else 0,
                }

            console.print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
            return

        # 일반 출력
        console.print("\n[bold blue]📊 Vibe Status[/bold blue]\n")

        # 프로젝트 정보
        console.print(f"[bold]프로젝트:[/bold] {config.project_name}")
        console.print(f"[bold]유형:[/bold] {config.project_type}")

        # 듀얼 모드
        dual_status = "[green]활성화[/green]" if config.dual_mode.enabled else "[dim]비활성화[/dim]"
        console.print(f"[bold]듀얼 모드:[/bold] {dual_status}")

        # 현재 Phase
        phase_name = PHASE_NAMES.get(state.current_phase, "Unknown")
        console.print(f"\n[bold]현재 Phase:[/bold] {state.current_phase} - {phase_name}")

        # Phase 상태
        console.print("\n[bold]Phase 진행 상황:[/bold]")
        for phase_num in range(5):  # 0-4
            phase_key = str(phase_num)
            status_value = state.phase_status.get(phase_key)
            name = PHASE_NAMES.get(phase_num, f"Phase {phase_num}")

            if status_value:
                if status_value.value == "completed":
                    icon = "[green]✓[/green]"
                elif status_value.value == "in_progress":
                    icon = "[yellow]→[/yellow]"
                else:
                    icon = "[dim]○[/dim]"
            else:
                icon = "[dim]○[/dim]"

            console.print(f"  {icon} Phase {phase_num}: {name}")

        # TODO 진행률
        todo_path = Path.cwd() / "TODO.md"
        if todo_path.exists():
            todo_content = read_file(todo_path)
            todo_list = parse_todo(todo_content)
            completed, total = todo_list.get_progress()

            if total > 0:
                percentage = completed * 100 // total
                bar_filled = percentage // 5
                bar_empty = 20 - bar_filled

                progress_bar = f"[green]{'█' * bar_filled}[/green][dim]{'░' * bar_empty}[/dim]"
                console.print(f"\n[bold]작업 진행률:[/bold] {progress_bar} {percentage}% ({completed}/{total})")

                # 다음 작업
                next_task = todo_list.get_next_task()
                if next_task:
                    console.print(f"[bold]다음 작업:[/bold] {next_task.id} - {next_task.title}")

        # 마지막 작업
        if state.last_action:
            console.print(f"\n[bold]마지막 작업:[/bold] {state.last_action.command}")
            console.print(f"[dim]시간: {state.last_action.timestamp}[/dim]")

        console.print("")

    except VibeError as e:
        print_error(f"{e.message}")
        raise typer.Exit(1)
