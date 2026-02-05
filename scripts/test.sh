#!/bin/bash
# Vibe Coding Helper - 테스트 실행 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Vibe Coding Helper 테스트 ===${NC}"

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

# 가상환경 확인 및 활성화
if [ -d ".venv" ]; then
    echo -e "${YELLOW}가상환경 활성화...${NC}"
    source .venv/bin/activate
fi

# 의존성 설치 확인
echo -e "${YELLOW}의존성 확인 중...${NC}"
pip install -e ".[dev]" --quiet

# 테스트 유형 선택
case "${1:-all}" in
    unit)
        echo -e "${GREEN}단위 테스트 실행...${NC}"
        pytest tests/unit/ -v
        ;;
    integration)
        echo -e "${GREEN}통합 테스트 실행...${NC}"
        pytest tests/integration/ -v
        ;;
    coverage)
        echo -e "${GREEN}커버리지 포함 테스트 실행...${NC}"
        pytest tests/ --cov=src/vibe --cov-report=html --cov-report=term-missing
        echo -e "${GREEN}커버리지 리포트: htmlcov/index.html${NC}"
        ;;
    fast)
        echo -e "${GREEN}빠른 테스트 (마커 없는 테스트만)...${NC}"
        pytest tests/ -v -m "not slow"
        ;;
    all)
        echo -e "${GREEN}전체 테스트 실행...${NC}"
        pytest tests/ -v
        ;;
    *)
        echo -e "${RED}사용법: $0 [unit|integration|coverage|fast|all]${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}테스트 완료!${NC}"
