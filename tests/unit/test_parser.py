"""parser 모듈 테스트."""

import pytest

from vibe.handlers.parser import (
    Task,
    TaskStatus,
    TodoList,
    parse_todo,
    parse_tree,
)


class TestTaskStatus:
    """TaskStatus 열거형 테스트."""

    def test_values(self):
        """값 검증."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.SKIPPED.value == "skipped"


class TestTask:
    """Task 모델 테스트."""

    def test_create(self):
        """생성 테스트."""
        task = Task(
            id="CODE-001",
            title="테스트 작업",
            description="작업 설명",
            priority="must",
            phase=3,
            files=["src/main.py"],
            depends_on=["CODE-000"],
        )
        assert task.id == "CODE-001"
        assert task.title == "테스트 작업"
        assert task.status == TaskStatus.PENDING
        assert task.phase == 3
        assert len(task.files) == 1

    def test_defaults(self):
        """기본값 테스트."""
        task = Task(id="T-001", title="Test", phase=0)
        assert task.status == TaskStatus.PENDING
        assert task.priority == "must"
        assert task.files == []
        assert task.depends_on == []
        assert task.description is None

    def test_phase_validation(self):
        """Phase 범위 검증."""
        # 유효한 범위
        for phase in range(4):
            task = Task(id="T-001", title="Test", phase=phase)
            assert task.phase == phase

        # 범위 초과
        with pytest.raises(ValueError):
            Task(id="T-001", title="Test", phase=4)

        with pytest.raises(ValueError):
            Task(id="T-001", title="Test", phase=-1)


class TestTodoList:
    """TodoList 모델 테스트."""

    @pytest.fixture
    def sample_tasks(self) -> list[Task]:
        """샘플 작업 목록."""
        return [
            Task(id="T-001", title="첫 번째 작업", phase=0),
            Task(id="T-002", title="두 번째 작업", phase=0, depends_on=["T-001"]),
            Task(
                id="T-003",
                title="세 번째 작업",
                phase=1,
                status=TaskStatus.COMPLETED,
            ),
        ]

    def test_get_task(self, sample_tasks):
        """ID로 작업 찾기."""
        todo = TodoList(tasks=sample_tasks)
        task = todo.get_task("T-002")
        assert task is not None
        assert task.title == "두 번째 작업"

        assert todo.get_task("T-999") is None

    def test_get_next_task(self, sample_tasks):
        """다음 작업 가져오기."""
        todo = TodoList(tasks=sample_tasks)

        # T-001이 첫 번째 (의존성 없음)
        next_task = todo.get_next_task()
        assert next_task is not None
        assert next_task.id == "T-001"

        # T-001 완료 후
        todo.mark_completed("T-001")
        next_task = todo.get_next_task()
        assert next_task is not None
        assert next_task.id == "T-002"  # 의존성 충족

    def test_get_next_task_with_blocked(self, sample_tasks):
        """의존성으로 차단된 작업."""
        todo = TodoList(tasks=sample_tasks)

        # T-002는 T-001에 의존하므로 먼저 T-001이 반환됨
        next_task = todo.get_next_task()
        assert next_task.id == "T-001"

    def test_mark_completed(self, sample_tasks):
        """작업 완료 처리."""
        todo = TodoList(tasks=sample_tasks)
        todo.mark_completed("T-001")

        task = todo.get_task("T-001")
        assert task.status == TaskStatus.COMPLETED

        # 존재하지 않는 작업
        todo.mark_completed("T-999")  # 오류 없이 무시

    def test_get_progress(self, sample_tasks):
        """진행 상황 조회."""
        todo = TodoList(tasks=sample_tasks)

        completed, total = todo.get_progress()
        assert completed == 1  # T-003이 이미 완료
        assert total == 3

        todo.mark_completed("T-001")
        completed, total = todo.get_progress()
        assert completed == 2
        assert total == 3

    def test_empty_list(self):
        """빈 목록."""
        todo = TodoList()
        assert todo.get_next_task() is None
        assert todo.get_progress() == (0, 0)


class TestParseTodo:
    """parse_todo 함수 테스트."""

    def test_basic_parsing(self):
        """기본 파싱."""
        content = """# TODO

## Phase 0
- [x] INIT-001: 프로젝트 초기화 (Must)
- [ ] INIT-002: 설정 파일 생성 (Should)

## Phase 1
- [ ] PLAN-001: PRD 작성 (Must)
"""
        todo = parse_todo(content)
        assert len(todo.tasks) == 3

        # 첫 번째 작업
        task = todo.get_task("INIT-001")
        assert task.title == "프로젝트 초기화"
        assert task.status == TaskStatus.COMPLETED
        assert task.priority == "must"
        assert task.phase == 0

        # 두 번째 작업
        task = todo.get_task("INIT-002")
        assert task.status == TaskStatus.PENDING
        assert task.priority == "should"

        # Phase 1 작업
        task = todo.get_task("PLAN-001")
        assert task.phase == 1

    def test_without_priority(self):
        """우선순위 없는 작업."""
        content = """## Phase 0
- [ ] TEST-001: 테스트 작업
"""
        todo = parse_todo(content)
        task = todo.get_task("TEST-001")
        assert task.priority == "must"  # 기본값

    def test_empty_content(self):
        """빈 내용."""
        todo = parse_todo("")
        assert len(todo.tasks) == 0

    def test_case_insensitive_checkbox(self):
        """체크박스 대소문자 무시."""
        content = """## Phase 0
- [X] DONE-001: 완료된 작업 (Must)
- [x] DONE-002: 또 완료된 작업 (Must)
"""
        todo = parse_todo(content)
        assert todo.get_task("DONE-001").status == TaskStatus.COMPLETED
        assert todo.get_task("DONE-002").status == TaskStatus.COMPLETED


class TestParseTree:
    """parse_tree 함수 테스트."""

    def test_basic_parsing(self):
        """기본 파싱."""
        content = """# 프로젝트 구조

```
project/
├── src/
│   ├── main.py
│   └── utils.py
├── tests/
│   └── test_main.py
└── README.md
```
"""
        paths = parse_tree(content)
        assert "project/" in paths
        assert "src/" in paths
        assert "main.py" in paths
        assert "README.md" in paths

    def test_with_comments(self):
        """주석 포함."""
        content = """```
src/
├── app.py  # 메인 애플리케이션
└── config.py  # 설정 파일
```
"""
        paths = parse_tree(content)
        assert "app.py" in paths
        assert "config.py" in paths
        # 주석은 제외되어야 함
        assert "# 메인 애플리케이션" not in paths

    def test_empty_content(self):
        """빈 내용."""
        paths = parse_tree("")
        assert paths == []

    def test_no_code_block(self):
        """코드 블록 없음."""
        content = """# 설명

그냥 텍스트입니다.
"""
        paths = parse_tree(content)
        assert paths == []
