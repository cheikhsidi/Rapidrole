#!/bin/bash
set -e

echo "🧪 Running tests..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please run ./scripts/setup.sh first"
    exit 1
fi

# Run linting first
echo "🔍 Running linting..."
uv run ruff check . || echo "⚠️  Linting warnings found"

# Run type checking
echo "🔍 Running type checking..."
uv run mypy . --ignore-missing-imports || echo "⚠️  Type checking warnings found"

# Run tests with coverage
echo "🧪 Running pytest..."
uv run pytest tests/ -v --cov=. --cov-report=html --cov-report=term --cov-report=xml

echo ""
echo "✅ Tests complete!"
echo "📊 Coverage report: htmlcov/index.html"
echo ""

# Check coverage threshold
COVERAGE=$(uv run coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')
THRESHOLD=70

if [ -n "$COVERAGE" ]; then
    echo "📊 Total coverage: ${COVERAGE}%"
    if (( $(echo "$COVERAGE < $THRESHOLD" | bc -l) )); then
        echo "⚠️  Coverage is below ${THRESHOLD}%"
    else
        echo "✅ Coverage meets threshold of ${THRESHOLD}%"
    fi
fi
