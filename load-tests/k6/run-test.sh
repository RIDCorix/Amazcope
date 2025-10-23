#!/bin/bash

# Quick test runner for k6 load tests
# Validates setup and runs throughput test
set -a; source .env; set +a
set -e

echo "=================================================="
echo "k6 Load Test Runner - SLI-007 Throughput Test"
echo "=================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
TEST_SCRIPT="${1:-throughput-test.js}"
OUTPUT_DIR="./results"

# Check k6 installation
if ! command -v k6 &> /dev/null; then
    echo -e "${RED}Error: k6 is not installed${NC}"
    echo ""
    echo "Install k6:"
    echo "  macOS:  brew install k6"
    echo "  Linux:  See https://k6.io/docs/getting-started/installation/"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ k6 is installed: $(k6 version)${NC}"
echo ""

# Check API health
echo -n "Checking API health at ${BASE_URL}/health ... "
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health" 2>/dev/null || echo "000")

if [ "$HEALTH_STATUS" == "200" ]; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ Failed (HTTP $HEALTH_STATUS)${NC}"
    echo ""
    echo "Start the API server first:"
    echo "  cd ../../backend/src"
    echo "  uv run uvicorn main:app --reload"
    echo ""
    exit 1
fi

# Check test users
echo -n "Checking test users ... "
cd ../../backend/src
USER_COUNT=$(uv run python -c "
from users.models import User
from api.deps import get_async_db_context
from sqlalchemy import select, func
import asyncio

async def count():
    async with get_async_db_context() as db:
        stmt = select(func.count()).select_from(User).where(
            User.email.like('loadtest%')
        )
        result = await db.execute(stmt)
        print(result.scalar_one())

asyncio.run(count())
" 2>/dev/null || echo "0")

cd - > /dev/null

if [ "$USER_COUNT" -ge "3" ]; then
    echo -e "${GREEN}✓ Found $USER_COUNT test users${NC}"
else
    echo -e "${YELLOW}⚠ Only found $USER_COUNT test users${NC}"
    echo ""
    echo "Run setup script to create test users:"
    echo "  ./setup.sh"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create results directory
mkdir -p "$OUTPUT_DIR"

# Determine output file
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT_FILE="${OUTPUT_DIR}/${TEST_SCRIPT%.js}-${TIMESTAMP}.json"

echo ""
echo "=================================================="
echo "Test Configuration"
echo "=================================================="
echo "  Script:      $TEST_SCRIPT"
echo "  Base URL:    $BASE_URL"
echo "  Output:      $OUTPUT_FILE"
echo "  Test Users:  $USER_COUNT"
echo "=================================================="
echo ""

# Prompt to continue
read -p "Press Enter to start test (Ctrl+C to cancel)..."
echo ""

# Run k6 test
echo "Starting k6 load test..."
echo ""

k6 run \
  --out influxdb=${INFLUX_DB_URL:-"http://admin:adminpassword@localhost:8086"}/amazcope_metrics \
  "$TEST_SCRIPT"

TEST_EXIT_CODE=$?

echo ""
echo "=================================================="
echo "Test Complete"
echo "=================================================="
echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Test passed all thresholds${NC}"
else
    echo -e "${RED}✗ Test failed some thresholds (exit code: $TEST_EXIT_CODE)${NC}"
fi

echo ""
echo "Results saved to: $OUTPUT_FILE"
echo ""

# Basic results parsing
if command -v jq &> /dev/null && [ -f "$OUTPUT_FILE" ]; then
    echo "Quick Summary:"
    echo "=============="

    # Total requests
    TOTAL_REQUESTS=$(cat "$OUTPUT_FILE" | jq -s 'map(select(.type=="Point" and .metric=="http_reqs")) | map(.data.value) | add // 0')
    echo -e "  Total Requests:    ${BLUE}${TOTAL_REQUESTS}${NC}"

    # Success rate
    SUCCESS_RATE=$(cat "$OUTPUT_FILE" | jq -s 'map(select(.type=="Point" and .metric=="successful_requests")) | map(.data.value) | add / length * 100 // 0')
    if (( $(echo "$SUCCESS_RATE >= 95" | bc -l) )); then
        echo -e "  Success Rate:      ${GREEN}${SUCCESS_RATE}%${NC}"
    else
        echo -e "  Success Rate:      ${RED}${SUCCESS_RATE}%${NC}"
    fi

    # Average response time
    AVG_DURATION=$(cat "$OUTPUT_FILE" | jq -s 'map(select(.type=="Point" and .metric=="http_req_duration")) | map(.data.value) | add / length // 0')
    echo -e "  Avg Response Time: ${BLUE}${AVG_DURATION}ms${NC}"

    echo ""
fi

echo "View full results with:"
echo "  cat $OUTPUT_FILE | jq"
echo ""
echo "Or analyze with:"
echo "  k6 cloud $OUTPUT_FILE  # Upload to k6 Cloud"
echo ""

exit $TEST_EXIT_CODE
