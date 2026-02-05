# Vibe Coding Helper - 제품 요구사항 문서 (PRD)

## 1. 개요

### 1.1 제품 비전
**Vibe Coding Helper**는 개발자의 막연한 아이디어("Vibe")를 체계적인 문서와 실행 가능한 코드로 변환하는 대화형 CLI 도구입니다.

### 1.2 문제 정의
| 문제 | 설명 |
|-----|------|
| **문맥 손실** | AI와 대화 중 문맥이 끊기면 처음부터 다시 설명해야 함 |
| **비체계적 개발** | 막연한 아이디어로 코딩을 시작하면 방향을 잃기 쉬움 |
| **재현 불가능** | 이전 결정 사항과 진행 상황을 추적하기 어려움 |

### 1.3 솔루션
- **Document-Driven**: 모든 개발 단계를 문서(Artifact)로 기록
- **Phase-Based Workflow**: 초기화 → 기획 → 설계 → 구현의 단계별 진행
- **Context Persistence**: `.vibe/` 디렉토리로 상태와 문맥 유지

## 2. 목표 사용자

### 2.1 Primary User
- AI 도구(ChatGPT, Claude 등)를 활용해 코딩하는 개발자
- 사이드 프로젝트나 MVP를 빠르게 만들고 싶은 개발자
- 체계적인 개발 프로세스를 원하지만 무거운 도구는 피하고 싶은 개발자

### 2.2 User Persona
```
이름: 김개발 (32세, 백엔드 개발자)
상황: 주말에 사이드 프로젝트로 날씨 알림 앱을 만들고 싶음
고민: "ChatGPT한테 물어보면서 코딩하는데, 대화가 길어지면
      앞에서 했던 얘기를 자꾸 까먹어서 다시 설명해야 해"
기대: "내가 뭘 만들고 있는지, 어디까지 했는지 한눈에 보이면 좋겠다"
```

## 3. 핵심 기능 (MVP)

### 3.1 Phase 0: 초기화 (`vibe init`)
| 기능 | 설명 | 우선순위 |
|-----|------|---------|
| 프로젝트 설명 입력 | 자연어로 프로젝트 아이디어 입력 | Must |
| 대화형 인터뷰 | 기술 스택, 코딩 스타일 등 질문 | Must |
| 문서 생성 | `TECH_STACK.md`, `RULES.md` 자동 생성 | Must |
| `.vibe/` 초기화 | 설정 및 상태 파일 생성 | Must |

### 3.2 Phase 1: 기획 (`vibe plan`)
| 기능 | 설명 | 우선순위 |
|-----|------|---------|
| 요구사항 인터뷰 | 핵심 기능, 사용자, MVP 범위 질문 | Must |
| PRD 생성 | `PRD.md` 자동 생성 | Must |
| User Story 생성 | `USER_STORIES.md` 자동 생성 | Must |
| 우선순위 지정 | MoSCoW 방식 우선순위 | Should |

### 3.3 Phase 2: 설계 (`vibe design`, `vibe scaffold`)
| 기능 | 설명 | 우선순위 |
|-----|------|---------|
| 구조 설계 | `TREE.md` 자동 생성 | Must |
| 스키마 설계 | `SCHEMA.md` (DB, API 등) 자동 생성 | Must |
| 스캐폴딩 | 디렉토리/파일 뼈대 생성 | Must |
| TODO 생성 | `TODO.md` 작업 목록 자동 생성 | Must |

### 3.4 Phase 3: 구현 (`vibe code`)
| 기능 | 설명 | 우선순위 |
|-----|------|---------|
| 작업 선택 | `TODO.md`에서 다음 작업 자동 선택 | Must |
| 코드 생성 | 컨텍스트 기반 코드 생성 | Must |
| Diff 미리보기 | 변경사항 확인 후 적용 | Must |
| 문서 업데이트 | `TODO.md`, `CONTEXT.md` 자동 갱신 | Must |

### 3.5 유틸리티 명령어
| 명령어 | 설명 | 우선순위 |
|-------|------|---------|
| `vibe status` | 현재 Phase 및 진행 상황 표시 | Must |
| `vibe chat` | 자유 대화 모드 (문서 수정 없음) | Should |
| `vibe undo` | 마지막 작업 롤백 (Git 기반) | Should |
| `vibe export` | 모든 문서를 하나로 출력 | Could |

## 4. 비기능 요구사항

### 4.1 성능
- 명령어 실행 시 초기 응답: 2초 이내
- 스트리밍 응답 시작: 3초 이내 (네트워크 상태 의존)

### 4.2 사용성
- 컬러풀한 터미널 UI (Rich 라이브러리)
- 명확한 진행 상황 표시 (프로그레스바, 스피너)
- 실수 방지를 위한 확인 프롬프트

### 4.3 확장성
- 다중 AI Provider 지원 (Anthropic, Google, OpenAI)
- 플러그인 아키텍처 고려 (v2.0)

### 4.4 신뢰성
- 모든 파일 변경 전 확인 요청
- Git 기반 롤백 지원
- 네트워크 에러 시 자동 재시도

## 5. 핵심 문서 체계 (Artifacts)

| 카테고리 | 문서 | 역할 | 생성 시점 |
|---------|------|-----|---------|
| **Rules** | `TECH_STACK.md` | 기술 스택 정의 | Phase 0 |
| **Rules** | `RULES.md` | 코딩 규칙 정의 | Phase 0 |
| **Goal** | `PRD.md` | 제품 요구사항 | Phase 1 |
| **Goal** | `USER_STORIES.md` | 사용자 스토리 | Phase 1 |
| **Skeleton** | `TREE.md` | 디렉토리 구조 | Phase 2 |
| **Skeleton** | `SCHEMA.md` | 데이터/API 스키마 | Phase 2 |
| **Memory** | `TODO.md` | 작업 목록 | Phase 2 |
| **Memory** | `CONTEXT.md` | 작업 히스토리 | Phase 3 |

## 6. 기술 제약사항

### 6.1 필수 환경
- Python 3.10 이상
- 인터넷 연결 (AI API 호출)
- AI Provider API 키 (최소 하나)

### 6.2 지원 AI Provider (2026 기준)
| Provider | 모델 | 역할 | 핵심 역량 |
|----------|------|-----|-----------|
| Anthropic | **Claude 4.5 Opus** | Main Agent | 자율 코딩, 아키텍처 설계, Self-Healing |
| Google | **Gemini 3 Pro** | Knowledge Engine | 무한 컨텍스트, 실시간 라이브러리 검증, 전역 감사 |
| OpenAI | GPT-5 | Backup | 대안 모델 |

### 6.3 지원 플랫폼
- macOS, Linux: 완전 지원
- Windows: WSL2 권장

## 7. 성공 지표

### 7.1 MVP 성공 기준
- [ ] Phase 0~3 전체 워크플로우 동작
- [ ] 3가지 AI Provider 모두 연동
- [ ] 기본 프로젝트 유형(backend, frontend, cli) 지원

### 7.2 사용자 경험 지표
- 첫 프로젝트 생성까지 10분 이내
- 문서 생성 후 수정 없이 사용 가능한 비율 70% 이상

## 8. 향후 로드맵

### v1.1
- 추가 프로젝트 유형 (fullstack, backend-web, mobile)
- 플러그인 시스템
- 웹 대시보드

### v2.0
- 로컬 LLM 지원 (Ollama)
- 팀 협업 기능
- IDE 확장 (VS Code)

## 9. 리스크 및 완화 방안

| 리스크 | 영향 | 완화 방안 |
|-------|-----|---------|
| API 비용 증가 | 높음 | 토큰 예산 관리, 캐싱 |
| AI 응답 품질 불일치 | 중간 | 프롬프트 버전 관리, 검증 로직 |
| Provider API 변경 | 중간 | 추상화 레이어, 버전 고정 |
