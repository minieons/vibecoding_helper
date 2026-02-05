"""프롬프트 로딩 유틸리티."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(category: str, name: str) -> str:
    """프롬프트 파일 로드.

    Args:
        category: 카테고리 (system, phases)
        name: 프롬프트 이름 (확장자 제외)

    Returns:
        프롬프트 내용
    """
    path = PROMPTS_DIR / category / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"프롬프트를 찾을 수 없습니다: {path}")
    return path.read_text(encoding="utf-8")


def load_system_prompt() -> str:
    """기본 시스템 프롬프트 로드."""
    return load_prompt("system", "base")


def load_phase_prompt(phase: int) -> str:
    """Phase별 프롬프트 로드."""
    phase_names = {
        0: "phase0_init",
        1: "phase1_plan",
        2: "phase2_design",
        3: "phase3_code",
    }
    name = phase_names.get(phase)
    if not name:
        raise ValueError(f"알 수 없는 Phase: {phase}")
    return load_prompt("phases", name)
