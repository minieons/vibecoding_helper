"""Jinja2 템플릿 로더."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent


def get_environment() -> Environment:
    """Jinja2 환경 생성."""
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_template(name: str, **context: Any) -> str:
    """템플릿 렌더링.

    Args:
        name: 템플릿 이름 (예: "PRD.md.j2")
        **context: 템플릿 변수

    Returns:
        렌더링된 문자열
    """
    env = get_environment()
    template = env.get_template(name)
    return template.render(**context)
