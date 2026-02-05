"""Rich Console 래퍼."""

from rich.console import Console

# 전역 콘솔 인스턴스
console = Console()
error_console = Console(stderr=True)
