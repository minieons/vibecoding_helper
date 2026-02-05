# Vibe Coding Helper - Makefile

.PHONY: help install dev test test-unit test-integration test-coverage lint format typecheck clean build

# 기본 Python
PYTHON := python3
PIP := pip3

help:
	@echo "Vibe Coding Helper 개발 명령어"
	@echo ""
	@echo "설치:"
	@echo "  make install      - 프로덕션 의존성 설치"
	@echo "  make dev          - 개발 의존성 포함 설치"
	@echo ""
	@echo "테스트:"
	@echo "  make test         - 전체 테스트 실행"
	@echo "  make test-unit    - 단위 테스트만 실행"
	@echo "  make test-int     - 통합 테스트만 실행"
	@echo "  make test-cov     - 커버리지 포함 테스트"
	@echo ""
	@echo "코드 품질:"
	@echo "  make lint         - 린트 검사 (ruff)"
	@echo "  make format       - 코드 포맷팅"
	@echo "  make typecheck    - 타입 체크 (mypy)"
	@echo "  make check        - lint + typecheck"
	@echo ""
	@echo "빌드:"
	@echo "  make build        - wheel 패키지 빌드"
	@echo "  make clean        - 빌드 파일 정리"

# 설치
install:
	$(PIP) install -e .

dev:
	$(PIP) install -e ".[dev]"

# 테스트
test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-int:
	pytest tests/integration/ -v

test-cov:
	pytest tests/ --cov=src/vibe --cov-report=html --cov-report=term-missing
	@echo "커버리지 리포트: htmlcov/index.html"

# 코드 품질
lint:
	ruff check src/ tests/

lint-fix:
	ruff check --fix src/ tests/

format:
	ruff format src/ tests/

typecheck:
	mypy src/vibe

check: lint typecheck

# 빌드
build:
	$(PYTHON) -m build

clean:
	rm -rf dist/ build/ *.egg-info
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	rm -rf htmlcov/ .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
