"""컨텍스트 수집 및 토큰 관리.

Dual-Track Context 전략:
- Hot Memory (Claude): 현재 작업 파일 + 핵심 규칙
- Cold Storage (Gemini): 전체 코드베이스 + 외부 문서
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """AI 대화 메시지."""

    role: Literal["system", "user", "assistant"]
    content: str


# =============================================================================
# Dual-Track Context (듀얼 모델용)
# =============================================================================


class HotMemory(BaseModel):
    """Hot Memory - Claude용 현재 작업 컨텍스트.

    Claude의 제한된 컨텍스트 윈도우에 맞춰 핵심 정보만 포함.
    """

    current_file: Optional[str] = None  # 현재 작업 중인 파일 경로
    current_file_content: Optional[str] = None  # 현재 파일 내용
    rules: Optional[str] = None  # RULES.md (항상 포함)
    recent_changes: list[str] = Field(default_factory=list)  # 최근 변경 파일 목록
    task_context: Optional[str] = None  # 현재 작업 설명

    def to_prompt(self) -> str:
        """Claude용 프롬프트로 변환."""
        sections = []

        if self.rules:
            sections.append(f"## 코딩 규칙\n{self.rules}")

        if self.task_context:
            sections.append(f"## 현재 작업\n{self.task_context}")

        if self.current_file and self.current_file_content:
            sections.append(
                f"## 작업 파일: {self.current_file}\n```\n{self.current_file_content}\n```"
            )

        if self.recent_changes:
            sections.append(
                "## 최근 변경된 파일\n" + "\n".join(f"- {f}" for f in self.recent_changes)
            )

        return "\n\n".join(sections)

    def estimate_tokens(self) -> int:
        """토큰 수 추정."""
        return len(self.to_prompt()) // 4


class ColdStorage(BaseModel):
    """Cold Storage - Gemini용 전체 프로젝트 컨텍스트.

    Gemini의 무한 컨텍스트를 활용하여 전체 프로젝트 정보 저장.
    """

    full_codebase: dict[str, str] = Field(default_factory=dict)  # 전체 소스 코드
    external_docs: list[str] = Field(default_factory=list)  # 외부 문서 URL
    library_docs: dict[str, str] = Field(default_factory=dict)  # 라이브러리 문서
    project_docs: dict[str, str] = Field(default_factory=dict)  # PRD, SCHEMA 등

    def to_prompt(self) -> str:
        """Gemini용 프롬프트로 변환."""
        sections = []

        if self.project_docs:
            for name, content in self.project_docs.items():
                sections.append(f"## {name}\n{content}")

        if self.full_codebase:
            code_section = "## 전체 코드베이스\n"
            for path, content in self.full_codebase.items():
                code_section += f"### {path}\n```\n{content}\n```\n\n"
            sections.append(code_section)

        if self.library_docs:
            lib_section = "## 라이브러리 문서\n"
            for lib, doc in self.library_docs.items():
                lib_section += f"### {lib}\n{doc}\n\n"
            sections.append(lib_section)

        return "\n\n".join(sections)

    def get_file_count(self) -> int:
        """코드베이스 파일 수."""
        return len(self.full_codebase)


class DualTrackContext(BaseModel):
    """Dual-Track Context - 듀얼 모델 협업용 컨텍스트.

    Hot Memory는 Claude에게, Cold Storage는 Gemini에게 전달.
    """

    hot: HotMemory = Field(default_factory=HotMemory)
    cold: ColdStorage = Field(default_factory=ColdStorage)

    def get_claude_context(self) -> str:
        """Claude용 컨텍스트 (Hot Memory)."""
        return self.hot.to_prompt()

    def get_gemini_context(self) -> str:
        """Gemini용 컨텍스트 (Cold Storage)."""
        return self.cold.to_prompt()

    def inject_knowledge(self, knowledge: str) -> None:
        """Gemini로부터 받은 지식을 Hot Memory에 주입."""
        if self.hot.task_context:
            self.hot.task_context += f"\n\n[Gemini 분석]\n{knowledge}"
        else:
            self.hot.task_context = f"[Gemini 분석]\n{knowledge}"


# =============================================================================
# 기본 프로젝트 컨텍스트 (레거시 호환)
# =============================================================================


class ProjectContext(BaseModel):
    """프로젝트 컨텍스트."""

    tech_stack: Optional[str] = None
    rules: Optional[str] = None
    prd: Optional[str] = None
    schema: Optional[str] = None
    tree: Optional[str] = None
    todo: Optional[str] = None
    context_md: Optional[str] = None
    related_files: dict[str, str] = Field(default_factory=dict)

    # 듀얼 모델용 컨텍스트 (선택적)
    dual_track: Optional[DualTrackContext] = None

    def to_context_string(self) -> str:
        """컨텍스트를 문자열로 변환."""
        sections = []

        if self.rules:
            sections.append(f"## 코딩 규칙 (RULES.md)\n{self.rules}")

        if self.tech_stack:
            sections.append(f"## 기술 스택 (TECH_STACK.md)\n{self.tech_stack}")

        if self.prd:
            sections.append(f"## 요구사항 (PRD.md)\n{self.prd}")

        if self.schema:
            sections.append(f"## 스키마 (SCHEMA.md)\n{self.schema}")

        if self.tree:
            sections.append(f"## 프로젝트 구조 (TREE.md)\n{self.tree}")

        if self.todo:
            sections.append(f"## TODO (TODO.md)\n{self.todo}")

        if self.related_files:
            files_section = "## 관련 파일\n"
            for filepath, content in self.related_files.items():
                files_section += f"### {filepath}\n```\n{content}\n```\n"
            sections.append(files_section)

        return "\n\n".join(sections)

    def estimate_tokens(self) -> int:
        """토큰 수 추정 (대략 4문자 = 1토큰)."""
        total_chars = len(self.to_context_string())
        return total_chars // 4


def load_project_context(project_root: Optional[Path] = None) -> ProjectContext:
    """프로젝트 컨텍스트 로드."""
    if project_root is None:
        project_root = Path.cwd()

    ctx = ProjectContext()

    files = {
        "tech_stack": "TECH_STACK.md",
        "rules": "RULES.md",
        "prd": "PRD.md",
        "schema": "SCHEMA.md",
        "tree": "TREE.md",
        "todo": "TODO.md",
        "context_md": "CONTEXT.md",
    }

    for attr, filename in files.items():
        filepath = project_root / filename
        if filepath.exists():
            setattr(ctx, attr, filepath.read_text(encoding="utf-8"))

    return ctx


def load_dual_track_context(
    project_root: Optional[Path] = None,
    current_file: Optional[str] = None,
    include_codebase: bool = True,
) -> DualTrackContext:
    """Dual-Track Context 로드.

    Args:
        project_root: 프로젝트 루트 경로
        current_file: 현재 작업 중인 파일 경로
        include_codebase: 전체 코드베이스 포함 여부

    Returns:
        DualTrackContext 인스턴스
    """
    if project_root is None:
        project_root = Path.cwd()

    # Hot Memory (Claude용)
    hot = HotMemory()

    # RULES.md는 항상 포함
    rules_path = project_root / "RULES.md"
    if rules_path.exists():
        hot.rules = rules_path.read_text(encoding="utf-8")

    # 현재 작업 파일
    if current_file:
        file_path = project_root / current_file
        if file_path.exists():
            hot.current_file = current_file
            hot.current_file_content = file_path.read_text(encoding="utf-8")

    # Cold Storage (Gemini용)
    cold = ColdStorage()

    # 프로젝트 문서
    doc_files = {
        "TECH_STACK.md": "기술 스택",
        "PRD.md": "제품 요구사항",
        "SCHEMA.md": "스키마",
        "TREE.md": "프로젝트 구조",
        "TODO.md": "작업 목록",
    }

    for filename, title in doc_files.items():
        filepath = project_root / filename
        if filepath.exists():
            cold.project_docs[title] = filepath.read_text(encoding="utf-8")

    # 전체 코드베이스 (선택적)
    if include_codebase:
        src_dir = project_root / "src"
        if src_dir.exists():
            for py_file in src_dir.rglob("*.py"):
                relative_path = py_file.relative_to(project_root)
                try:
                    cold.full_codebase[str(relative_path)] = py_file.read_text(
                        encoding="utf-8"
                    )
                except Exception:
                    pass  # 읽기 실패한 파일은 스킵

    return DualTrackContext(hot=hot, cold=cold)


def get_context_for_phase(
    phase: int,
    project_root: Optional[Path] = None,
    dual_mode: bool = False,
) -> ProjectContext | DualTrackContext:
    """Phase별 적절한 컨텍스트 반환.

    Args:
        phase: 현재 Phase (0-4)
        project_root: 프로젝트 루트
        dual_mode: 듀얼 모델 모드 여부

    Returns:
        Phase에 맞는 컨텍스트
    """
    if dual_mode:
        ctx = load_dual_track_context(project_root)

        # Phase별 Hot Memory 조정
        if phase == 0:
            # Init: 최소 컨텍스트
            ctx.hot.rules = None
        elif phase in (1, 2):
            # Plan/Design: 규칙 + 문서
            pass
        elif phase == 3:
            # Code: 규칙 + 현재 파일
            pass
        elif phase == 4:
            # Test: 전체 컨텍스트 필요
            pass

        return ctx
    else:
        return load_project_context(project_root)
