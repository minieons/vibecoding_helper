# Vibe Coding Helper - 프로젝트 구조 (TREE.md)

## 디렉토리 구조

```
vibe-coding-helper/
├── src/
│   └── vibe/
│       ├── __init__.py                 # 패키지 초기화, 버전 정보
│       ├── main.py                     # CLI 진입점 (Typer app)
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── app.py                  # Typer 앱 인스턴스 및 공통 옵션
│       │   ├── commands/
│       │   │   ├── __init__.py
│       │   │   ├── init.py             # vibe init 명령어 (Phase 0)
│       │   │   ├── plan.py             # vibe plan 명령어 (Phase 1)
│       │   │   ├── design.py           # vibe design 명령어 (Phase 2)
│       │   │   ├── scaffold.py         # vibe scaffold 명령어 (Phase 2)
│       │   │   ├── code.py             # vibe code 명령어 (Phase 3)
│       │   │   ├── test.py             # vibe test 명령어 (Phase 4) - NEW
│       │   │   ├── status.py           # vibe status 명령어
│       │   │   ├── chat.py             # vibe chat 명령어
│       │   │   ├── undo.py             # vibe undo 명령어
│       │   │   └── verify.py           # vibe verify 명령어 (코드 검증)
│       │   └── ui/
│       │       ├── __init__.py
│       │       ├── console.py          # Rich Console 래퍼
│       │       ├── prompts.py          # 대화형 프롬프트 컴포넌트
│       │       ├── display.py          # 출력 포매팅 (테이블, 패널 등)
│       │       └── progress.py         # 프로그레스바, 스피너
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py               # 설정 로드/저장 (Pydantic 모델)
│       │   ├── state.py                # .vibe/state.json 관리
│       │   ├── context.py              # 컨텍스트 수집 및 토큰 관리
│       │   ├── workflow.py             # Phase별 워크플로우 오케스트레이션
│       │   └── exceptions.py           # 커스텀 예외 클래스
│       ├── providers/
│       │   ├── __init__.py
│       │   ├── base.py                 # AIProvider 추상 클래스
│       │   ├── anthropic.py            # Anthropic (Claude 4.5) - Main Agent
│       │   ├── google.py               # Google (Gemini 3) - Knowledge Engine
│       │   ├── openai.py               # OpenAI (GPT-5) - Backup
│       │   ├── factory.py              # Provider 팩토리
│       │   └── orchestrator.py         # 듀얼 모델 오케스트레이터 - NEW
│       ├── handlers/
│       │   ├── __init__.py
│       │   ├── file.py                 # 파일 읽기/쓰기/검증
│       │   ├── git.py                  # Git 연동 (커밋, 롤백)
│       │   ├── parser.py               # 마크다운/YAML 파싱
│       │   └── scaffold.py             # 디렉토리/파일 생성
│       ├── verifiers/                  # 언어별 코드 검증기 - NEW
│       │   ├── __init__.py
│       │   ├── base.py                 # LanguageVerifier 추상 클래스
│       │   ├── factory.py              # 검증기 팩토리
│       │   ├── python.py               # Python 검증기 (ast, mypy, ruff)
│       │   └── typescript.py           # TypeScript/JS 검증기 (tsc, eslint)
│       ├── prompts/
│       │   ├── __init__.py
│       │   ├── loader.py               # 프롬프트 로딩 유틸리티
│       │   ├── system/
│       │   │   ├── base.txt            # 공통 시스템 프롬프트
│       │   │   ├── agent_claude.txt    # Claude용 자율 에이전트 프롬프트
│       │   │   └── analyst_gemini.txt  # Gemini용 분석가 프롬프트
│       │   ├── phases/
│       │   │   ├── phase0_init.txt     # 초기화 프롬프트
│       │   │   ├── phase1_plan.txt     # 기획 프롬프트 (Multi-modal)
│       │   │   ├── phase2_design.txt   # 설계 프롬프트 (아키텍처)
│       │   │   ├── phase3_code.txt     # 구현 프롬프트 (Self-Healing)
│       │   │   └── phase4_test.txt     # 테스트 프롬프트 (감사/엣지케이스)
│       │   └── utils/
│       │       ├── audit_request.txt   # Gemini 전역 감사 요청
│       │       └── edge_case_gen.txt   # Claude 엣지 케이스 생성
│       └── templates/
│           ├── __init__.py
│           ├── loader.py               # Jinja2 템플릿 로더
│           ├── TECH_STACK.md.j2        # 기술 스택 템플릿
│           ├── RULES.md.j2             # 코딩 규칙 템플릿
│           ├── PRD.md.j2               # PRD 템플릿
│           ├── USER_STORIES.md.j2      # User Story 템플릿
│           ├── TREE.md.j2              # 구조 템플릿
│           ├── SCHEMA.md.j2            # 스키마 템플릿
│           ├── TODO.md.j2              # TODO 템플릿
│           └── CONTEXT.md.j2           # 컨텍스트 템플릿
├── tests/
│   ├── __init__.py
│   ├── conftest.py                     # pytest 공통 픽스처
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_config.py
│   │   ├── test_state.py
│   │   ├── test_context.py
│   │   ├── test_parser.py
│   │   └── providers/
│   │       ├── __init__.py
│   │       └── test_base.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_init_flow.py
│   │   ├── test_plan_flow.py
│   │   └── test_scaffold.py
│   └── fixtures/
│       ├── sample_projects/            # 테스트용 샘플 프로젝트
│       └── mock_responses/             # AI 응답 모킹 데이터
├── docs/                               # 추가 문서 (선택)
├── pyproject.toml                      # 프로젝트 설정 및 의존성
├── README.md                           # 프로젝트 소개
├── LICENSE                             # 라이선스
├── .gitignore                          # Git 제외 패턴
├── .pre-commit-config.yaml             # pre-commit 훅 설정
├── ruff.toml                           # ruff 린터 설정
│
│── # Vibe Artifacts (이 프로젝트용)
├── PLAN.md                             # 개발 계획서
├── TECH_STACK.md                       # 기술 스택
├── RULES.md                            # 코딩 규칙
├── PRD.md                              # 제품 요구사항
├── USER_STORIES.md                     # 사용자 스토리
├── TREE.md                             # 프로젝트 구조 (이 파일)
├── SCHEMA.md                           # 데이터 스키마
├── TODO.md                             # 작업 목록
└── .vibe/                              # 상태 관리 디렉토리
    ├── config.yaml                     # 프로젝트 설정
    ├── state.json                      # 현재 상태
    └── history/                        # 작업 히스토리
```

## 모듈 책임

### CLI Layer (`cli/`)
| 모듈 | 책임 |
|-----|------|
| `app.py` | Typer 앱 인스턴스, 전역 옵션 정의 |
| `commands/*.py` | 각 명령어별 핸들러 |
| `ui/*.py` | 터미널 UI 컴포넌트 (Rich 기반) |

### Core Layer (`core/`)
| 모듈 | 책임 |
|-----|------|
| `config.py` | 설정 로드/저장, 환경변수 처리 |
| `state.py` | Phase 상태, 작업 히스토리 관리 |
| `context.py` | AI 컨텍스트 수집, 토큰 예산 관리 |
| `workflow.py` | Phase별 워크플로우 조율 |
| `exceptions.py` | 커스텀 예외 정의 |

### Provider Layer (`providers/`)
| 모듈 | 책임 | 역할 |
|-----|------|-----|
| `base.py` | AIProvider 추상 클래스 | - |
| `anthropic.py` | Claude 4.5 API 연동 | **Main Agent** (코딩, 아키텍처) |
| `google.py` | Gemini 3 API 연동 | **Knowledge Engine** (컨텍스트, 감사) |
| `openai.py` | GPT-5 API 연동 | Backup |
| `factory.py` | Provider 인스턴스 생성 | - |
| `orchestrator.py` | 듀얼 모델 오케스트레이션 | Claude↔Gemini 협업 조율 |

### Handler Layer (`handlers/`)
| 모듈 | 책임 |
|-----|------|
| `file.py` | 파일 시스템 작업 |
| `git.py` | Git 커밋, 롤백 |
| `parser.py` | 마크다운, YAML, TOML 파싱 |
| `scaffold.py` | TREE.md 기반 디렉토리/파일 생성 |

### Prompts & Templates (`prompts/`, `templates/`)
| 디렉토리 | 책임 |
|---------|------|
| `prompts/system/` | 시스템 프롬프트 |
| `prompts/phases/` | Phase별 작업 프롬프트 |
| `templates/*.j2` | 문서 생성 Jinja2 템플릿 |
