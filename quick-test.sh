#!/bin/bash
# Quick test runner - Run this from anywhere in the project

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       Amazcope Test Runner                     ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo ""

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"
BACKEND_SRC="$PROJECT_ROOT/backend/src"

# Change to backend/src directory
cd "$BACKEND_SRC" || exit 1

echo -e "${GREEN}📍 Running from:${NC} $BACKEND_SRC"
echo ""

# Run tests based on argument
case "$1" in
    "marketplace")
        echo -e "${GREEN}🧪 Running marketplace integration test...${NC}"
        pytest ../tests/test_marketplace_integration.py -v -s
        ;;
    "tracking")
        echo -e "${GREEN}🧪 Running product tracking test...${NC}"
        pytest ../tests/test_product_tracking.py -v -s
        ;;
    "all")
        echo -e "${GREEN}🧪 Running all tests...${NC}"
        pytest ../tests/ -v -s
        ;;
    "coverage")
        echo -e "${GREEN}📊 Running tests with coverage...${NC}"
        pytest ../tests/ --cov=. --cov-report=html --cov-report=term
        echo ""
        echo -e "${GREEN}✅ Coverage report: file://$BACKEND_SRC/htmlcov/index.html${NC}"
        ;;
    "postgres")
        echo -e "${GREEN}🐘 Running tests with PostgreSQL...${NC}"
        TEST_USE_SQLITE=false pytest ../tests/ -v -s
        ;;
    *)
        echo -e "${GREEN}Usage:${NC}"
        echo "  ./quick-test.sh marketplace  - Run marketplace integration test"
        echo "  ./quick-test.sh tracking     - Run product tracking test"
        echo "  ./quick-test.sh all          - Run all tests"
        echo "  ./quick-test.sh coverage     - Run with coverage report"
        echo "  ./quick-test.sh postgres     - Run with PostgreSQL"
        echo ""
        echo -e "${GREEN}Running all tests by default...${NC}"
        pytest ../tests/ -v -s
        ;;
esac

echo ""
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
