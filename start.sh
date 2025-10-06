#!/bin/bash
# Quick start script for RapidRole Backend

set -e

echo "🚀 RapidRole Backend - Quick Start"
echo "=================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.docker .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - ANTHROPIC_API_KEY"
    echo ""
    echo "Then run this script again."
    exit 0
fi

# Check if API keys are set
if grep -q "your-openai-key-here" .env || grep -q "your-anthropic-key-here" .env; then
    echo "⚠️  Please update .env with your actual API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - ANTHROPIC_API_KEY"
    echo ""
    exit 1
fi

echo "✅ Environment configured"
echo ""

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check health
echo ""
echo "🔍 Checking service health..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is healthy!"
else
    echo "⚠️  API not responding yet, checking logs..."
    docker-compose logs api | tail -20
fi

echo ""
echo "=================================="
echo "✅ RapidRole Backend is running!"
echo "=================================="
echo ""
echo "📍 API: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo "❤️  Health: http://localhost:8000/health"
echo ""
echo "Useful commands:"
echo "  make logs       - View logs"
echo "  make test       - Run tests"
echo "  make shell      - Access container"
echo "  make down       - Stop services"
echo ""
echo "Happy coding! 🚀"
