"""vibe chat 명령어 - 자유 대화 모드."""

import typer

from vibe.cli.ui.console import console
from vibe.cli.ui.display import print_error, print_info
from vibe.cli.ui.prompts import text_input


def chat(
    ctx: typer.Context,
    context: bool = typer.Option(
        True, "--context", "-c", help="프로젝트 컨텍스트 포함"
    ),
) -> None:
    """자유 대화 모드 - 문서 변경 없이 AI와 대화."""
    import asyncio
    from pathlib import Path

    from vibe.core.config import VIBE_DIR, load_config
    from vibe.core.context import Message, load_project_context
    from vibe.core.exceptions import VibeError

    async def run_chat() -> None:
        try:
            console.print("\n[bold blue]💬 Vibe Chat[/bold blue]")
            console.print("[dim]'exit' 또는 'quit'로 종료[/dim]\n")

            # 설정 로드 (선택적)
            vibe_path = Path.cwd() / VIBE_DIR
            config = None
            project_context = ""

            if vibe_path.exists():
                config = load_config()
                if context:
                    ctx_obj = load_project_context()
                    project_context = _build_context_string(ctx_obj)
                    console.print(f"[dim]프로젝트 컨텍스트 로드됨: {config.project_name}[/dim]\n")
            else:
                print_info("프로젝트가 초기화되지 않았습니다. 기본 모드로 실행합니다.\n")

            # 대화 기록
            conversation: list[Message] = []

            # 시스템 프롬프트
            system_prompt = """당신은 Vibe Coding Helper의 AI 어시스턴트입니다.
사용자의 질문에 친절하고 정확하게 답변하세요.
코드 관련 질문에는 구체적인 예제를 포함하세요."""

            if project_context:
                system_prompt += f"\n\n## 프로젝트 컨텍스트\n{project_context}"

            while True:
                # 사용자 입력
                try:
                    user_input = text_input("[cyan]You[/cyan]", default="")
                except (KeyboardInterrupt, EOFError):
                    console.print("\n")
                    break

                if not user_input.strip():
                    continue

                if user_input.lower() in ("exit", "quit", "q"):
                    console.print("\n[dim]대화를 종료합니다.[/dim]")
                    break

                # 메시지 추가
                conversation.append(Message(role="user", content=user_input))

                # AI 응답
                response = await _get_chat_response(
                    config=config,
                    messages=conversation,
                    system=system_prompt,
                )

                # 응답 저장
                conversation.append(Message(role="assistant", content=response))

                # 출력
                console.print(f"\n[green]AI[/green]: {response}\n")

        except VibeError as e:
            print_error(f"{e.message}")
            raise typer.Exit(1)

    asyncio.run(run_chat())


def _build_context_string(ctx) -> str:
    """ProjectContext를 문자열로 변환."""
    parts = []

    if ctx.tech_stack:
        parts.append(f"### TECH_STACK\n{ctx.tech_stack[:500]}...")

    if ctx.rules:
        parts.append(f"### RULES\n{ctx.rules[:500]}...")

    if ctx.prd:
        parts.append(f"### PRD\n{ctx.prd[:500]}...")

    return "\n\n".join(parts)


async def _get_chat_response(
    config,
    messages: list,
    system: str,
) -> str:
    """AI 응답 생성."""
    from vibe.cli.ui.progress import spinner

    if config and config.dual_mode.enabled:
        # 듀얼 모드: Claude 사용
        from vibe.providers.factory import create_provider

        provider = create_provider("anthropic")
        with spinner("생각 중..."):
            response = await provider.generate(
                messages=messages,
                system=system,
                max_tokens=2048,
            )
        return response.content
    else:
        # 기본 Provider
        from vibe.providers.factory import create_provider

        provider = create_provider(config.provider if config else "anthropic")
        with spinner("생각 중..."):
            response = await provider.generate(
                messages=messages,
                system=system,
                max_tokens=2048,
            )
        return response.content
