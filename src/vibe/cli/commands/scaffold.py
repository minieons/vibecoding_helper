"""vibe scaffold 명령어 - 프로젝트 스캐폴딩."""

from pathlib import Path
from typing import Optional

import typer

from vibe.cli.ui.console import console
from vibe.cli.ui.display import print_error, print_info, print_warning
from vibe.cli.ui.progress import spinner
from vibe.cli.ui.prompts import confirm


def scaffold(
    ctx: typer.Context,
    tree: Optional[Path] = typer.Option(
        None, "--tree", help="사용할 TREE.md 경로"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="기존 파일 덮어쓰기"
    ),
) -> None:
    """스캐폴딩 - TREE.md 기반 디렉토리/파일 생성."""
    from vibe.core.config import load_config
    from vibe.core.exceptions import PhaseError, VibeError
    from vibe.core.state import load_state
    from vibe.handlers.file import read_file, write_file
    from vibe.handlers.parser import parse_tree
    from vibe.handlers.scaffold import scaffold_from_tree

    try:
        # 설정 및 상태 로드
        config = load_config()
        state = load_state()

        # Phase 확인
        if not state.is_phase_complete(2):
            raise PhaseError(
                "먼저 'vibe design'으로 설계 단계를 완료해주세요.",
                code="E040"
            )

        console.print("\n[bold blue]🔧 스캐폴딩[/bold blue]\n")

        # TREE.md 경로 결정
        tree_path = tree or (Path.cwd() / "TREE.md")

        if not tree_path.exists():
            print_error(f"TREE.md를 찾을 수 없습니다: {tree_path}")
            raise typer.Exit(1)

        # TREE.md 파싱
        tree_content = read_file(tree_path)
        paths = parse_tree(tree_content)

        if not paths:
            print_warning("TREE.md에서 생성할 경로를 찾을 수 없습니다.")
            print_info("트리 구조가 ``` 코드 블록 안에 있는지 확인하세요.")
            raise typer.Exit(1)

        console.print(f"[dim]발견된 경로: {len(paths)}개[/dim]")

        # 확인
        if not force:
            console.print("\n[bold]생성될 구조:[/bold]")
            for p in paths[:15]:
                console.print(f"  • {p}")
            if len(paths) > 15:
                console.print(f"  ... 외 {len(paths) - 15}개")

            if not confirm("\n이 구조를 생성하시겠습니까?", default=True):
                print_info("취소되었습니다.")
                raise typer.Exit(0)

        # 스캐폴딩 실행
        with spinner("디렉토리 및 파일 생성 중..."):
            created = scaffold_from_tree(
                tree_paths=paths,
                base_path=Path.cwd(),
                force=force,
            )

        # TODO.md 생성
        todo_path = Path.cwd() / "TODO.md"
        if not todo_path.exists():
            with spinner("TODO.md 생성 중..."):
                todo_content = _generate_todo_from_tree(paths, config.project_name)
                write_file(todo_path, todo_content)
                created.append(todo_path)

        # 상태 업데이트
        if state.current_phase < 3:
            state.advance_phase()
        state.save()

        # 결과 출력
        console.print("\n[bold green]✓ 스캐폴딩 완료![/bold green]\n")

        console.print(f"[bold]생성된 항목: {len(created)}개[/bold]")

        # 디렉토리와 파일 분리
        dirs = [p for p in created if p.is_dir()]
        files = [p for p in created if p.is_file()]

        if dirs:
            console.print(f"  • 디렉토리: {len(dirs)}개")
        if files:
            console.print(f"  • 파일: {len(files)}개")

        console.print("\n[bold]다음 단계:[/bold]")
        console.print("  1. 생성된 파일 구조를 확인하세요")
        console.print("  2. [cyan]vibe code[/cyan]로 구현을 시작하세요")

    except VibeError as e:
        print_error(f"{e.message}")
        if e.code:
            console.print(f"[dim]에러 코드: {e.code}[/dim]")
        raise typer.Exit(1)


def _generate_todo_from_tree(paths: list[str], project_name: str) -> str:
    """TREE.md에서 TODO.md 생성."""
    # Python 파일만 추출
    py_files = [p for p in paths if p.endswith(".py") and not p.startswith("__")]

    todo_lines = [
        f"# TODO - {project_name}",
        "",
        "## Phase 3: 구현",
        "",
    ]

    # 파일별 작업 생성
    for i, file_path in enumerate(py_files, 1):
        task_id = f"CODE-{i:03d}"
        file_name = Path(file_path).stem
        todo_lines.append(f"- [ ] {task_id}: {file_name} 구현")
        todo_lines.append(f"  - 파일: {file_path}")
        todo_lines.append("")

    # 진행 상황 테이블
    todo_lines.extend([
        "---",
        "",
        "## 진행 상황",
        "",
        "| Phase | 완료 | 전체 | 진행률 |",
        "|-------|-----|------|--------|",
        f"| Phase 3 | 0 | {len(py_files)} | 0% |",
        "",
    ])

    return "\n".join(todo_lines)
