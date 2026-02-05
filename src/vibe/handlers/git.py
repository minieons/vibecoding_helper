"""Git 연동 (커밋, 롤백)."""

from pathlib import Path
from typing import Optional

from vibe.core.exceptions import GitError


def is_git_repo(path: Optional[Path] = None) -> bool:
    """Git 저장소인지 확인."""
    if path is None:
        path = Path.cwd()
    return (path / ".git").is_dir()


def ensure_git_repo(path: Optional[Path] = None) -> None:
    """Git 저장소 확인."""
    if not is_git_repo(path):
        raise GitError(
            "Git 저장소가 아닙니다. 'git init'을 먼저 실행하세요.",
            code="E030",
        )


def init_repo(path: Optional[Path] = None) -> None:
    """Git 저장소 초기화."""
    try:
        import git

        if path is None:
            path = Path.cwd()
        git.Repo.init(path)
    except Exception as e:
        raise GitError(f"Git 초기화 실패: {e}", code="E030") from e


def commit(message: str, files: list[Path] | None = None) -> str:
    """커밋 생성."""
    try:
        import git

        repo = git.Repo(Path.cwd())

        # 파일 스테이징
        if files:
            for f in files:
                repo.index.add([str(f)])
        else:
            repo.index.add(".")

        # 커밋
        commit_obj = repo.index.commit(message)
        return commit_obj.hexsha[:7]
    except Exception as e:
        raise GitError(f"커밋 실패: {e}", code="E031") from e


def undo_commit(steps: int = 1) -> None:
    """커밋 되돌리기."""
    try:
        import git

        repo = git.Repo(Path.cwd())
        repo.head.reset(f"HEAD~{steps}", index=True, working_tree=True)
    except Exception as e:
        raise GitError(f"롤백 실패: {e}", code="E031") from e


def has_uncommitted_changes() -> bool:
    """커밋되지 않은 변경사항 확인."""
    try:
        import git

        repo = git.Repo(Path.cwd())
        return repo.is_dirty(untracked_files=True)
    except Exception:
        return False


def get_recent_commits(count: int = 5) -> list[dict]:
    """최근 커밋 목록 조회."""
    try:
        import git

        repo = git.Repo(Path.cwd())
        commits = []

        for commit_obj in repo.iter_commits(max_count=count):
            commits.append({
                "hash": commit_obj.hexsha,
                "message": commit_obj.message.strip().split("\n")[0],
                "author": str(commit_obj.author),
                "date": commit_obj.committed_datetime,
            })

        return commits
    except Exception:
        return []


def git_revert() -> bool:
    """마지막 커밋 되돌리기 (revert)."""
    try:
        import git

        repo = git.Repo(Path.cwd())
        repo.git.revert("HEAD", no_edit=True)
        return True
    except Exception:
        return False
