"""vibe verify 명령어 - 코드 검증."""

from pathlib import Path
from typing import Optional

import typer

from vibe.cli.ui.console import console
from vibe.cli.ui.display import print_error, print_info, print_success, print_warning


def verify(
    ctx: typer.Context,
    file: Optional[Path] = typer.Argument(
        None, help="검증할 파일 (없으면 전체 검증)"
    ),
    fix: bool = typer.Option(
        False, "--fix", "-f", help="자동 수정 (린트)"
    ),
    syntax_only: bool = typer.Option(
        False, "--syntax", "-s", help="문법 검사만 실행"
    ),
    skip_tests: bool = typer.Option(
        False, "--skip-tests", help="테스트 건너뛰기"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="상세 출력"
    ),
) -> None:
    """코드 검증 - 문법, 타입, 린트, 테스트."""
    from vibe.verifiers import VerifyLevel

    console.print("\n[bold blue]🔍 코드 검증[/bold blue]\n")

    # 검증 레벨 결정
    level = VerifyLevel.SYNTAX if syntax_only else VerifyLevel.ALL

    if file:
        # 단일 파일 검증
        _verify_single_file(
            file_path=file,
            level=level,
            fix=fix,
            skip_tests=skip_tests,
            verbose=verbose,
        )
    else:
        # 전체 프로젝트 검증
        _verify_project(
            level=level,
            fix=fix,
            skip_tests=skip_tests,
            verbose=verbose,
        )


def _verify_single_file(
    file_path: Path,
    level,
    fix: bool,
    skip_tests: bool,
    verbose: bool,
) -> None:
    """단일 파일 검증."""
    from vibe.verifiers import get_verifier, verify_file
    from vibe.verifiers.factory import is_supported

    if not file_path.exists():
        print_error(f"파일을 찾을 수 없습니다: {file_path}")
        raise typer.Exit(1)

    if not is_supported(file_path):
        print_warning(f"지원하지 않는 파일 형식입니다: {file_path.suffix}")
        raise typer.Exit(0)

    verifier = get_verifier(file_path)
    console.print(f"[dim]검증기: {verifier.language}[/dim]")
    console.print(f"[dim]파일: {file_path}[/dim]\n")

    # 검증 실행
    results = verify_file(
        file_path=file_path,
        level=level,
        fix=fix,
        skip_tests=skip_tests,
    )

    # 결과 출력
    _print_results(results, verbose)

    # 종료 코드
    if not verifier.is_all_passed(results):
        raise typer.Exit(1)


def _verify_project(
    level,
    fix: bool,
    skip_tests: bool,
    verbose: bool,
) -> None:
    """전체 프로젝트 검증."""
    from vibe.verifiers import get_verifier, verify_file
    from vibe.verifiers.factory import get_supported_extensions

    # 지원하는 파일 찾기
    extensions = get_supported_extensions()
    files_to_verify = []

    # src/ 디렉토리 검색
    for ext in extensions:
        files_to_verify.extend(Path.cwd().glob(f"src/**/*{ext}"))

    # tests/ 디렉토리도 검색
    for ext in extensions:
        files_to_verify.extend(Path.cwd().glob(f"tests/**/*{ext}"))

    if not files_to_verify:
        print_info("검증할 파일이 없습니다.")
        raise typer.Exit(0)

    console.print(f"[dim]검증 대상: {len(files_to_verify)}개 파일[/dim]\n")

    # 통계
    total_files = len(files_to_verify)
    passed_files = 0
    failed_files = 0
    all_issues = []

    # 각 파일 검증
    for file_path in files_to_verify:
        if verbose:
            console.print(f"검증 중: {file_path}")

        results = verify_file(
            file_path=file_path,
            level=level,
            fix=fix,
            skip_tests=True,  # 전체 검증 시 테스트는 별도로
        )

        verifier = get_verifier(file_path)

        if verifier.is_all_passed(results):
            passed_files += 1
            if verbose:
                console.print("  [green]✓[/green] 통과")
        else:
            failed_files += 1
            if verbose:
                console.print("  [red]✗[/red] 실패")

            # 이슈 수집
            for result in results:
                all_issues.extend(result.issues)

    # 요약 출력
    console.print("\n[bold]== 검증 결과 ==[/bold]")
    console.print(f"전체 파일: {total_files}개")
    console.print(f"[green]통과: {passed_files}개[/green]")

    if failed_files > 0:
        console.print(f"[red]실패: {failed_files}개[/red]")

        # 이슈 상세
        if all_issues:
            console.print(f"\n[bold]발견된 이슈: {len(all_issues)}개[/bold]")

            # 에러만 먼저 표시
            errors = [i for i in all_issues if i.level == "error"]
            warnings = [i for i in all_issues if i.level == "warning"]

            if errors:
                console.print("\n[red]Errors:[/red]")
                for issue in errors[:10]:  # 최대 10개
                    console.print(f"  • {issue}")
                if len(errors) > 10:
                    console.print(f"  ... 외 {len(errors) - 10}개")

            if warnings and verbose:
                console.print("\n[yellow]Warnings:[/yellow]")
                for issue in warnings[:5]:
                    console.print(f"  • {issue}")
                if len(warnings) > 5:
                    console.print(f"  ... 외 {len(warnings) - 5}개")

        raise typer.Exit(1)

    print_success("\n모든 파일 검증 통과!")


def _print_results(results: list, verbose: bool) -> None:
    """검증 결과 출력."""
    for result in results:
        # 상태 아이콘
        if result.success:
            icon = "[green]✓[/green]"
        else:
            icon = "[red]✗[/red]"

        console.print(f"{icon} {result.check_type.value}: ", end="")

        if result.success:
            console.print("[green]통과[/green]")
        else:
            console.print(f"[red]실패[/red] ({result.error_count} 에러)")

        # 이슈 상세 (verbose 또는 실패 시)
        if result.issues and (verbose or not result.success):
            for issue in result.issues[:5]:
                level_color = "red" if issue.level == "error" else "yellow"
                console.print(f"  [{level_color}]•[/{level_color}] {issue}")

            if len(result.issues) > 5:
                console.print(f"  ... 외 {len(result.issues) - 5}개")

    # 전체 요약
    total_errors = sum(r.error_count for r in results)
    total_warnings = sum(r.warning_count for r in results)

    console.print("")
    if total_errors == 0 and total_warnings == 0:
        print_success("검증 완료 - 이슈 없음")
    else:
        console.print(f"[dim]총 {total_errors} 에러, {total_warnings} 경고[/dim]")
