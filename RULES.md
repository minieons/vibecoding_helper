# Vibe Coding Helper - 코딩 규칙 (RULES.md)

## 1. 코드 스타일

### 1.1 일반 원칙
- **함수형 + 클래스 혼합**: Provider, Handler 등 상태를 가진 컴포넌트는 클래스, 유틸리티는 순수 함수
- **명시적 타입 힌트**: 모든 함수 시그니처에 타입 힌트 필수
- **Docstring**: 공개 API에는 Google 스타일 docstring 작성
- **최대 줄 길이**: 100자 (ruff 설정)

### 1.2 네이밍 컨벤션
```python
# 클래스: PascalCase
class AIProvider:
    pass

class ContextManager:
    pass

# 함수/메서드: snake_case
def load_config() -> Config:
    pass

async def generate_response() -> str:
    pass

# 상수: SCREAMING_SNAKE_CASE
DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
MAX_TOKENS = 100000

# 프라이빗: 언더스코어 접두사
def _internal_helper():
    pass

class Provider:
    def _validate_response(self):
        pass
```

### 1.3 파일 구조
```python
# 파일 상단 순서
"""
모듈 docstring (선택)
"""

# 1. Future imports (필요시)
from __future__ import annotations

# 2. 표준 라이브러리
import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

# 3. 서드파티
from pydantic import BaseModel
from rich.console import Console

# 4. 로컬
from vibe.core.config import Config

# 5. TYPE_CHECKING 블록 (순환 참조 방지)
if TYPE_CHECKING:
    from vibe.providers.base import AIProvider

# 6. 상수
DEFAULT_TIMEOUT = 30

# 7. 클래스/함수 정의
...
```

## 2. 아키텍처 규칙

### 2.1 레이어 분리
```
CLI Layer (cli/)
    ↓ 호출만
Core Layer (core/)
    ↓ 호출만
Provider/Handler Layer (providers/, handlers/)
```

- **상위 → 하위만 참조**: CLI는 Core만, Core는 Provider/Handler만 참조
- **순환 참조 금지**: TYPE_CHECKING으로 타입 힌트만 허용

### 2.2 의존성 주입
```python
# Good: 의존성 주입
class Workflow:
    def __init__(self, provider: AIProvider, file_handler: FileHandler):
        self.provider = provider
        self.file_handler = file_handler

# Bad: 내부에서 직접 생성
class Workflow:
    def __init__(self):
        self.provider = AnthropicProvider()  # 테스트 어려움
```

### 2.3 에러 처리
```python
# 커스텀 예외 계층
class VibeError(Exception):
    """기본 예외 클래스"""
    pass

class ConfigError(VibeError):
    """설정 관련 에러"""
    pass

class ProviderError(VibeError):
    """AI Provider 에러"""
    pass

class FileError(VibeError):
    """파일 시스템 에러"""
    pass

# 사용
def load_config(path: Path) -> Config:
    if not path.exists():
        raise ConfigError(f"설정 파일을 찾을 수 없습니다: {path}")
```

## 3. Provider 인터페이스

### 3.1 추상 기반 클래스
```python
from abc import ABC, abstractmethod

class AIProvider(ABC):
    """AI Provider 추상 기반 클래스"""

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> Response:
        """응답 생성"""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
    ) -> AsyncIterator[str]:
        """스트리밍 응답"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider 이름"""
        pass
```

### 3.2 구현 규칙
- 모든 Provider는 `AIProvider`를 상속
- API 키는 환경변수 또는 설정에서 로드 (하드코딩 금지)
- 재시도 로직은 Provider 내부에서 처리 (exponential backoff)

## 4. 설정 관리

### 4.1 Pydantic 모델 사용
```python
from pydantic import BaseModel, Field

class VibeConfig(BaseModel):
    """프로젝트 설정"""
    project_name: str
    project_type: str = "backend"
    provider: str = "anthropic"
    model: str | None = None
    auto_commit: bool = True
    language: str = "ko"
    token_budget: int = Field(default=100000, ge=1000)

    class Config:
        extra = "forbid"  # 알 수 없는 필드 에러
```

### 4.2 환경변수 우선순위
```
1. CLI 인자 (--provider anthropic)
2. 환경변수 (VIBE_PROVIDER)
3. 프로젝트 설정 (.vibe/config.yaml)
4. 전역 설정 (~/.config/vibe/config.yaml)
5. 기본값
```

## 5. 비동기 처리

### 5.1 async/await 일관성
```python
# Provider 메서드는 모두 async
async def generate(self, messages: list[Message]) -> Response:
    pass

# CLI 진입점에서 asyncio.run 사용
def main():
    asyncio.run(async_main())
```

### 5.2 동시성 제한
```python
import asyncio

# 동시 API 호출 제한
semaphore = asyncio.Semaphore(3)

async def rate_limited_call():
    async with semaphore:
        return await provider.generate(messages)
```

## 6. 테스트 규칙

### 6.1 테스트 구조
```
tests/
├── unit/           # 외부 의존성 모킹
├── integration/    # 실제 파일 시스템, 모킹된 API
└── fixtures/       # 공유 픽스처
```

### 6.2 테스트 네이밍
```python
# test_<모듈명>.py
# test_<기능>_<시나리오>

def test_load_config_returns_default_when_file_missing():
    pass

def test_generate_raises_error_on_invalid_api_key():
    pass

async def test_stream_yields_chunks_correctly():
    pass
```

### 6.3 픽스처 사용
```python
import pytest

@pytest.fixture
def mock_provider():
    """모킹된 AI Provider"""
    ...

@pytest.fixture
def temp_project(tmp_path):
    """임시 프로젝트 디렉토리"""
    ...
```

## 7. 문서화 규칙

### 7.1 Docstring 스타일 (Google)
```python
def generate_prd(
    description: str,
    context: ProjectContext,
) -> str:
    """PRD 문서를 생성합니다.

    Args:
        description: 프로젝트 설명
        context: 프로젝트 컨텍스트 (TECH_STACK, RULES 포함)

    Returns:
        생성된 PRD 마크다운 문자열

    Raises:
        ProviderError: API 호출 실패 시
        ConfigError: 설정이 올바르지 않을 때

    Example:
        >>> prd = generate_prd("날씨 API 서버", context)
        >>> print(prd[:50])
        '# Product Requirements Document...'
    """
    pass
```

### 7.2 주석 원칙
- **왜(Why)** 를 설명하는 주석만 작성
- 코드가 **무엇(What)** 을 하는지는 코드 자체로 표현
- TODO 주석은 이슈 번호와 함께: `# TODO(#123): 토큰 카운팅 최적화`

## 8. Git 규칙

### 8.1 커밋 메시지
```
<type>: <subject>

<body>

<footer>
```

**타입:**
- `feat`: 새 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 포매팅 (코드 변경 없음)
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드, 설정 변경

**예시:**
```
feat: vibe init 명령어 구현

- TECH_STACK.md 생성 로직
- RULES.md 템플릿 적용
- 대화형 인터뷰 플로우

Closes #12
```

### 8.2 브랜치 전략
```
main                 # 안정 버전
├── develop          # 개발 통합
│   ├── feat/init-command
│   ├── feat/plan-phase
│   └── fix/config-loading
```

## 9. 보안 규칙

### 9.1 API 키 처리
- **절대** 코드나 설정 파일에 하드코딩 금지
- 환경변수 (`ANTHROPIC_API_KEY`) 또는 시스템 키체인 사용
- `.gitignore`에 `.env`, `*.key` 패턴 추가

### 9.2 파일 시스템 보안
- 프로젝트 디렉토리 외부 파일 접근 차단
- 사용자 입력 경로는 항상 검증 (`Path.resolve()` 후 상위 디렉토리 체크)

### 9.3 생성 코드 검증
- SQL Injection, XSS 등 취약점 패턴 감지 경고
- 민감 정보 하드코딩 감지 (정규식 기반)
