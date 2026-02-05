"""디렉토리/파일 스캐폴딩."""

from pathlib import Path
from typing import Optional

from vibe.core.exceptions import FileError
from vibe.handlers.file import ensure_directory, is_safe_path, write_file


def scaffold_from_tree(
    tree_paths: list[str],
    base_path: Optional[Path] = None,
    force: bool = False,
) -> list[Path]:
    """TREE.md 파싱 결과로 디렉토리/파일 생성.

    Args:
        tree_paths: 경로 목록
        base_path: 기준 경로
        force: 기존 파일 덮어쓰기

    Returns:
        생성된 경로 목록
    """
    if base_path is None:
        base_path = Path.cwd()

    created = []
    current_dir = base_path

    for path_str in tree_paths:
        # 경로 정규화
        path_str = path_str.strip()
        if not path_str:
            continue

        # 디렉토리인지 파일인지 판단 (/ 또는 확장자 없음)
        is_dir = path_str.endswith("/") or "." not in Path(path_str).name

        target = base_path / path_str.rstrip("/")

        # 보안 검사
        if not is_safe_path(base_path, target):
            raise FileError(
                f"허용되지 않은 경로입니다: {path_str}",
                code="E021",
            )

        if is_dir:
            ensure_directory(target)
            created.append(target)
        else:
            # 파일 생성 (이미 존재하면 스킵)
            if not target.exists() or force:
                # 빈 파일 또는 기본 내용
                content = _get_default_content(target)
                write_file(target, content)
                created.append(target)

    return created


def _get_default_content(path: Path) -> str:
    """파일 확장자에 따른 기본 내용."""
    suffix = path.suffix.lower()

    if suffix == ".py":
        module_name = path.stem
        return f'"""{module_name} 모듈."""\n'

    elif suffix in {".md", ".txt"}:
        return f"# {path.stem}\n"

    elif suffix == ".json":
        return "{}\n"

    elif suffix == ".yaml" or suffix == ".yml" or suffix == ".toml":
        return "# Configuration\n"

    elif suffix == ".j2":
        return "{% block content %}{% endblock %}\n"

    return ""
