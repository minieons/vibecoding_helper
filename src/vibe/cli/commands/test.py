"""vibe test 명령어 - Phase 4 테스트."""

from pathlib import Path

import typer

from vibe.cli.ui.console import console
from vibe.cli.ui.display import print_error, print_info, print_success
from vibe.cli.ui.progress import spinner


def test(
    ctx: typer.Context,
    audit: bool = typer.Option(
        False, "--audit", help="Gemini를 사용한 전역 감사 실행"
    ),
    edge_cases: bool = typer.Option(
        False, "--edge-cases", help="Claude를 사용한 엣지 케이스 생성"
    ),
    coverage: bool = typer.Option(
        False, "--coverage", help="테스트 커버리지 분석"
    ),
    all_tests: bool = typer.Option(
        False, "--all", "-a", help="모든 테스트 실행"
    ),
    output: Path = typer.Option(
        None, "--output", "-o", help="결과 저장 경로"
    ),
) -> None:
    """Phase 4: 테스트 - 전역 감사, 엣지 케이스 생성.

    듀얼 모델 전략:
    - --audit: Gemini가 전체 코드베이스 감사
    - --edge-cases: Claude가 엣지 케이스 테스트 생성
    """
    import asyncio

    from vibe.core.config import load_config
    from vibe.core.context import load_dual_track_context
    from vibe.core.exceptions import PhaseError, VibeError
    from vibe.core.state import load_state

    # 옵션 검증
    if not any([audit, edge_cases, coverage, all_tests]):
        console.print(
            "[yellow]옵션을 선택하세요:[/yellow]\n"
            "  --audit       전역 감사 (Gemini)\n"
            "  --edge-cases  엣지 케이스 생성 (Claude)\n"
            "  --coverage    커버리지 분석\n"
            "  --all         모든 테스트 실행"
        )
        raise typer.Exit(1)

    async def run_test() -> None:
        try:
            # 설정 및 상태 로드
            config = load_config()
            state = load_state()

            # Phase 확인 (Phase 3 이상에서 실행 가능)
            if state.current_phase < 3:
                raise PhaseError(
                    "테스트는 Phase 3 (구현) 이후에 실행할 수 있습니다.",
                    code="E040"
                )

            # 듀얼 모드 확인
            if not config.dual_mode.enabled:
                print_info("듀얼 모드가 비활성화되어 있습니다. 단일 모델로 실행합니다.")

            # 컨텍스트 로드
            with spinner("프로젝트 컨텍스트 로드 중..."):
                dual_ctx = load_dual_track_context(include_codebase=True)

            console.print(
                f"[dim]코드베이스: {dual_ctx.cold.get_file_count()}개 파일[/dim]"
            )

            results = []

            # 전역 감사 실행
            if audit or all_tests:
                console.print("\n[bold blue]== 전역 감사 (Gemini) ==[/bold blue]")
                with spinner("Gemini가 코드베이스를 분석 중..."):
                    audit_result = await _run_audit(config, dual_ctx)
                results.append(("감사 리포트", audit_result))
                print_success("전역 감사 완료")

            # 엣지 케이스 생성
            if edge_cases or all_tests:
                console.print("\n[bold blue]== 엣지 케이스 생성 (Claude) ==[/bold blue]")
                with spinner("Claude가 테스트 케이스를 생성 중..."):
                    edge_result = await _run_edge_cases(config, dual_ctx)
                results.append(("엣지 케이스", edge_result))
                print_success("엣지 케이스 생성 완료")

            # 커버리지 분석
            if coverage or all_tests:
                console.print("\n[bold blue]== 커버리지 분석 ==[/bold blue]")
                with spinner("커버리지 분석 중..."):
                    coverage_result = await _run_coverage(config, dual_ctx)
                results.append(("커버리지", coverage_result))
                print_success("커버리지 분석 완료")

            # 결과 출력
            for title, content in results:
                console.print(f"\n[bold]# {title}[/bold]")
                console.print(content)

            # 파일로 저장 (선택적)
            if output:
                combined = "\n\n---\n\n".join(
                    f"# {title}\n\n{content}" for title, content in results
                )
                output.write_text(combined, encoding="utf-8")
                print_info(f"결과가 {output}에 저장되었습니다.")

        except VibeError as e:
            print_error(f"{e.message}")
            if e.code:
                console.print(f"[dim]에러 코드: {e.code}[/dim]")
            raise typer.Exit(1)

    asyncio.run(run_test())


async def _run_audit(config, dual_ctx) -> str:
    """전역 감사 실행."""
    from vibe.core.context import Message
    from vibe.prompts.loader import load_prompt
    from vibe.providers.orchestrator import create_orchestrator

    # 프롬프트 로드
    try:
        audit_prompt = load_prompt("utils", "audit_request")
    except FileNotFoundError:
        audit_prompt = "전체 코드베이스를 감사하고 이슈를 식별해주세요."

    # 코드베이스 준비
    codebase_str = dual_ctx.cold.to_prompt()

    messages = [
        Message(
            role="user",
            content=audit_prompt.format(
                codebase=codebase_str,
                timestamp="now",
                file_count=dual_ctx.cold.get_file_count(),
                line_count="N/A",
            ),
        )
    ]

    # 오케스트레이터 사용 (Gemini 담당)
    orchestrator = create_orchestrator(config.dual_mode)
    result = await orchestrator.execute_phase4_test(
        messages,
        full_codebase=dual_ctx.cold.full_codebase,
        mode="audit",
    )

    return result.content


async def _run_edge_cases(config, dual_ctx) -> str:
    """엣지 케이스 생성."""
    from vibe.core.context import Message
    from vibe.prompts.loader import load_prompt
    from vibe.providers.orchestrator import create_orchestrator

    # 프롬프트 로드
    try:
        edge_prompt = load_prompt("utils", "edge_case_gen")
    except FileNotFoundError:
        edge_prompt = "다음 코드에 대한 엣지 케이스 테스트를 생성해주세요:\n{target_code}"

    # 주요 파일 선택 (core 모듈)
    target_files = {
        k: v for k, v in dual_ctx.cold.full_codebase.items()
        if "core" in k and k.endswith(".py")
    }

    target_code = "\n\n".join(
        f"### {path}\n```python\n{content}\n```"
        for path, content in list(target_files.items())[:3]  # 상위 3개
    )

    messages = [
        Message(
            role="user",
            content=edge_prompt.format(
                target_code=target_code,
                context=dual_ctx.hot.rules or "",
                module_name="core",
                module_path="vibe.core",
                target_class_or_function="VibeConfig",
                TargetName="Config",
            ),
        )
    ]

    # 오케스트레이터 사용 (Claude 담당)
    orchestrator = create_orchestrator(config.dual_mode)
    result = await orchestrator.execute_phase4_test(
        messages,
        mode="edge_cases",
    )

    return result.content


async def _run_coverage(config, dual_ctx) -> str:
    """커버리지 분석."""
    # 간단한 커버리지 분석 (실제로는 pytest-cov 결과 파싱)
    test_files = [
        f for f in dual_ctx.cold.full_codebase.keys()
        if "test_" in f
    ]

    src_files = [
        f for f in dual_ctx.cold.full_codebase.keys()
        if f.startswith("src/") and f.endswith(".py") and "test_" not in f
    ]

    result = f"""# 커버리지 분석

## 파일 현황
- 소스 파일: {len(src_files)}개
- 테스트 파일: {len(test_files)}개

## 테스트되지 않은 파일
"""

    # 테스트 파일이 없는 소스 파일 찾기
    for src in src_files:
        # src/vibe/core/config.py -> test_config.py
        base_name = Path(src).stem
        test_name = f"test_{base_name}.py"
        if not any(test_name in t for t in test_files):
            result += f"- {src}\n"

    result += """
## 권장 조치
1. pytest --cov=src/vibe 실행하여 상세 커버리지 확인
2. 누락된 모듈에 대한 테스트 작성
"""

    return result
