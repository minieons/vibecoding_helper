"""마크다운/YAML/TODO 파싱."""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """작업 상태."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class Task(BaseModel):
    """TODO 작업 항목."""

    id: str
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: str = "must"
    phase: int = Field(ge=0, le=3)
    files: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    user_story: Optional[str] = None


class TodoList(BaseModel):
    """TODO.md 파싱 결과."""

    tasks: list[Task] = Field(default_factory=list)

    def get_next_task(self) -> Optional[Task]:
        """다음 실행할 작업 반환."""
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                # 의존 작업이 모두 완료되었는지 확인
                deps_complete = all(
                    self.get_task(dep_id).status == TaskStatus.COMPLETED
                    for dep_id in task.depends_on
                    if self.get_task(dep_id)
                )
                if deps_complete:
                    return task
        return None

    def get_task(self, task_id: str) -> Optional[Task]:
        """ID로 작업 찾기."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def mark_completed(self, task_id: str) -> None:
        """작업 완료 처리."""
        task = self.get_task(task_id)
        if task:
            task.status = TaskStatus.COMPLETED

    def get_progress(self) -> tuple[int, int]:
        """진행 상황 (완료, 전체)."""
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        return completed, len(self.tasks)


def parse_todo(content: str) -> TodoList:
    """TODO.md 파싱."""
    tasks = []
    current_phase = 0

    # Phase 섹션 패턴
    phase_pattern = re.compile(r"##\s+Phase\s+(\d+)")
    # 작업 패턴: - [x] ID: 제목 (우선순위)
    task_pattern = re.compile(r"-\s+\[([ xX])\]\s+(\w+-\d+):\s+(.+?)(?:\s+\((\w+)\))?$")

    for line in content.split("\n"):
        phase_match = phase_pattern.match(line)
        if phase_match:
            current_phase = int(phase_match.group(1))
            continue

        task_match = task_pattern.match(line.strip())
        if task_match:
            checked, task_id, title, priority = task_match.groups()
            tasks.append(
                Task(
                    id=task_id,
                    title=title,
                    status=TaskStatus.COMPLETED if checked.lower() == "x" else TaskStatus.PENDING,
                    priority=priority.lower() if priority else "must",
                    phase=current_phase,
                )
            )

    return TodoList(tasks=tasks)


def parse_tree(content: str) -> list[str]:
    """TREE.md에서 경로 목록 추출."""
    paths = []
    # 트리 라인 패턴: │   ├── filename
    tree_pattern = re.compile(r"[│├└─\s]*(.+?)(?:\s+#.*)?$")

    in_tree_block = False
    for line in content.split("\n"):
        if line.strip().startswith("```"):
            in_tree_block = not in_tree_block
            continue

        if in_tree_block:
            match = tree_pattern.match(line)
            if match:
                name = match.group(1).strip()
                if name and not name.startswith("#"):
                    paths.append(name)

    return paths
