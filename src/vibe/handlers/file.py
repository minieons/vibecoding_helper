"""파일 읽기/쓰기/검증."""

from pathlib import Path

from vibe.core.exceptions import FileError


def read_file(path: Path) -> str:
    """파일 읽기."""
    if not path.exists():
        raise FileError(f"파일을 찾을 수 없습니다: {path}", code="E020")
    try:
        return path.read_text(encoding="utf-8")
    except PermissionError as e:
        raise FileError(f"파일 읽기 권한이 없습니다: {path}", code="E021") from e
    except Exception as e:
        raise FileError(f"파일 읽기 오류: {e}", code="E020") from e


def write_file(path: Path, content: str, create_parents: bool = True) -> None:
    """파일 쓰기."""
    try:
        if create_parents:
            path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except PermissionError as e:
        raise FileError(f"파일 쓰기 권한이 없습니다: {path}", code="E021") from e
    except Exception as e:
        raise FileError(f"파일 쓰기 오류: {e}", code="E020") from e


def ensure_directory(path: Path) -> None:
    """디렉토리 존재 보장."""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise FileError(f"디렉토리 생성 권한이 없습니다: {path}", code="E021") from e


def is_safe_path(base: Path, target: Path) -> bool:
    """경로가 base 내부에 있는지 확인 (보안)."""
    try:
        target.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False
