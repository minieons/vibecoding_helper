"""vibe undo 명령어 - 작업 되돌리기."""

import typer

from vibe.cli.ui.console import console
from vibe.cli.ui.display import print_error, print_info, print_success, print_warning
from vibe.cli.ui.prompts import confirm


def undo(
    ctx: typer.Context,
    steps: int = typer.Option(
        1, "--steps", "-n", help="되돌릴 작업 수"
    ),
) -> None:
    """마지막 작업 되돌리기 - Git 기반 롤백."""
    from pathlib import Path

    from vibe.core.config import VIBE_DIR, load_config
    from vibe.core.exceptions import VibeError
    from vibe.core.state import load_state
    from vibe.handlers.git import get_recent_commits, git_revert, is_git_repo

    try:
        # 초기화 확인
        vibe_path = Path.cwd() / VIBE_DIR
        if not vibe_path.exists():
            print_error("프로젝트가 초기화되지 않았습니다.")
            raise typer.Exit(1)

        config = load_config()
        state = load_state()

        console.print("\n[bold blue]⏪ 작업 되돌리기[/bold blue]\n")

        # Git 확인
        if not is_git_repo():
            print_warning("Git 저장소가 아닙니다.")
            print_info("Git 기반 되돌리기를 사용하려면 'git init'을 먼저 실행하세요.")
            raise typer.Exit(1)

        # 최근 커밋 조회
        commits = get_recent_commits(steps + 2)

        if not commits:
            print_info("되돌릴 커밋이 없습니다.")
            raise typer.Exit(0)

        # 되돌릴 커밋 표시
        console.print(f"[bold]최근 커밋 ({len(commits)}개):[/bold]")
        for i, commit in enumerate(commits[:steps], 1):
            marker = "[yellow]→[/yellow]" if i <= steps else "[dim] [/dim]"
            console.print(f"  {marker} {commit['hash'][:7]} - {commit['message']}")

        # 확인
        if not confirm(f"\n{steps}개의 커밋을 되돌리시겠습니까?", default=False):
            print_info("취소되었습니다.")
            raise typer.Exit(0)

        # 되돌리기 실행
        for i in range(steps):
            result = git_revert()
            if result:
                print_success(f"커밋 {i + 1}/{steps} 되돌림 완료")
            else:
                print_error(f"커밋 {i + 1} 되돌리기 실패")
                raise typer.Exit(1)

        console.print("\n[bold green]✓ 되돌리기 완료![/bold green]")
        print_info("'git status'로 변경 사항을 확인하세요.")

    except VibeError as e:
        print_error(f"{e.message}")
        raise typer.Exit(1)
