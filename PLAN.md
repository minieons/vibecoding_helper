# Vibe Coding Helper - 개발 계획서 (Detailed Plan)

## 목차
1. [프로젝트 개요](#1-프로젝트-개요)
2. [핵심 철학](#2-핵심-철학)
3. [핵심 문서 체계](#3-핵심-문서-체계-the-vibe-artifacts)
4. [프로젝트 유형별 전략](#4-프로젝트-유형별-전략)
5. [CLI 명령어 체계](#5-cli-명령어-체계)
6. [시스템 아키텍처](#6-시스템-아키텍처)
7. [워크플로우 상세](#7-워크플로우-workflow-상세)
8. [기술 스택](#8-기술-스택-technical-stack)
9. [AI 프롬프트 관리 전략](#9-ai-프롬프트-관리-전략)
10. [에러 처리 전략](#10-에러-처리-전략)
11. [테스트 전략](#11-테스트-전략)
12. [개발 로드맵](#12-개발-로드맵)
13. [사용 시나리오 예시](#13-사용-시나리오-예시)
14. [보안 고려사항](#14-보안-고려사항)
15. [향후 확장 계획](#15-향후-확장-계획)

---

## 1. 프로젝트 개요
**Vibe Coding Helper**는 대화형 CLI 툴로서, 개발의 전 과정을 "핵심 문서(Artifact)의 정의와 구현" 과정으로 체계화합니다. AI는 이 문서들을 이정표 삼아 문맥을 유지하며 사용자의 'Vibe'를 실행 가능한 코드로 변환합니다.

### 1.1 핵심 가치 제안
- **문맥 손실 방지**: AI가 대화 도중 문맥을 잃어버리는 문제를 문서 기반 접근으로 해결
- **재현 가능한 개발**: 모든 결정과 진행 상황이 문서화되어 언제든 복구/재개 가능
- **점진적 구체화**: 막연한 아이디어에서 실행 가능한 코드까지 단계별 안내

## 2. 핵심 철학
*   **Document-Driven:** 모든 개발 단계는 특정 문서의 생성 또는 업데이트로 귀결됩니다.
*   **Context-Aware:** 생성된 문서와 `.vibe/` 상태 파일을 통해 프로젝트의 문맥을 지속적으로 추적합니다.
*   **Step-by-Step:** 복잡한 개발 과정을 관리 가능한 작은 단계(Phase)로 나누어 안내합니다.
*   **Transparent & Controlled:** AI의 모든 작업은 사용자 승인을 거치며, 언제든 롤백 가능합니다.

## 3. 핵심 문서 체계 (The Vibe Artifacts)
이 툴은 다음 4가지 카테고리의 문서를 필수적으로 관리하며, 이는 AI의 '장기 기억' 역할을 합니다.

| 카테고리 | 문서명 | 역할 |
| :--- | :--- | :--- |
| **The Rules** | `RULES.md`, `.cursorrules` | 코딩 스타일, 네이밍 컨벤션, 아키텍처 규칙 정의 |
| **The Goal** | `PRD.md`, `USER_STORIES.md` | 프로젝트 목적, 핵심 기능 요구사항, 사용자 시나리오 |
| **The Skeleton** | `TREE.md`, `TECH_STACK.md`, `SCHEMA.md` | 폴더 구조, 사용 기술 버전, 데이터/API 규격 |
| **The Memory** | `TODO.md`, `CONTEXT.md` | 현재 진행 상황(할 일 목록), 작업 히스토리 및 결정 사항 |

## 4. 프로젝트 유형별 전략

### 4.1 지원 프로젝트 유형
`vibe init` 시 프로젝트 유형을 감지하거나 선택받아, 적합한 문서 템플릿과 워크플로우를 적용합니다.

| 유형 | 설명 | 예시 |
|-----|------|-----|
| **backend** | API 서버, 백엔드 단독 | FastAPI, Django REST, Express |
| **frontend** | SPA, 정적 웹사이트 | React, Vue, Svelte |
| **fullstack** | 프론트+백엔드 통합 | Next.js, Nuxt, SvelteKit |
| **backend-web** | 백엔드 + 별도 웹 클라이언트 | FastAPI + React (모노레포) |
| **backend-mobile** | 백엔드 + 모바일 앱 | Django + React Native |
| **mobile** | 모바일 앱 단독 | React Native, Flutter |
| **library** | 라이브러리/패키지 | npm 패키지, PyPI 패키지 |
| **cli** | CLI 도구 | Typer, Commander.js |

### 4.2 유형별 문서 체계 차이

#### 4.2.1 SCHEMA.md 구조 차이
```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SCHEMA.md 구성 요소                            │
├─────────────┬─────────┬──────────┬─────────────┬──────────┬────────────┤
│   유형       │ DB 스키마│ API 스펙  │ 상태 관리    │ 네비게이션 │ 컴포넌트   │
├─────────────┼─────────┼──────────┼─────────────┼──────────┼────────────┤
│ backend     │   ✅    │   ✅     │     -       │    -     │     -      │
│ frontend    │    -    │   ✅*    │    ✅       │   ✅     │    ✅      │
│ fullstack   │   ✅    │   ✅     │    ✅       │   ✅     │    ✅      │
│ backend-web │   ✅    │   ✅     │    ✅       │   ✅     │    ✅      │
│ backend-mobile│  ✅   │   ✅     │    ✅       │   ✅     │    ✅      │
│ mobile      │    -    │   ✅*    │    ✅       │   ✅     │    ✅      │
│ library     │    -    │   ✅**   │     -       │    -     │     -      │
│ cli         │    -    │   ✅***  │     -       │    -     │     -      │
└─────────────┴─────────┴──────────┴─────────────┴──────────┴────────────┘
* 외부 API 연동 스펙  ** 퍼블릭 API 문서  *** 명령어 인터페이스 정의
```

#### 4.2.2 유형별 SCHEMA.md 템플릿

**backend 유형:**
```markdown
# SCHEMA.md

## 1. 데이터베이스 스키마
### 1.1 ERD
### 1.2 테이블 정의
### 1.3 마이그레이션 전략

## 2. API 스펙
### 2.1 인증/인가
### 2.2 엔드포인트 목록
### 2.3 요청/응답 스키마 (OpenAPI 형식)

## 3. 외부 연동
### 3.1 서드파티 API
### 3.2 메시지 큐/이벤트
```

**frontend 유형:**
```markdown
# SCHEMA.md

## 1. 상태 관리
### 1.1 전역 상태 구조 (Store)
### 1.2 로컬 상태 전략
### 1.3 서버 상태 (React Query/SWR)

## 2. API 연동
### 2.1 백엔드 API 스펙 (참조)
### 2.2 API 클라이언트 구조

## 3. 라우팅/네비게이션
### 3.1 페이지 구조
### 3.2 인증 라우트 가드
### 3.3 딥링크 (모바일)

## 4. 컴포넌트 아키텍처
### 4.1 컴포넌트 계층 구조
### 4.2 공통 컴포넌트 목록
### 4.3 디자인 시스템/토큰
```

**backend-web / backend-mobile 유형 (멀티 파트):**
```markdown
# SCHEMA.md

## Part A: Backend
### A.1 데이터베이스 스키마
### A.2 API 스펙 (계약)
### A.3 인증 흐름

## Part B: Client (Web/Mobile)
### B.1 상태 관리
### B.2 API 클라이언트
### B.3 라우팅/네비게이션
### B.4 컴포넌트 아키텍처

## Part C: 공유
### C.1 타입 정의 (공유 스키마)
### C.2 검증 규칙
### C.3 에러 코드 체계
```

### 4.3 유형별 TREE.md 구조

#### backend
```
project/
├── src/
│   ├── api/              # 라우터/컨트롤러
│   ├── services/         # 비즈니스 로직
│   ├── models/           # DB 모델
│   ├── schemas/          # Pydantic/DTO
│   └── core/             # 설정, 의존성
├── tests/
├── migrations/
└── docker-compose.yml
```

#### frontend (React)
```
project/
├── src/
│   ├── components/       # UI 컴포넌트
│   │   ├── common/       # 공통 컴포넌트
│   │   └── features/     # 기능별 컴포넌트
│   ├── pages/            # 페이지 컴포넌트
│   ├── hooks/            # 커스텀 훅
│   ├── stores/           # 상태 관리
│   ├── services/         # API 클라이언트
│   └── styles/           # 글로벌 스타일
├── public/
└── tests/
```

#### backend-web (모노레포)
```
project/
├── packages/
│   ├── backend/          # 백엔드 (위 backend 구조)
│   ├── web/              # 웹 클라이언트 (위 frontend 구조)
│   └── shared/           # 공유 코드
│       ├── types/        # 공유 타입 정의
│       └── validators/   # 공유 검증 로직
├── docker-compose.yml
└── turbo.json / nx.json  # 모노레포 설정
```

#### backend-mobile
```
project/
├── backend/              # 백엔드 (별도 저장소 가능)
│   └── ...
├── mobile/               # 모바일 앱
│   ├── src/
│   │   ├── screens/      # 화면
│   │   ├── components/   # 컴포넌트
│   │   ├── navigation/   # 네비게이션 설정
│   │   ├── stores/       # 상태 관리
│   │   └── services/     # API 클라이언트
│   ├── ios/
│   └── android/
└── shared/               # 공유 타입 (선택)
```

### 4.4 유형별 워크플로우 차이

#### Phase 2 (설계) 차이점

| 유형 | 추가 질문/단계 |
|-----|--------------|
| **backend** | DB 선택 (PostgreSQL/MySQL/MongoDB), ORM 선택 |
| **frontend** | 상태 관리 라이브러리, CSS 전략 (Tailwind/CSS-in-JS) |
| **fullstack** | SSR/SSG 전략, API 라우트 설계 |
| **backend-web** | 모노레포 도구 (Turborepo/Nx), 공유 코드 범위 |
| **backend-mobile** | 모바일 프레임워크, 오프라인 전략, 푸시 알림 |
| **mobile** | 네이티브 모듈 필요 여부, 딥링크 설계 |

#### Phase 3 (구현) 차이점

**멀티 파트 프로젝트의 구현 순서:**
```
backend-web / backend-mobile:

1. 공유 타입/스키마 정의 (shared/)
2. 백엔드 API 구현 (계약 기반)
3. 클라이언트 API 클라이언트 생성
4. 클라이언트 기능 구현
5. 통합 테스트

→ TODO.md가 파트별로 그룹화됨:
   [BACKEND-001] ~ [BACKEND-010]
   [SHARED-001] ~ [SHARED-003]
   [WEB-001] ~ [WEB-015]
```

### 4.5 유형별 추가 문서

| 유형 | 추가 문서 |
|-----|----------|
| **backend** | `API.md` (OpenAPI 기반 상세 문서) |
| **frontend** | `COMPONENTS.md` (Storybook 연동 가능) |
| **fullstack** | `ROUTES.md` (페이지 + API 라우트 통합) |
| **backend-web** | `CONTRACT.md` (프론트-백 계약), `MONOREPO.md` |
| **backend-mobile** | `CONTRACT.md`, `MOBILE_SPEC.md` (플랫폼별 고려사항) |
| **mobile** | `SCREENS.md` (화면 플로우), `NATIVE.md` (네이티브 연동) |
| **library** | `API_REFERENCE.md`, `MIGRATION.md` (버전 업그레이드) |
| **cli** | `COMMANDS.md` (명령어 상세) |

### 4.6 프로젝트 유형 감지 로직

`vibe init` 시 자동 감지:
```python
def detect_project_type(description: str, existing_files: list) -> str:
    # 1. 기존 파일 기반 감지
    if "package.json" in existing_files:
        pkg = load_json("package.json")
        if "next" in pkg.get("dependencies", {}):
            return "fullstack"
        if "react-native" in pkg.get("dependencies", {}):
            return "mobile" or "backend-mobile"
        if "react" in pkg.get("dependencies", {}):
            return "frontend" or "backend-web"

    if "pyproject.toml" in existing_files or "requirements.txt" in existing_files:
        # FastAPI, Django 등 감지
        return "backend"

    # 2. 설명 기반 추론
    keywords = {
        "api": "backend",
        "서버": "backend",
        "웹사이트": "frontend",
        "앱": "mobile",
        "모바일": "mobile",
        "풀스택": "fullstack",
    }

    # 3. 사용자에게 확인
    return ask_user_to_select()
```

## 5. CLI 명령어 체계

### 5.1 핵심 명령어
```bash
# 프로젝트 초기화
vibe init [프로젝트_설명]        # 새 프로젝트 시작, TECH_STACK.md & RULES.md 생성

# 기획 단계
vibe plan                       # PRD.md, USER_STORIES.md 생성을 위한 인터뷰 시작
vibe plan --review              # 기존 PRD 검토 및 수정

# 설계 단계
vibe design                     # TREE.md, SCHEMA.md 생성
vibe scaffold                   # TREE.md 기반으로 실제 디렉토리/파일 생성

# 구현 단계
vibe code                       # TODO.md의 다음 작업 자동 진행
vibe code [task_id]             # 특정 작업 지정 실행
vibe code --file [파일경로]      # 특정 파일 코드 생성/수정

# 상태 관리
vibe status                     # 현재 Phase 및 진행 상황 표시
vibe todo                       # TODO.md 내용 표시 및 관리
vibe context                    # CONTEXT.md 요약 표시

# 유틸리티
vibe undo                       # 마지막 작업 롤백 (Git 기반)
vibe chat                       # 자유 대화 모드 (문서 수정 없음)
vibe export                     # 모든 문서를 하나의 컨텍스트로 출력
```

### 5.2 명령어 옵션
```bash
# 전역 옵션
--provider, -p [openai|anthropic|google]  # AI 제공자 선택
--model, -m [모델명]                       # 특정 모델 지정
--verbose, -v                              # 상세 로그 출력
--dry-run                                  # 실제 파일 변경 없이 미리보기
--yes, -y                                  # 모든 확인 프롬프트 자동 승인
```

## 6. 시스템 아키텍처

### 6.1 핵심 컴포넌트
```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                             │
│                   (Typer + Rich UI)                         │
├─────────────────────────────────────────────────────────────┤
│                    Core Controller                           │
│         (명령 해석, 워크플로우 오케스트레이션)                    │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   AI Provider│   Context    │    File      │     State      │
│   Interface  │   Manager    │   Handler    │   Persistence  │
│  (추상 클래스) │ (대화/프로젝트)│  (읽기/쓰기)  │   (.vibe/)     │
├──────────────┴──────────────┴──────────────┴────────────────┤
│                    External Services                         │
│           (OpenAI / Anthropic / Google APIs)                │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 디렉토리 구조 (프로젝트 자체)
```
vibe-coding-helper/
├── src/
│   └── vibe/
│       ├── __init__.py
│       ├── main.py              # CLI 진입점 (Typer app)
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── commands/        # 각 명령어 구현 (init, plan, design, code 등)
│       │   └── ui.py            # Rich 기반 UI 컴포넌트
│       ├── core/
│       │   ├── __init__.py
│       │   ├── controller.py    # 메인 워크플로우 오케스트레이션
│       │   ├── context.py       # 컨텍스트 매니저 (토큰 최적화 포함)
│       │   ├── state.py         # .vibe/ 상태 관리
│       │   └── workflow.py      # Phase별 워크플로우 정의
│       ├── providers/
│       │   ├── __init__.py
│       │   ├── base.py          # AI Provider 추상 클래스
│       │   ├── openai.py        # OpenAI 구현
│       │   ├── anthropic.py     # Anthropic 구현
│       │   └── google.py        # Google AI 구현
│       ├── handlers/
│       │   ├── __init__.py
│       │   ├── file.py          # 파일 읽기/쓰기/검증
│       │   ├── git.py           # Git 연동 (커밋, 롤백)
│       │   └── parser.py        # 마크다운/YAML 파싱
│       ├── prompts/             # AI 프롬프트 템플릿
│       │   ├── system/          # 시스템 프롬프트
│       │   └── phases/          # Phase별 프롬프트
│       └── templates/           # 문서 생성용 Jinja2 템플릿
│           ├── PRD.md.j2
│           ├── RULES.md.j2
│           ├── TREE.md.j2
│           └── ...
├── tests/
│   ├── unit/                    # 단위 테스트
│   ├── integration/             # 통합 테스트
│   └── fixtures/                # 테스트 픽스처
├── pyproject.toml
└── README.md
```

### 6.3 `.vibe/` 상태 디렉토리 구조
사용자 프로젝트 내에 생성되는 상태 관리 디렉토리:
```
.vibe/
├── config.yaml                  # 프로젝트별 설정 (provider, model 등)
├── state.json                   # 현재 Phase, 마지막 작업 등 상태 정보
├── history/                     # 작업 히스토리 (롤백용)
│   ├── 2024-01-15_001.json
│   └── ...
├── cache/                       # AI 응답 캐시 (선택적)
└── locks/                       # 동시 실행 방지용 락 파일
```

#### `config.yaml` 예시
```yaml
project_name: "weather-api"
project_type: backend-mobile     # backend, frontend, fullstack, backend-web, backend-mobile, mobile, library, cli
provider: anthropic
model: claude-3-5-sonnet
auto_commit: true
language: ko                     # 응답 언어
token_budget: 100000             # 컨텍스트 토큰 예산

# 멀티 파트 프로젝트 설정 (backend-web, backend-mobile인 경우)
parts:
  backend:
    path: ./backend
    framework: fastapi
  client:
    path: ./mobile
    framework: react-native
  shared:
    path: ./shared
```

#### `state.json` 예시
```json
{
  "current_phase": 2,
  "phase_status": {
    "0": "completed",
    "1": "completed",
    "2": "in_progress",
    "3": "pending"
  },
  "last_action": {
    "command": "vibe design",
    "timestamp": "2024-01-15T10:30:00Z",
    "files_modified": ["TREE.md"]
  },
  "git_enabled": true,
  "last_commit": "abc1234"
}
```

## 7. 워크플로우 (Workflow) 상세

### Phase 0: 초기화 (Initialization)
**목표:** 프로젝트의 '성격'을 결정하고 기본 규칙을 수립합니다.

**입력:** `vibe init "프로젝트 설명"`
**출력:** `TECH_STACK.md`, `RULES.md`

**상세 플로우:**
```
1. 사용자 입력 분석 → 기술 스택 추론
2. 인터뷰 질문 생성:
   - "어떤 프레임워크를 선호하시나요?" (추천 포함)
   - "코딩 스타일 선호도가 있나요?" (함수형/OOP 등)
   - "테스트 프레임워크 선호도?"
3. 응답 기반 문서 생성
4. 사용자 검토 및 승인
5. Git 초기 커밋 (선택적)
```

### Phase 1: 기획 (Planning)
**목표:** 사용자의 아이디어를 구체적인 요구사항으로 변환합니다.

**입력:** `vibe plan`
**출력:** `PRD.md`, `USER_STORIES.md`

**상세 플로우:**
```
1. 기존 문서(TECH_STACK, RULES) 로드
2. 대화형 인터뷰:
   - "이 서비스의 핵심 기능은 무엇인가요?"
   - "주요 사용자는 누구인가요?"
   - "MVP 범위는 어디까지인가요?"
3. PRD 초안 생성 및 검토
4. User Story 도출: "As a [user], I want [feature], so that [benefit]"
5. 우선순위 지정 (MoSCoW: Must/Should/Could/Won't)
6. 문서 확정 및 커밋
```

### Phase 2: 설계 (Blueprint)
**목표:** 요구사항을 실행 가능한 기술 설계로 변환합니다.

**입력:** `vibe design`, `vibe scaffold`
**출력:** `TREE.md`, `SCHEMA.md`, 실제 디렉토리/파일

**상세 플로우:**
```
1. PRD 및 USER_STORIES 분석
2. 아키텍처 제안:
   - 디렉토리 구조 (TREE.md)
   - 데이터 모델 (SCHEMA.md)
   - API 엔드포인트 (SCHEMA.md 내 API 섹션)
3. 사용자 검토 및 수정
4. 스캐폴딩 실행:
   - 디렉토리 생성
   - 빈 파일 생성 (주석으로 목적 명시)
   - 의존성 파일 생성 (requirements.txt, package.json 등)
5. TODO.md 자동 생성 (구현 태스크 목록)
```

### Phase 3: 구현 (Implementation)
**목표:** 설계를 실제 동작하는 코드로 변환합니다.

**입력:** `vibe code`
**출력:** 소스 코드, 업데이트된 `TODO.md`, `CONTEXT.md`

**상세 플로우:**
```
1. TODO.md에서 다음 작업 선택
2. 관련 컨텍스트 수집:
   - RULES.md (코딩 규칙)
   - SCHEMA.md (데이터 구조)
   - 관련 기존 코드 파일
3. 코드 생성
4. 사용자 검토 (diff 표시)
5. 승인 시:
   - 파일 작성
   - Git 커밋 (자동)
   - TODO.md 업데이트 (체크)
   - CONTEXT.md 업데이트 (작업 내용 기록)
6. 다음 작업으로 진행 또는 일시 정지
```

### 상태 전이 다이어그램
```
[init] → Phase 0 → [plan] → Phase 1 → [design] → Phase 2 → [code] → Phase 3
                                                     ↑                  ↓
                                                     └──── [iterate] ←──┘
```

## 8. 기술 스택 (Technical Stack)

### 8.1 핵심 의존성
| 카테고리 | 라이브러리 | 버전 | 용도 |
|---------|-----------|------|-----|
| **Runtime** | Python | 3.10+ | 기본 언어 |
| **CLI** | Typer | 0.9+ | 명령어 파싱 및 라우팅 |
| **UI** | Rich | 13+ | 터미널 UI (프로그레스, 테이블, 패널) |
| **AI** | openai | 1.0+ | OpenAI API 연동 |
| **AI** | anthropic | 0.18+ | Anthropic API 연동 |
| **AI** | google-generativeai | 0.3+ | Google AI 연동 |
| **Template** | Jinja2 | 3.1+ | 문서 템플릿 엔진 |
| **Config** | PyYAML | 6.0+ | YAML 설정 파일 파싱 |
| **Config** | pydantic | 2.0+ | 설정/상태 스키마 검증 |
| **Git** | GitPython | 3.1+ | Git 연동 |

### 8.2 개발 의존성
| 라이브러리 | 용도 |
|-----------|-----|
| pytest | 테스트 프레임워크 |
| pytest-asyncio | 비동기 테스트 |
| pytest-cov | 커버리지 리포트 |
| ruff | 린팅 및 포매팅 |
| mypy | 타입 체킹 |
| pre-commit | Git 훅 관리 |

## 9. AI 모델 및 프롬프트 운영 전략

### 9.1 단계별 모델 할당 전략 (Model Orchestration)
각 단계(Phase)의 목표 달성을 위해 Claude 4.5(Agentic)와 Gemini 3(Contextual)의 강점을 교차 활용합니다.

| Phase | 단계명 | 담당 모델 (Role) | 핵심 활용 기능 |
|:---:|:---:|:---|:---|
| **0** | **Init** | **Gemini 3** | 사용자 의도 파악 및 초기 기술 스택 제안 |
| **1** | **Plan** | **Gemini 3** (Ingester)<br>+ **Claude 4.5** (Planner) | **G:** 무한 문맥(문서/영상) 분석, 아이디어 발산<br>**C:** 사용자의 코딩 습관/선호도에 맞춘 PRD 정렬 |
| **2** | **Design** | **Claude 4.5** (Architect)<br>+ **Gemini 3** (Navigator) | **C:** 전체 아키텍처 시뮬레이션 및 구조 설계<br>**G:** 라이브러리 버전 호환성 실시간 검증 (Web Access) |
| **3** | **Code** | **Claude 4.5** (Coder)<br>+ **Gemini 3** (Bridge) | **C:** 자율 코딩, 툴 사용(Tool Use), 에러 자가 치유<br>**G:** 전체 코드베이스 실시간 동기화 및 컨텍스트 주입 |
| **4** | **Test** | **Gemini 3** (Auditor)<br>+ **Claude 4.5** (Tester) | **G:** 시스템 전역 데이터 흐름 감사 및 논리적 결함 탐지<br>**C:** 엣지 케이스 생성 및 사용자 관점 테스트 시나리오 작성 |

### 9.2 프롬프트 관리 전략
#### 프롬프트 구조
```
prompts/
├── system/
│   ├── base.txt                 # 공통 시스템 프롬프트
│   ├── agent_claude.txt         # Claude 4.5용 자율 에이전트 프롬프트
│   └── analyst_gemini.txt       # Gemini 3용 분석가 프롬프트
├── phases/
│   ├── phase1_planning.txt      # 기획 단계 (Multi-modal 지원)
│   ├── phase2_design.txt        # 설계 단계 (아키텍처 시뮬레이션 요청)
│   └── phase3_implement.txt     # 구현 단계 (Self-Healing 가이드)
└── utils/
    ├── audit_request.txt        # Gemini 전체 감사 요청
    └── edge_case_gen.txt        # Claude 엣지 케이스 생성
```

### 9.3 컨텍스트 관리 (Context Management)
*   **Dual-Track Context:**
    *   **Hot Memory (Claude):** 현재 작업 중인 파일 + 핵심 규칙 (`RULES.md`)
    *   **Cold Storage (Gemini):** 프로젝트 전체 소스, 외부 문서, 라이브러리 공식 문서 (Infinite Context 활용)
*   **Context Injection:**
    *   Claude가 코딩 중 외부 정보가 필요할 때 Gemini에게 질의하여 요약 정보를 주입받음.

### 9.4 에러 처리 및 자가 치유
*   **Self-Healing Workflow:**
    1.  Claude가 코드 생성 및 실행
    2.  에러 발생 시 Traceback 분석
    3.  Claude가 스스로 수정안 도출 및 재시도 (최대 3회)
    4.  실패 시 Gemini가 전체 시스템 관점에서 원인 분석 리포트 제공

## 10. 에러 처리 전략

### 10.1 에러 카테고리
| 카테고리 | 예시 | 처리 방식 |
|---------|-----|---------|
| **API 에러** | Rate limit, 인증 실패 | 재시도 with exponential backoff |
| **파일 에러** | 권한 없음, 파일 없음 | 명확한 메시지 + 복구 제안 |
| **상태 에러** | 잘못된 Phase 순서 | 현재 상태 표시 + 올바른 명령 안내 |
| **검증 에러** | 잘못된 YAML/JSON | 파싱 에러 위치 표시 + 수정 제안 |
| **Git 에러** | 충돌, 더티 상태 | 상황 설명 + 해결 방법 안내 |

### 10.2 롤백 메커니즘
```python
# 모든 파일 변경 작업은 트랜잭션으로 처리
with FileTransaction() as tx:
    tx.write("file1.py", content1)
    tx.write("file2.py", content2)
    # 예외 발생 시 모든 변경 자동 롤백
```

### 10.3 사용자 친화적 에러 메시지
```
❌ API 호출 실패: Rate limit 초과

원인: OpenAI API 요청 한도를 초과했습니다.
해결: 1분 후 자동으로 재시도합니다. (시도 2/3)

💡 팁: 'vibe config --provider anthropic'으로 다른 제공자를 사용할 수 있습니다.
```

## 11. 테스트 전략

### 11.1 테스트 계층
```
tests/
├── unit/                        # 단위 테스트 (외부 의존성 모킹)
│   ├── test_context.py
│   ├── test_parser.py
│   └── test_state.py
├── integration/                 # 통합 테스트 (실제 파일 시스템)
│   ├── test_init_flow.py
│   ├── test_plan_flow.py
│   └── test_scaffold.py
├── e2e/                         # E2E 테스트 (실제 AI API, 선택적)
│   └── test_full_workflow.py
└── fixtures/
    ├── sample_projects/         # 테스트용 샘플 프로젝트
    └── mock_responses/          # AI 응답 모킹 데이터
```

### 11.2 테스트 커버리지 목표
- 단위 테스트: 80% 이상
- 통합 테스트: 핵심 워크플로우 100%
- E2E: 주요 시나리오 (CI에서는 모킹)

### 11.3 AI 응답 테스트
```python
# 실제 API 호출 없이 일관된 테스트를 위한 응답 모킹
@pytest.fixture
def mock_ai_response():
    return load_fixture("mock_responses/prd_generation.json")
```

## 12. 개발 로드맵

### Step 1: Foundation (Week 1-2)
- [ ] 프로젝트 구조 생성 (`pyproject.toml`, 디렉토리)
- [ ] Typer CLI 기본 셋업 (`main.py`, 명령어 라우팅)
- [ ] AI Provider 인터페이스 정의 (`providers/base.py`)
- [ ] OpenAI Provider 구현 (`providers/openai.py`)
- [ ] 기본 설정 시스템 (`.vibe/config.yaml`)
- [ ] **Phase 0 구현:** `vibe init` 명령

### Step 2: Planning Phase (Week 3-4)
- [ ] 대화형 인터뷰 엔진 구현
- [ ] Jinja2 템플릿 시스템 구축
- [ ] **Phase 1 구현:** `vibe plan` (PRD, USER_STORIES 생성)
- [ ] Anthropic Provider 구현
- [ ] 문서 파싱 유틸리티

### Step 3: Design Phase (Week 5-6)
- [ ] TREE.md 파서 및 스캐폴딩 엔진
- [ ] SCHEMA.md 생성 로직
- [ ] **Phase 2 구현:** `vibe design`, `vibe scaffold`
- [ ] TODO.md 자동 생성

### Step 4: Implementation Phase (Week 7-8)
- [ ] 컨텍스트 매니저 (토큰 예산, 요약)
- [ ] 코드 생성 엔진
- [ ] **Phase 3 구현:** `vibe code`
- [ ] CONTEXT.md 자동 업데이트

### Step 5: Polish & Release (Week 9-10)
- [ ] Git 연동 (`vibe undo`, 자동 커밋)
- [ ] `vibe status`, `vibe chat` 구현
- [ ] 에러 처리 강화
- [ ] 문서화 및 README
- [ ] PyPI 배포 준비

## 13. 사용 시나리오 예시

### 13.1 새 프로젝트 시작
```bash
$ vibe init "FastAPI를 사용한 날씨 알림 API 서버를 만들고 싶어."

🚀 Vibe Coding Helper v1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 프로젝트 초기화를 시작합니다...

💬 몇 가지 질문에 답해주세요:

[1/4] 선호하는 Python 버전은? (기본: 3.11)
> 3.11

[2/4] 코딩 스타일 선호도는?
  1. 함수형 (Recommended)
  2. 객체지향
  3. 혼합
> 1

[3/4] 테스트 프레임워크 선호도는?
  1. pytest (Recommended)
  2. unittest
> 1

[4/4] 자동 Git 커밋을 활성화할까요? (Y/n)
> Y

✅ 다음 파일을 생성했습니다:
   • TECH_STACK.md
   • RULES.md
   • .vibe/config.yaml

💡 다음 단계: 'vibe plan'을 실행하여 기획을 시작하세요.
```

### 13.2 기획 단계
```bash
$ vibe plan

📋 Phase 1: 기획 (Planning)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

현재 문서 로드 중... ✓

💬 프로젝트에 대해 더 알려주세요:

Q: 이 서비스의 핵심 기능은 무엇인가요?
> 사용자가 원하는 지역의 날씨를 조회하고, 특정 조건에서 알림을 받을 수 있어야 해.

Q: 주요 사용자는 누구인가요?
> 출퇴근하는 직장인들

Q: MVP에 꼭 포함되어야 할 기능은?
> 날씨 조회, 알림 설정, 푸시 알림

───────────────────────────────
📝 PRD.md 초안을 생성했습니다. 검토해주세요:
───────────────────────────────

[PRD 내용 미리보기...]

이 내용이 맞나요? (Y/n/edit)
> Y

✅ 생성 완료:
   • PRD.md
   • USER_STORIES.md

💡 다음 단계: 'vibe design'을 실행하여 설계를 시작하세요.
```

### 13.3 코드 구현
```bash
$ vibe code

📋 Phase 3: 구현 (Implementation)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 TODO.md 로드 중... ✓

다음 작업을 진행합니다:
┌─────────────────────────────────────────┐
│ [TODO-003] WeatherService 클래스 구현    │
│ 우선순위: High | 예상 파일: services/weather.py │
└─────────────────────────────────────────┘

진행할까요? (Y/n/skip)
> Y

🔄 코드 생성 중...

───────────────────────────────
📝 services/weather.py
───────────────────────────────
+ from typing import Optional
+ from datetime import datetime
+ import httpx
+
+ class WeatherService:
+     def __init__(self, api_key: str):
+         self.api_key = api_key
+         self.base_url = "https://api.openweathermap.org"
+     ...

이 변경사항을 적용할까요? (Y/n/edit)
> Y

✅ 완료:
   • services/weather.py 생성
   • TODO.md 업데이트 ([TODO-003] ✓)
   • Git 커밋: "feat: implement WeatherService class"

📊 진행 상황: ████████░░ 80% (8/10 tasks)

계속 진행할까요? (Y/n)
> n

💡 다음에 'vibe code'를 실행하면 [TODO-004]부터 이어서 진행합니다.
```

## 14. 보안 고려사항

### 14.1 API 키 관리
- API 키는 **절대** 문서나 코드에 포함하지 않음
- 환경 변수 또는 시스템 키체인 사용 권장
- `.vibe/config.yaml`에는 provider 이름만 저장

### 14.2 생성 코드 보안
- SQL Injection, XSS 등 OWASP Top 10 취약점 방지 규칙 적용
- 시스템 프롬프트에 보안 가이드라인 포함
- 민감한 정보(비밀번호, 토큰) 하드코딩 감지 및 경고

### 14.3 파일 시스템 안전
- 프로젝트 디렉토리 외부 파일 접근 차단
- 심볼릭 링크 추적 제한
- `.gitignore` 자동 생성 (민감 파일 제외)

## 15. 향후 확장 계획

### v1.1
- [ ] 플러그인 시스템 (커스텀 Phase 추가)
- [ ] 웹 UI 대시보드
- [ ] 팀 협업 기능 (공유 컨텍스트)

### v1.2
- [ ] IDE 확장 (VS Code, JetBrains)
- [ ] 코드 리뷰 자동화 연동 (GitHub PR)
- [ ] 다국어 지원 강화

### v2.0
- [ ] 로컬 LLM 지원 (Ollama, LM Studio)
- [ ] 멀티 프로젝트 관리
- [ ] AI 모델 파인튜닝 지원