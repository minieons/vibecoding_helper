"""출력 포매팅 유틸리티."""

from rich.panel import Panel

from vibe.cli.ui.console import console, error_console


def print_success(message: str) -> None:
    """성공 메시지 출력."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """에러 메시지 출력."""
    error_console.print(f"[red]✗[/red] {message}")


def print_warning(message: str) -> None:
    """경고 메시지 출력."""
    console.print(f"[yellow]![/yellow] {message}")


def print_info(message: str) -> None:
    """정보 메시지 출력."""
    console.print(f"[blue]ℹ[/blue] {message}")


def print_panel(content: str, title: str = "") -> None:
    """패널로 감싼 내용 출력."""
    console.print(Panel(content, title=title))
