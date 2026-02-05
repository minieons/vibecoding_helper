"""Typer 앱 인스턴스 및 공통 옵션."""


from __future__ import annotations

import typer
from typing import Optional

from vibe import __version__

app = typer.Typer(
    name="vibe",
    help="Vibe Coding Helper - AI 기반 문서 주도 개발 도구",
    no_args_is_help=True,
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """버전 정보 출력."""
    if value:
        typer.echo(f"Vibe Coding Helper v{__version__}")
        raise typer.Exit()


@app.callback()
def common_options(
    ctx: typer.Context,
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="AI Provider [anthropic|google|openai]"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="사용할 모델 지정"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="상세 로그 출력"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="파일 변경 없이 미리보기"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="모든 확인 프롬프트 자동 승인"
    ),
    version: bool = typer.Option(
        False, "--version", callback=version_callback, help="버전 정보"
    ),
) -> None:
    """공통 옵션 처리."""
    ctx.ensure_object(dict)
    ctx.obj["provider"] = provider
    ctx.obj["model"] = model
    ctx.obj["verbose"] = verbose
    ctx.obj["dry_run"] = dry_run
    ctx.obj["yes"] = yes


# 명령어 등록
from vibe.cli.commands import chat, code, design, init, plan, scaffold, status, test, undo, verify

app.command()(init.init)
app.command()(plan.plan)
app.command()(design.design)
app.command()(scaffold.scaffold)
app.command()(code.code)
app.command()(status.status)
app.command()(chat.chat)
app.command()(undo.undo)
app.command()(test.test)
app.command()(verify.verify)
