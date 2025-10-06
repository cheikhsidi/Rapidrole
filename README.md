# AI-Powered Universal Job Application Copilot - Backend

Production-ready backend for intelligent job application automation using agentic AI architecture.

## Tech Stack

- **API Framework**: FastAPI + Uvicorn (async)
- **AI Orchestration**: LangGraph + LangChain
- **Database**: PostgreSQL + pgvector extension
- **Cache/State**: Redis Cluster
- **LLM Providers**: OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet
- **Embeddings**: OpenAI text-embedding-3-small

## Quick Start

### 🐳 Docker (Recommended)

```bash
cd backend

# 1. Configure API keys
cp .env.docker .env
# Edit .env and add your OPENAI_API_KEY and ANTHROPIC_API_KEY

# 2. Start everything (API + PostgreSQL + Redis)
docker-compose up -d

# 3. Done! API is running
open http://localhost:8000/docs
```

See [Docker Setup Guide](docs/DOCKER_SETUP.md) or [README.docker.md](README.docker.md) for details.

### 💻 Local Development

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
cd backend
uv sync

# Start infrastructure
docker-compose up -d postgres redis

# Run migrations
uv run alembic upgrade head

# Start server
uv run uvicorn main:app --reload
```

## Project Structure

```
backend/
├── api/              # FastAPI routes and endpoints
├── agents/           # LangGraph agent definitions
├── db/               # Database models and migrations
├── embeddings/       # Vector embedding pipeline
├── services/         # Business logic layer
├── config/           # Configuration and settings
├── tests/            # Test suite
└── main.py           # Application entry point
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

Copy `.env.example` to `.env` and configure:
- `DATABASE_URL`
- `REDIS_URL`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`

## Automated Setup

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

This will:
- Install uv if needed
- Install all dependencies
- Start Docker services (PostgreSQL + Redis)
- Run database migrations
- Enable pgvector extension

## Testing

```bash
chmod +x scripts/test.sh
./scripts/test.sh
```

## Key Features

### 🤖 Agentic AI Architecture
- Multi-agent workflow orchestration with LangGraph
- Job analysis, resume optimization, cover letter generation
- Human-in-the-loop capabilities

### 🔍 Semantic Job Matching
- Multi-dimensional vector embeddings
- Weighted similarity scoring
- Skills, experience, and career goals alignment

### 📊 Real-Time Intelligence
- Company research and insights
- Salary benchmarking
- Application tracking and analytics

### ⚡ Production-Ready
- Async/await throughout for high concurrency
- Horizontal scaling support
- Prometheus metrics
- Comprehensive error handling

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design.
