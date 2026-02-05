# Vibe Coding Helper

AI 기반 문서 주도 개발(Document-Driven Development) CLI 도구

개발자의 막연한 아이디어("Vibe")를 체계적인 문서와 실행 가능한 코드로 변환합니다.

## 특징

- **Document-Driven**: 모든 개발 단계를 문서(Artifact)로 기록
- **Phase-Based Workflow**: 초기화 → 기획 → 설계 → 구현 → 테스트의 단계별 진행
- **Dual Model Strategy**: Claude(Main Agent) + Gemini(Knowledge Engine) 협업
- **Self-Healing**: 코드 생성 후 자동 검증 및 수정
- **Multi-Language Support**: Python, TypeScript, JavaScript, Java, Flutter/Dart 검증 지원

## 설치

### 요구사항

- Python 3.10 이상
- AI Provider API 키 (Anthropic, Google, OpenAI 중 최소 하나)

### pip으로 설치

```bash
pip install vibe-coding-helper
```

### 개발 환경 설치

```bash
# 저장소 클론
git clone https://github.com/vibe-team/vibe-coding-helper.git
cd vibe-coding-helper

## 빠른 시작

### 1. API 키 설정

```bash
# 환경 변수로 설정
export ANTHROPIC_API_KEY="your-api-key"
export GOOGLE_API_KEY="your-api-key"
export OPENAI_API_KEY="your-api-key"
```

### 2. 프로젝트 초기화

```bash
# 새 프로젝트 디렉토리에서
mkdir my-project && cd my-project

# 프로젝트 초기화
vibe init
```

### 3. 개발 워크플로우

```bash
# Phase 1: 기획 - PRD, User Stories 생성
vibe plan

# Phase 2: 설계 - TREE.md, SCHEMA.md 생성
vibe design

# Phase 2: 스캐폴딩 - 디렉토리/파일 구조 생성
vibe scaffold

# Phase 3: 코드 구현
vibe code

# Phase 4: 테스트 - 전역 감사 및 엣지 케이스 생성
vibe test
```

## 명령어

| 명령어 | 설명 | Phase |
|--------|------|-------|
| `vibe init` | 프로젝트 초기화, 기술 스택 설정 | 0 |
| `vibe plan` | PRD, User Stories 생성 | 1 |
| `vibe design` | TREE.md, SCHEMA.md 생성 | 2 |
| `vibe scaffold` | 디렉토리/파일 구조 생성 | 2 |
| `vibe code` | TODO.md 기반 코드 구현 | 3 |
| `vibe test` | 전역 감사, 엣지 케이스 생성 | 4 |
| `vibe verify` | 코드 검증 (문법, 타입, 린트) | - |
| `vibe status` | 현재 진행 상황 표시 | - |
| `vibe chat` | 자유 대화 모드 | - |
| `vibe undo` | 마지막 작업 롤백 (Git 기반) | - |

## 생성되는 문서

| 문서 | 역할 | 생성 Phase |
|------|------|------------|
| `TECH_STACK.md` | 기술 스택 정의 | Phase 0 |
| `RULES.md` | 코딩 규칙 정의 | Phase 0 |
| `PRD.md` | 제품 요구사항 | Phase 1 |
| `USER_STORIES.md` | 사용자 스토리 | Phase 1 |
| `TREE.md` | 디렉토리 구조 | Phase 2 |
| `SCHEMA.md` | 데이터/API 스키마 | Phase 2 |
| `TODO.md` | 작업 목록 | Phase 2 |

## 아키텍처

### Dual Model Strategy

```
Phase 0 (Init)     →  [Gemini 단독]
                      사용자 의도 파악, 기술 스택 제안

Phase 1 (Plan)     →  [Gemini] → [Claude]
                      컨텍스트 분석    PRD 작성

Phase 2 (Design)   →  [Claude] → [Gemini]
                      아키텍처 설계    라이브러리 검증

Phase 3 (Code)     →  [Claude] ↔ [Gemini]
                      자율 코딩        컨텍스트 주입
                          ↓
                     [Verifier] → [Self-Healing]
                      자동 검증        자동 수정

Phase 4 (Test)     →  [Gemini] + [Claude]
                      전역 감사    엣지 케이스 생성
```

### 검증기 시스템

| 언어 | 검증 도구 |
|------|----------|
| Python | ast, mypy, ruff, pytest |
| TypeScript | tsc, eslint, vitest/jest |
| JavaScript | node --check, eslint |
| Java | javac, checkstyle, maven/gradle |
| Flutter/Dart | dart analyze, flutter test |

## 설정

### `.vibe/config.yaml`

```yaml
# AI Provider 설정
provider: anthropic  # anthropic, google, openai

# 듀얼 모델 설정
dual_mode:
  enabled: true
  main_agent: anthropic  # 코드 생성 담당
  knowledge_engine: google  # 컨텍스트 분석 담당

# 검증 설정
verification:
  auto_verify: true
  self_healing: true
  max_healing_attempts: 2
```

## 지원 플랫폼

| 플랫폼 | 지원 |
|--------|------|
| macOS | O |
| Linux | O |
| Windows | O (WSL2 권장) |

## 기술 스택

- **CLI Framework**: Typer + Rich
- **AI SDKs**: Anthropic, Google Generative AI, OpenAI
- **Data Validation**: Pydantic v2
- **Template Engine**: Jinja2
- **Git Integration**: GitPython

## 개발

### 테스트 실행

```bash
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=src/vibe

# 특정 테스트
pytest tests/unit/test_config.py
```

### 린트 및 포매팅

```bash
# 린트 검사
ruff check src/

# 자동 수정
ruff check --fix src/

# 포매팅
ruff format src/
```

### 타입 체크

```bash
mypy src/vibe
```

## 라이선스

MIT License

## 기여

이슈와 풀 리퀘스트를 환영합니다.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
