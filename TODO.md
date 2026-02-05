# TODO - Vibe Coding Helper 구현 작업 목록

## Phase 0: 초기화
- [x] INIT-001: 프로젝트 구조 생성 (Must)
- [x] INIT-002: pyproject.toml 설정 (Must)
- [x] INIT-003: 기본 패키지 구조 생성 (Must)

## Phase 1: 기획
- [x] PLAN-001: PRD 문서 작성 (Must)
- [x] PLAN-002: User Story 작성 (Must)

## Phase 2: 설계
- [x] DESIGN-001: TREE.md 작성 (Must)
- [x] DESIGN-002: SCHEMA.md 작성 (Must)
- [x] DESIGN-003: 프로젝트 스캐폴딩 (Must)

## Phase 3: 구현

### Core 모듈
- [x] CODE-001: exceptions.py 구현 (Must)
  - 파일: src/vibe/core/exceptions.py
- [x] CODE-002: config.py 구현 (Must)
  - 파일: src/vibe/core/config.py
  - 의존: CODE-001
- [x] CODE-003: state.py 구현 (Must)
  - 파일: src/vibe/core/state.py
  - 의존: CODE-001
- [x] CODE-004: context.py 구현 (Must)
  - 파일: src/vibe/core/context.py
- [x] CODE-005: workflow.py 구현 (Must)
  - 파일: src/vibe/core/workflow.py
  - 의존: CODE-002, CODE-003, CODE-004

### Provider 모듈
- [x] CODE-006: base.py (AIProvider 추상 클래스) 구현 (Must)
  - 파일: src/vibe/providers/base.py
- [x] CODE-007: anthropic.py 구현 (Must)
  - 파일: src/vibe/providers/anthropic.py
  - 의존: CODE-006
- [x] CODE-008: google.py 구현 (Must)
  - 파일: src/vibe/providers/google.py
  - 의존: CODE-006
- [x] CODE-009: openai.py 구현 (Must)
  - 파일: src/vibe/providers/openai.py
  - 의존: CODE-006
- [x] CODE-010: factory.py 구현 (Must)
  - 파일: src/vibe/providers/factory.py
  - 의존: CODE-007, CODE-008, CODE-009

### Handler 모듈
- [x] CODE-011: file.py 구현 (Must)
  - 파일: src/vibe/handlers/file.py
  - 의존: CODE-001
- [x] CODE-012: parser.py 구현 (Must)
  - 파일: src/vibe/handlers/parser.py
- [x] CODE-013: git.py 구현 (Should)
  - 파일: src/vibe/handlers/git.py
  - 의존: CODE-001
- [x] CODE-014: scaffold.py 구현 (Must)
  - 파일: src/vibe/handlers/scaffold.py
  - 의존: CODE-011

### CLI UI 모듈
- [x] CODE-015: console.py 구현 (Must)
  - 파일: src/vibe/cli/ui/console.py
- [x] CODE-016: display.py 구현 (Must)
  - 파일: src/vibe/cli/ui/display.py
  - 의존: CODE-015
- [x] CODE-017: prompts.py 구현 (Must)
  - 파일: src/vibe/cli/ui/prompts.py
  - 의존: CODE-015
- [x] CODE-018: progress.py 구현 (Should)
  - 파일: src/vibe/cli/ui/progress.py
  - 의존: CODE-015

### CLI 명령어 (핵심)
- [x] CODE-019: init.py 구현 (Must)
  - 파일: src/vibe/cli/commands/init.py
  - 의존: CODE-002, CODE-003, CODE-005, CODE-010, CODE-016, CODE-017
  - US: US-001, US-002, US-003
- [x] CODE-020: plan.py 구현 (Must)
  - 파일: src/vibe/cli/commands/plan.py
  - 의존: CODE-005, CODE-010
  - US: US-004, US-005, US-006
- [x] CODE-021: design.py 구현 (Must)
  - 파일: src/vibe/cli/commands/design.py
  - 의존: CODE-005, CODE-010
  - US: US-007, US-008
- [x] CODE-022: scaffold.py 명령어 구현 (Must)
  - 파일: src/vibe/cli/commands/scaffold.py
  - 의존: CODE-014, CODE-012
  - US: US-009, US-010
- [x] CODE-023: code.py 구현 (Must)
  - 파일: src/vibe/cli/commands/code.py
  - 의존: CODE-005, CODE-010, CODE-012
  - US: US-011, US-012, US-013, US-014
- [x] CODE-024: status.py 구현 (Must)
  - 파일: src/vibe/cli/commands/status.py
  - 의존: CODE-003
  - US: US-015

### CLI 명령어 (보조)
- [x] CODE-025: chat.py 구현 (Should)
  - 파일: src/vibe/cli/commands/chat.py
  - 의존: CODE-004, CODE-010
  - US: US-016
- [x] CODE-026: undo.py 구현 (Should)
  - 파일: src/vibe/cli/commands/undo.py
  - 의존: CODE-013
  - US: US-017
- [x] CODE-027: test.py 구현 (Must) - NEW (Phase 4)
  - 파일: src/vibe/cli/commands/test.py
  - 의존: CODE-010, DUAL-001
  - 기능: 전역 감사, 엣지 케이스 생성

### CLI 앱 통합
- [x] CODE-028: app.py 완성 (Must)
  - 파일: src/vibe/cli/app.py
  - 의존: CODE-019 ~ CODE-027

### 듀얼 모델 전략 (NEW)
- [x] DUAL-001: orchestrator.py 구현 (Must)
  - 파일: src/vibe/providers/orchestrator.py
  - Claude↔Gemini 협업 오케스트레이션
- [x] DUAL-002: Dual-Track Context 구현 (Must)
  - 파일: src/vibe/core/context.py 확장
  - Hot Memory (Claude) / Cold Storage (Gemini)
- [x] DUAL-003: Self-Healing 워크플로우 구현 (Should)
  - 파일: src/vibe/core/workflow.py 확장
  - SelfHealingWorkflow 클래스, verify_and_heal 편의 함수
  - 에러 발생 시 자동 재시도 및 다국어 지원
- [x] DUAL-004: agent_claude.txt 프롬프트 작성 (Must)
  - 파일: src/vibe/prompts/system/agent_claude.txt
- [x] DUAL-005: analyst_gemini.txt 프롬프트 작성 (Must)
  - 파일: src/vibe/prompts/system/analyst_gemini.txt
- [x] DUAL-006: Phase 4 프롬프트 작성 (Must)
  - 파일: src/vibe/prompts/phases/phase4_test.txt
- [x] DUAL-007: utils 프롬프트 작성 (Should)
  - 파일: src/vibe/prompts/utils/audit_request.txt
  - 파일: src/vibe/prompts/utils/edge_case_gen.txt

### 코드 검증기 (NEW)
- [x] VERIFY-001: base.py 검증기 추상 클래스 (Must)
  - 파일: src/vibe/verifiers/base.py
- [x] VERIFY-002: python.py Python 검증기 (Must)
  - 파일: src/vibe/verifiers/python.py
  - 도구: ast, mypy, ruff, pytest
- [x] VERIFY-003: typescript.py TypeScript 검증기 (Must)
  - 파일: src/vibe/verifiers/typescript.py
  - 도구: tsc, eslint, vitest/jest
- [x] VERIFY-004: factory.py 검증기 팩토리 (Must)
  - 파일: src/vibe/verifiers/factory.py
- [x] VERIFY-005: verify.py CLI 명령어 (Must)
  - 파일: src/vibe/cli/commands/verify.py
- [x] VERIFY-006: code.py에 자동 검증 통합 (Should)
  - Self-Healing 연동

### 프롬프트 & 템플릿
- [x] CODE-028: prompts/loader.py 구현 (Must)
  - 파일: src/vibe/prompts/loader.py
- [x] CODE-029: 시스템 프롬프트 업데이트 (Must)
  - 파일: src/vibe/prompts/system/*.txt
  - base.txt에 듀얼 모델 아키텍처, Phase 정보 추가
  - rules_aware.txt 규칙 준수 지침 보강
- [x] CODE-030: Phase별 프롬프트 업데이트 (Must)
  - 파일: src/vibe/prompts/phases/*.txt
  - Phase 0~3 상세 템플릿 추가
  - Self-Healing 프로세스 문서화
- [x] CODE-031: templates/loader.py 구현 (Must)
  - 파일: src/vibe/templates/loader.py
- [x] CODE-032: 문서 템플릿 작성 (Should)
  - 파일: src/vibe/templates/*.j2
  - TECH_STACK, RULES, PRD, USER_STORIES, TREE, SCHEMA, TODO 템플릿 완성

### 테스트
- [x] TEST-001: config 테스트 확장 (Should)
  - 파일: tests/unit/test_config.py
- [x] TEST-002: state 테스트 (Should)
  - 파일: tests/unit/test_state.py
- [x] TEST-003: parser 테스트 (Should)
  - 파일: tests/unit/test_parser.py
- [x] TEST-004: Provider 테스트 (Should)
  - 파일: tests/unit/providers/test_base.py
- [x] TEST-005: 통합 테스트 - init 플로우 (Should)
  - 파일: tests/integration/test_init_flow.py

### 문서화 & 마무리
- [x] DOC-001: README.md 작성 (Must)
- [x] DOC-002: 설치 및 사용법 문서화 (Should)
  - README.md에 설치 및 사용법 포함

---

## 진행 상황

| Phase | 완료 | 전체 | 진행률 |
|-------|-----|------|--------|
| Phase 0 | 3 | 3 | 100% |
| Phase 1 | 2 | 2 | 100% |
| Phase 2 | 3 | 3 | 100% |
| Phase 3 | 32 | 32 | 100% |
| Phase 4 (Test) | 1 | 1 | 100% |
| 듀얼 모델 | 7 | 7 | 100% |
| 검증기 | 6 | 6 | 100% |
| 테스트 | 5 | 5 | 100% |
| 문서화 | 2 | 2 | 100% |

**전체 진행률: 61/61 (100%)**

---

## 완료!
