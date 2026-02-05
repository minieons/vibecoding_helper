# Vibe Coding Helper - 스키마 정의 (SCHEMA.md)

## 1. CLI 인터페이스

### 1.1 명령어 구조
```
vibe [OPTIONS] COMMAND [ARGS]

전역 옵션:
  --provider, -p TEXT    AI Provider 선택 [anthropic|google|openai]
  --model, -m TEXT       모델 지정 (예: claude-4-5-opus)
  --verbose, -v          상세 로그 출력
  --dry-run              파일 변경 없이 미리보기만
  --yes, -y              모든 확인 프롬프트 자동 승인
  --dual-mode            듀얼 모델 활성화 (Claude + Gemini 협업)
  --version              버전 정보 표시
  --help                 도움말 표시
```

### 1.2 명령어 상세

#### `vibe init`
```
vibe init [OPTIONS] [DESCRIPTION]

인자:
  DESCRIPTION    프로젝트 설명 (선택, 없으면 대화형)

옵션:
  --type, -t TEXT    프로젝트 유형 [backend|frontend|cli|library]
  --force, -f        기존 설정 덮어쓰기

출력:
  - TECH_STACK.md
  - RULES.md
  - .vibe/config.yaml
  - .vibe/state.json
```

#### `vibe plan`
```
vibe plan [OPTIONS]

옵션:
  --review, -r    기존 PRD 검토 및 수정 모드

출력:
  - PRD.md
  - USER_STORIES.md
```

#### `vibe design`
```
vibe design [OPTIONS]

옵션:
  --skip-review    생성 후 검토 건너뛰기

출력:
  - TREE.md
  - SCHEMA.md
```

#### `vibe scaffold`
```
vibe scaffold [OPTIONS]

옵션:
  --tree PATH      사용할 TREE.md 경로 (기본: ./TREE.md)
  --force, -f      기존 파일 덮어쓰기

출력:
  - 디렉토리 및 파일 생성
  - TODO.md
```

#### `vibe code`
```
vibe code [OPTIONS] [TASK_ID]

인자:
  TASK_ID    작업 ID (선택, 없으면 다음 작업 자동 선택)

옵션:
  --file, -f PATH    특정 파일만 처리
  --all, -a          모든 미완료 작업 연속 처리

출력:
  - 소스 코드 파일
  - TODO.md 업데이트
  - CONTEXT.md 업데이트
  - Git 커밋 (auto_commit 설정 시)
```

#### `vibe status`
```
vibe status [OPTIONS]

옵션:
  --json    JSON 형식으로 출력

출력: (stdout)
  현재 Phase, 진행률, 마지막 작업 정보
```

#### `vibe chat`
```
vibe chat [OPTIONS]

옵션:
  --context, -c    프로젝트 컨텍스트 포함 여부 (기본: true)

입력: 대화형
출력: AI 응답 (파일 변경 없음)
```

#### `vibe undo`
```
vibe undo [OPTIONS]

옵션:
  --steps, -n INT    되돌릴 작업 수 (기본: 1)

출력:
  - Git revert
  - 상태 파일 복구
```

#### `vibe test` (Phase 4)
```
vibe test [OPTIONS]

옵션:
  --audit              Gemini를 사용한 전역 감사 실행
  --edge-cases         Claude를 사용한 엣지 케이스 생성
  --coverage           테스트 커버리지 분석
  --all, -a            모든 테스트 실행

출력:
  - 테스트 결과 리포트
  - 감사 리포트 (--audit 시)
  - 엣지 케이스 목록 (--edge-cases 시)
```

---

## 2. 데이터 모델 (Pydantic)

### 2.1 설정 모델

```python
# core/config.py

class DualModelConfig(BaseModel):
    """듀얼 모델 설정"""
    enabled: bool = True
    main_provider: Literal["anthropic", "openai"] = "anthropic"
    main_model: str = "claude-4-5-opus"
    knowledge_provider: Literal["google"] = "google"
    knowledge_model: str = "gemini-3-pro"


class VibeConfig(BaseModel):
    """프로젝트 설정 (.vibe/config.yaml)"""
    project_name: str
    project_type: Literal["backend", "frontend", "fullstack", "cli", "library"] = "backend"

    # 듀얼 모델 설정 (2026 전략)
    dual_mode: DualModelConfig = Field(default_factory=DualModelConfig)

    # 레거시 호환 (단일 모델 모드)
    provider: Literal["anthropic", "google", "openai"] = "anthropic"
    model: str | None = None

    auto_commit: bool = True
    language: Literal["ko", "en"] = "ko"
    token_budget: int = Field(default=100000, ge=1000, le=500000)

    model_config = ConfigDict(extra="forbid")


class GlobalConfig(BaseModel):
    """전역 설정 (~/.config/vibe/config.yaml)"""
    default_provider: str = "anthropic"
    default_language: str = "ko"
    dual_mode_enabled: bool = True
    api_keys: dict[str, str] = Field(default_factory=dict)  # 암호화 필요
```

### 2.2 상태 모델

```python
# core/state.py

class PhaseStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class LastAction(BaseModel):
    """마지막 작업 정보"""
    command: str
    timestamp: datetime
    files_created: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    git_commit: str | None = None


class VibeState(BaseModel):
    """프로젝트 상태 (.vibe/state.json)"""
    current_phase: int = Field(ge=0, le=4)  # Phase 0-4 (Test 포함)
    phase_status: dict[str, PhaseStatus]
    last_action: LastAction | None = None
    git_enabled: bool = False
    dual_mode_active: bool = True  # 듀얼 모델 활성화 여부
    created_at: datetime
    updated_at: datetime = Field(default_factory=datetime.now)
```

### 2.3 컨텍스트 모델

```python
# core/context.py

class Message(BaseModel):
    """AI 대화 메시지"""
    role: Literal["system", "user", "assistant"]
    content: str


class HotMemory(BaseModel):
    """Hot Memory - Claude용 현재 작업 컨텍스트"""
    current_file: str | None = None    # 현재 작업 중인 파일
    rules: str | None = None           # RULES.md (항상 포함)
    recent_changes: list[str] = Field(default_factory=list)  # 최근 변경 파일 목록


class ColdStorage(BaseModel):
    """Cold Storage - Gemini용 전체 프로젝트 컨텍스트"""
    full_codebase: dict[str, str] = Field(default_factory=dict)  # 전체 소스 코드
    external_docs: list[str] = Field(default_factory=list)  # 외부 문서 URL
    library_docs: dict[str, str] = Field(default_factory=dict)  # 라이브러리 문서


class DualTrackContext(BaseModel):
    """Dual-Track Context (듀얼 모델용)"""
    hot: HotMemory = Field(default_factory=HotMemory)
    cold: ColdStorage = Field(default_factory=ColdStorage)

    def get_claude_context(self) -> str:
        """Claude용 컨텍스트 (Hot Memory)"""
        ...

    def get_gemini_context(self) -> str:
        """Gemini용 컨텍스트 (Cold Storage)"""
        ...


class ProjectContext(BaseModel):
    """프로젝트 컨텍스트 (AI에게 전달)"""
    tech_stack: str | None = None      # TECH_STACK.md 내용
    rules: str | None = None           # RULES.md 내용
    prd: str | None = None             # PRD.md 내용
    schema: str | None = None          # SCHEMA.md 내용
    tree: str | None = None            # TREE.md 내용
    todo: str | None = None            # TODO.md 내용
    related_files: dict[str, str] = Field(default_factory=dict)  # 관련 코드 파일

    # 듀얼 모델용 컨텍스트
    dual_track: DualTrackContext | None = None

    def to_context_string(self) -> str:
        """컨텍스트를 문자열로 변환"""
        ...

    def estimate_tokens(self) -> int:
        """토큰 수 추정"""
        ...
```

### 2.4 TODO 모델

```python
# handlers/parser.py

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class Task(BaseModel):
    """TODO 작업 항목"""
    id: str                           # 예: "INIT-001"
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    priority: Literal["must", "should", "could"] = "must"
    phase: int = Field(ge=0, le=4)    # Phase 0-4 (Test 포함)
    files: list[str] = Field(default_factory=list)  # 관련 파일
    depends_on: list[str] = Field(default_factory=list)  # 의존 작업 ID
    user_story: str | None = None     # 관련 User Story ID
    assigned_model: Literal["claude", "gemini", "both"] | None = None  # 담당 모델


class TodoList(BaseModel):
    """TODO.md 파싱 결과"""
    tasks: list[Task]

    def get_next_task(self) -> Task | None:
        """다음 실행할 작업 반환"""
        ...

    def mark_completed(self, task_id: str) -> None:
        """작업 완료 처리"""
        ...
```

### 2.5 Provider 응답 모델

```python
# providers/base.py

class Usage(BaseModel):
    """토큰 사용량"""
    input_tokens: int
    output_tokens: int


class Response(BaseModel):
    """AI 응답"""
    content: str
    model: str
    usage: Usage
    stop_reason: str | None = None


class StreamChunk(BaseModel):
    """스트리밍 청크"""
    content: str
    is_final: bool = False
```

---

## 3. 파일 형식

### 3.1 `.vibe/config.yaml`
```yaml
project_name: "my-project"
project_type: "backend"

# 듀얼 모델 설정 (2026 전략)
dual_mode:
  enabled: true
  main_provider: "anthropic"
  main_model: "claude-4-5-opus"
  knowledge_provider: "google"
  knowledge_model: "gemini-3-pro"

# 레거시 호환 (단일 모델)
provider: "anthropic"
model: "claude-4-5-opus"

auto_commit: true
language: "ko"
token_budget: 100000
```

### 3.2 `.vibe/state.json`
```json
{
  "current_phase": 2,
  "phase_status": {
    "0": "completed",
    "1": "completed",
    "2": "in_progress",
    "3": "pending",
    "4": "pending"
  },
  "last_action": {
    "command": "design",
    "timestamp": "2026-02-03T10:30:00Z",
    "files_created": ["TREE.md", "SCHEMA.md"],
    "files_modified": [],
    "git_commit": "abc1234",
    "model_used": "claude-4-5-opus"
  },
  "git_enabled": true,
  "dual_mode_active": true,
  "created_at": "2026-02-03T09:00:00Z",
  "updated_at": "2026-02-03T10:30:00Z"
}
```

### 3.3 `TODO.md` 형식
```markdown
# TODO

## Phase 0: 초기화
- [x] INIT-001: 프로젝트 설정 파일 생성 (Must)
- [x] INIT-002: Git 초기화 (Should)

## Phase 1: 기획
- [x] PLAN-001: PRD 문서 생성 (Must)
- [x] PLAN-002: User Story 도출 (Must)

## Phase 2: 설계
- [x] DESIGN-001: 프로젝트 구조 설계 (Must)
- [ ] DESIGN-002: 스키마 설계 (Must)

## Phase 3: 구현
- [ ] CODE-001: CLI 진입점 구현 (Must)
  - 파일: src/vibe/main.py
  - 의존: DESIGN-001
- [ ] CODE-002: 설정 모듈 구현 (Must)
  - 파일: src/vibe/core/config.py
  - 의존: CODE-001
```

---

## 4. 환경변수

| 변수 | 설명 | 기본값 |
|-----|------|-------|
| `ANTHROPIC_API_KEY` | Anthropic API 키 | - |
| `GOOGLE_API_KEY` | Google AI API 키 | - |
| `OPENAI_API_KEY` | OpenAI API 키 | - |
| `VIBE_PROVIDER` | 기본 Provider | anthropic |
| `VIBE_MODEL` | 기본 모델 | - |
| `VIBE_CONFIG_DIR` | 전역 설정 디렉토리 | ~/.config/vibe |
| `VIBE_DEBUG` | 디버그 모드 | false |

---

## 5. 에러 코드

| 코드 | 이름 | 설명 |
|-----|------|------|
| E001 | `ConfigNotFound` | 설정 파일 없음 |
| E002 | `ConfigInvalid` | 설정 파일 형식 오류 |
| E003 | `StateCorrupted` | 상태 파일 손상 |
| E010 | `ProviderNotConfigured` | API 키 미설정 |
| E011 | `ProviderRateLimit` | API 호출 한도 초과 |
| E012 | `ProviderTimeout` | API 응답 시간 초과 |
| E020 | `FileNotFound` | 파일 없음 |
| E021 | `FilePermission` | 파일 권한 오류 |
| E030 | `GitNotInitialized` | Git 저장소 아님 |
| E031 | `GitDirtyState` | 커밋되지 않은 변경사항 |
| E040 | `PhaseNotReady` | 이전 Phase 미완료 |
| E041 | `TaskDependencyUnmet` | 의존 작업 미완료 |
