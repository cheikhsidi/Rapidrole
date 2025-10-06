#!/bin/bash
set -e

echo "🚀 Setting up Job Copilot Backend..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Install dependencies
echo "📚 Installing dependencies..."
uv sync

# Start Docker services
echo "🐳 Starting PostgreSQL and Redis..."
docker-compose up -d

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 5

# Copy env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please update .env with your API keys!"
fi

# Run migrations
echo "🗄️  Running database migrations..."
uv run alembic upgrade head

# Enable pgvector extension
echo "🔧 Enabling pgvector extension..."
docker exec job_copilot_db psql -U postgres -d job_copilot -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "✅ Setup complete!"
echo ""
echo "To start the server:"
echo "  uv run uvicorn main:app --reload"
echo ""
echo "API docs will be available at:"
echo "  http://localhost:8000/docs"
