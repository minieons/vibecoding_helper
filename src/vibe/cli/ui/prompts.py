"""대화형 프롬프트 컴포넌트."""

from typing import Optional, TypeVar

from rich.prompt import Confirm, Prompt

from vibe.cli.ui.console import console

T = TypeVar("T")


def confirm(message: str, default: bool = True) -> bool:
    """확인 프롬프트."""
    return Confirm.ask(message, console=console, default=default)


def text_input(message: str, default: str = "") -> str:
    """텍스트 입력 프롬프트."""
    return Prompt.ask(message, console=console, default=default)


def select(message: str, choices: list[str], default: Optional[str] = None) -> str:
    """선택 프롬프트."""
    console.print(f"\n{message}")
    for i, choice in enumerate(choices, 1):
        marker = "(Recommended)" if default and choice == default else ""
        console.print(f"  {i}. {choice} {marker}")

    while True:
        response = Prompt.ask("선택", console=console, default="1")
        try:
            idx = int(response) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            if response in choices:
                return response
        console.print("[red]올바른 선택이 아닙니다.[/red]")
