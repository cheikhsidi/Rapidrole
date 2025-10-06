#!/bin/bash
# Production Readiness Verification Script
# This script verifies that all components are properly configured

set -e

echo "🔍 Job Copilot Backend - Production Readiness Verification"
echo "=========================================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

echo "1. Checking Project Structure..."
echo "--------------------------------"

# Check critical directories
for dir in api agents db embeddings config tests utils scripts examples docs; do
    if [ -d "$dir" ]; then
        check_pass "Directory /$dir exists"
    else
        check_fail "Directory /$dir missing"
    fi
done

# Check critical files
for file in main.py pyproject.toml docker-compose.yml Dockerfile .env.example; do
    if [ -f "$file" ]; then
        check_pass "File $file exists"
    else
        check_fail "File $file missing"
    fi
done

echo ""
echo "2. Checking Python Environment..."
echo "--------------------------------"

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    if [[ "$PYTHON_VERSION" == 3.12* ]]; then
        check_pass "Python 3.12 installed ($PYTHON_VERSION)"
    else
        check_warn "Python version is $PYTHON_VERSION (3.12 recommended)"
    fi
else
    check_fail "Python 3 not found"
fi

# Check uv
if command -v uv &> /dev/null; then
    check_pass "uv package manager installed"
else
    check_fail "uv not installed (run: curl -LsSf https://astral.sh/uv/install.sh | sh)"
fi

echo ""
echo "3. Checking Dependencies..."
echo "--------------------------------"

if [ -f "pyproject.toml" ]; then
    check_pass "pyproject.toml exists"
    
    # Check if dependencies are installed
    if uv run python -c "import fastapi" 2>/dev/null; then
        check_pass "FastAPI installed"
    else
        check_warn "FastAPI not installed (run: uv sync)"
    fi
    
    if uv run python -c "import langchain" 2>/dev/null; then
        check_pass "LangChain installed"
    else
        check_warn "LangChain not installed (run: uv sync)"
    fi
else
    check_fail "pyproject.toml missing"
fi

echo ""
echo "4. Checking Configuration..."
echo "--------------------------------"

if [ -f ".env.example" ]; then
    check_pass ".env.example exists"
else
    check_fail ".env.example missing"
fi

if [ -f ".env" ]; then
    check_pass ".env file exists"
    
    # Check for required variables
    if grep -q "OPENAI_API_KEY" .env; then
        check_pass "OPENAI_API_KEY configured"
    else
        check_warn "OPENAI_API_KEY not set in .env"
    fi
    
    if grep -q "ANTHROPIC_API_KEY" .env; then
        check_pass "ANTHROPIC_API_KEY configured"
    else
        check_warn "ANTHROPIC_API_KEY not set in .env"
    fi
else
    check_warn ".env file not found (copy from .env.example)"
fi

echo ""
echo "5. Checking Docker Setup..."
echo "--------------------------------"

if command -v docker &> /dev/null; then
    check_pass "Docker installed"
    
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        check_pass "Docker Compose available"
    else
        check_fail "Docker Compose not available"
    fi
else
    check_fail "Docker not installed"
fi

echo ""
echo "6. Checking Database Configuration..."
echo "--------------------------------"

if [ -f "alembic.ini" ]; then
    check_pass "Alembic configuration exists"
else
    check_fail "alembic.ini missing"
fi

if [ -d "alembic/versions" ]; then
    MIGRATION_COUNT=$(ls -1 alembic/versions/*.py 2>/dev/null | wc -l)
    if [ "$MIGRATION_COUNT" -gt 0 ]; then
        check_pass "Database migrations exist ($MIGRATION_COUNT found)"
    else
        check_warn "No database migrations found"
    fi
else
    check_fail "alembic/versions directory missing"
fi

echo ""
echo "7. Checking API Endpoints..."
echo "--------------------------------"

# Check if all API modules exist
for module in jobs applications users intelligence; do
    if [ -f "api/${module}.py" ]; then
        check_pass "API module api/${module}.py exists"
    else
        check_fail "API module api/${module}.py missing"
    fi
done

echo ""
echo "8. Checking AI Agents..."
echo "--------------------------------"

for agent in job_analyzer resume_optimizer cover_letter_generator workflow state; do
    if [ -f "agents/${agent}.py" ]; then
        check_pass "Agent agents/${agent}.py exists"
    else
        check_fail "Agent agents/${agent}.py missing"
    fi
done

echo ""
echo "9. Checking Tests..."
echo "--------------------------------"

if [ -f "pytest.ini" ]; then
    check_pass "pytest.ini exists"
else
    check_warn "pytest.ini missing"
fi

if [ -d "tests" ]; then
    TEST_COUNT=$(ls -1 tests/test_*.py 2>/dev/null | wc -l)
    if [ "$TEST_COUNT" -gt 0 ]; then
        check_pass "Test files exist ($TEST_COUNT found)"
    else
        check_warn "No test files found"
    fi
else
    check_fail "tests directory missing"
fi

echo ""
echo "10. Checking Documentation..."
echo "--------------------------------"

for doc in README.md docs/ARCHITECTURE.md docs/DEPLOYMENT.md docs/PRODUCTION_READINESS.md; do
    if [ -f "$doc" ]; then
        check_pass "Documentation $doc exists"
    else
        check_warn "Documentation $doc missing"
    fi
done

echo ""
echo "11. Checking Logging & Monitoring..."
echo "--------------------------------"

if [ -f "utils/logging.py" ]; then
    check_pass "Logging module exists"
else
    check_fail "utils/logging.py missing"
fi

if [ -f "utils/tracing.py" ]; then
    check_pass "Tracing module exists"
else
    check_fail "utils/tracing.py missing"
fi

if [ -f "utils/metrics.py" ]; then
    check_pass "Metrics module exists"
else
    check_fail "utils/metrics.py missing"
fi

echo ""
echo "=========================================================="
echo "Verification Summary"
echo "=========================================================="
echo -e "${GREEN}Passed:${NC} $PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Failed:${NC} $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run: ./scripts/setup.sh (if not done)"
    echo "2. Configure .env with your API keys"
    echo "3. Run: uv run uvicorn main:app --reload"
    echo "4. Visit: http://localhost:8000/docs"
    exit 0
else
    echo -e "${RED}✗ Some critical checks failed${NC}"
    echo "Please fix the issues above before proceeding"
    exit 1
fi
