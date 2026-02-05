# 테스트 가이드

## 테스트 구조

```
tests/
├── conftest.py              # 공통 픽스처
├── unit/                    # 단위 테스트
│   ├── test_config.py       # config 모듈 테스트
│   ├── test_state.py        # state 모듈 테스트
│   ├── test_parser.py       # parser 모듈 테스트
│   └── providers/
│       └── test_base.py     # Provider 기본 클래스 테스트
└── integration/             # 통합 테스트
    └── test_init_flow.py    # init 워크플로우 테스트
```

## 환경 설정

### 1. 개발 의존성 설치

```bash
# pip 사용
pip install -e ".[dev]"

# 또는 uv 사용
uv pip install -e ".[dev]"

# 또는 Make 사용
make dev
```

### 2. 가상환경 권장

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 또는
.venv\Scripts\activate     # Windows

pip install -e ".[dev]"
```

## 테스트 실행

### 기본 실행

```bash
# 전체 테스트
pytest

# 또는
make test
```

### 선택적 실행

```bash
# 단위 테스트만
pytest tests/unit/
make test-unit

# 통합 테스트만
pytest tests/integration/
make test-int

# 특정 파일
pytest tests/unit/test_config.py

# 특정 클래스
pytest tests/unit/test_config.py::TestVibeConfig

# 특정 테스트
pytest tests/unit/test_config.py::TestVibeConfig::test_defaults
```

### 상세 출력

```bash
# 상세 모드
pytest -v

# 더 상세한 출력
pytest -vv

# 실패 시 즉시 중단
pytest -x

# 처음 3개 실패만 표시
pytest --maxfail=3
```

## 커버리지

### 커버리지 리포트 생성

```bash
# 터미널 출력
pytest --cov=src/vibe

# HTML 리포트 생성
pytest --cov=src/vibe --cov-report=html
make test-cov

# 리포트 확인
open htmlcov/index.html  # macOS
```

### 커버리지 목표

| 모듈 | 목표 커버리지 |
|------|--------------|
| core/ | 90% |
| handlers/ | 80% |
| providers/ | 70% |
| cli/ | 60% |

## 테스트 작성 가이드

### 테스트 명명 규칙

```python
# 클래스: Test + 테스트 대상
class TestVibeConfig:
    # 메서드: test_ + 동작 설명
    def test_defaults(self):
        ...

    def test_save_and_load(self):
        ...

    def test_invalid_input_raises_error(self):
        ...
```

### 픽스처 사용

```python
import pytest

@pytest.fixture
def sample_config():
    """테스트용 설정."""
    return VibeConfig(project_name="test")

def test_with_fixture(sample_config):
    assert sample_config.project_name == "test"
```

### 공통 픽스처 (conftest.py)

```python
# tests/conftest.py에 정의된 픽스처
- temp_project: 임시 프로젝트 디렉토리
- vibe_dir: .vibe 디렉토리
- sample_config: 샘플 설정 파일
```

### 비동기 테스트

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### 예외 테스트

```python
import pytest

def test_raises_error():
    with pytest.raises(ConfigError) as exc_info:
        load_config()
    assert exc_info.value.code == "E001"
```

### 파라미터화 테스트

```python
import pytest

@pytest.mark.parametrize("project_type", [
    "backend", "frontend", "fullstack", "cli", "library"
])
def test_project_types(project_type):
    config = VibeConfig(project_name="test", project_type=project_type)
    assert config.project_type == project_type
```

## 마커 (Markers)

### 사용 가능한 마커

```python
@pytest.mark.slow       # 느린 테스트
@pytest.mark.asyncio    # 비동기 테스트
@pytest.mark.integration # 통합 테스트
```

### 마커로 필터링

```bash
# 느린 테스트 제외
pytest -m "not slow"

# 비동기 테스트만
pytest -m asyncio
```

## CI/CD 통합

### GitHub Actions 예시

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: pip install -e ".[dev]"

    - name: Run tests
      run: pytest --cov=src/vibe --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v4
```

## 문제 해결

### pytest를 찾을 수 없음

```bash
# 개발 의존성 설치
pip install -e ".[dev]"
```

### 모듈 import 오류

```bash
# 패키지 재설치
pip install -e .
```

### 비동기 테스트 실패

```bash
# pytest-asyncio 설치 확인
pip install pytest-asyncio
```

## 테스트 체크리스트

새 기능 추가 시:

- [ ] 단위 테스트 작성
- [ ] 엣지 케이스 테스트
- [ ] 에러 케이스 테스트
- [ ] 필요시 통합 테스트
- [ ] 커버리지 80% 이상 유지
- [ ] 모든 테스트 통과 확인
