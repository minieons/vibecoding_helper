"""프로그레스바, 스피너 컴포넌트."""

from collections.abc import Iterator
from contextlib import contextmanager

from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.status import Status

from vibe.cli.ui.console import console


@contextmanager
def spinner(message: str) -> Iterator[Status]:
    """스피너 컨텍스트 매니저."""
    with console.status(message) as status:
        yield status


def create_progress() -> Progress:
    """프로그레스바 생성."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )
