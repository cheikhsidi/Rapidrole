# Backend Architecture

## Overview

Production-ready AI-powered job application copilot using modern agentic AI architecture.

## Tech Stack

### Core Framework
- **FastAPI**: Async API framework with automatic OpenAPI docs
- **Uvicorn**: ASGI server for high-performance async handling
- **Python 3.12**: Latest Python with improved performance

### AI/ML Layer
- **LangGraph**: State-based agent orchestration
- **LangChain**: LLM integration and tooling
- **OpenAI GPT-4o**: Primary LLM for analysis and generation
- **Anthropic Claude 3.5**: Cover letter generation
- **OpenAI Embeddings**: text-embedding-3-small (768-dim)

### Data Layer
- **PostgreSQL 16**: Primary database
- **pgvector**: Vector similarity search
- **SQLAlchemy 2.0**: Async ORM
- **Alembic**: Database migrations
- **Redis 7**: Caching and session management

## Architecture Patterns

### 1. Async-First Design
All I/O operations use async/await for maximum concurrency:
- Database queries (AsyncSession)
- Redis operations (async Redis client)
- LLM API calls (async clients)
- HTTP endpoints (async route handlers)

### 2. Agent Orchestration
LangGraph manages multi-step workflows:
```
Job Application Flow:
analyze_job → optimize_resume → generate_cover_letter → finalize
```

Each agent is stateless and receives/emits structured state.

### 3. Vector Search Architecture
Multi-dimensional semantic matching:
- User profiles: 3 embeddings (skills, experience, goals)
- Job postings: 2 embeddings (description, requirements)
- Weighted similarity scoring for nuanced matching

### 4. Dependency Injection
FastAPI dependencies for clean separation:
- `get_db()`: Database session management
- `get_redis()`: Redis client access
- Automatic transaction handling

## API Structure

```
/api/v1/
├── /jobs              # Job search and parsing
├── /applications      # Application management
├── /users             # User and profile management
└── /intelligence      # AI insights and recommendations
```

## Agent System

### Job Analyzer Agent
- Extracts structured data from job postings
- Identifies required/preferred skills
- Determines experience level
- Analyzes company culture indicators

### Resume Optimizer Agent
- Tailors resume to job requirements
- Optimizes for ATS systems
- Maintains authenticity
- Provides improvement recommendations

### Cover Letter Generator Agent
- Creates personalized cover letters
- Demonstrates cultural fit
- Highlights relevant experience
- Professional yet warm tone

## Database Schema

### Core Tables
- `users`: User accounts
- `user_profiles`: Profiles with embeddings
- `job_postings`: Jobs with embeddings
- `applications`: Application tracking
- `company_intelligence`: Company research data

### Vector Indexes
- IVFFlat indexes on embedding columns
- Optimized for cosine similarity search
- Automatic index maintenance

## Scalability Considerations

### Horizontal Scaling
- Stateless API servers
- Shared PostgreSQL and Redis
- Load balancer ready

### Performance Optimization
- Connection pooling (DB and Redis)
- Async I/O throughout
- Efficient vector search with indexes
- LLM response caching

### Monitoring
- Prometheus metrics endpoint
- Structured JSON logging
- Health check endpoints
- Request tracing

## Security

- Environment-based secrets
- CORS configuration
- Rate limiting via Redis
- Input validation with Pydantic
- SQL injection prevention (ORM)
- PII encryption at rest

## Development Workflow

1. **Local Development**
   ```bash
   uv sync
   docker-compose up -d
   uv run uvicorn main:app --reload
   ```

2. **Testing**
   ```bash
   uv run pytest tests/ -v --cov
   ```

3. **Migrations**
   ```bash
   uv run alembic revision --autogenerate -m "description"
   uv run alembic upgrade head
   ```

4. **Production Build**
   ```bash
   docker build -t job-copilot-backend .
   docker run -p 8000:8000 job-copilot-backend
   ```

## Future Enhancements

- WebSocket support for real-time updates
- Celery for background job processing
- GraphQL API option
- Multi-tenancy support
- Advanced caching strategies
- A/B testing framework
