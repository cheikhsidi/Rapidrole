# Getting Started with Job Copilot Backend

## 🎯 What You've Got

A production-ready, AI-powered job application copilot backend featuring:

- **Modern Python 3.12** with uv package manager
- **FastAPI** async framework with auto-generated docs
- **LangGraph + LangChain** for agentic AI workflows
- **PostgreSQL + pgvector** for semantic search
- **Redis** for caching and state management
- **OpenAI GPT-4o & Anthropic Claude** for AI capabilities

## 🚀 Quick Start (5 minutes)

### 1. Prerequisites

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Ensure Docker is running
docker --version
```

### 2. Setup

```bash
cd backend

# Automated setup
chmod +x scripts/setup.sh
./scripts/setup.sh

# Configure API keys
cp .env.example .env
# Edit .env and add your OpenAI and Anthropic API keys
```

### 3. Start the Server

```bash
uv run uvicorn main:app --reload
```

### 4. Test It

Visit http://localhost:8000/docs for interactive API documentation.

Or run the example:
```bash
uv run python examples/example_usage.py
```

## 📁 Project Structure

```
backend/
├── api/                    # REST API endpoints
│   ├── jobs.py            # Job search & parsing
│   ├── applications.py    # Application management
│   ├── users.py           # User profiles
│   └── intelligence.py    # AI insights
│
├── agents/                 # AI Agents (LangGraph)
│   ├── job_analyzer.py    # Analyzes job postings
│   ├── resume_optimizer.py # Tailors resumes
│   ├── cover_letter_generator.py # Writes cover letters
│   └── workflow.py        # Orchestrates agents
│
├── embeddings/             # Vector search
│   ├── service.py         # Generate embeddings
│   └── matcher.py         # Semantic matching
│
├── db/                     # Database layer
│   ├── models.py          # SQLAlchemy models
│   └── database.py        # Connection management
│
├── config/                 # Configuration
├── tests/                  # Test suite
├── examples/               # Usage examples
└── main.py                 # Entry point
```

## 🔑 Core Concepts

### 1. Semantic Job Matching

The system uses multi-dimensional embeddings to match candidates with jobs:

```python
# User profile has 3 embeddings:
- skills_embedding      # Technical & soft skills
- experience_embedding  # Work history
- goals_embedding       # Career aspirations

# Jobs have 2 embeddings:
- description_embedding
- requirements_embedding

# Weighted similarity = best match
```

### 2. Agentic Workflow

Applications flow through specialized AI agents:

```
Job Posting → Job Analyzer → Resume Optimizer → Cover Letter Generator → Final Application
```

Each agent is stateless and can be tested independently.

### 3. Vector Search

PostgreSQL with pgvector extension enables fast semantic search:

```sql
-- Find similar jobs using cosine similarity
SELECT * FROM job_postings
ORDER BY description_embedding <=> user_skills_embedding
LIMIT 10;
```

## 🧪 Testing

### Run All Tests
```bash
./scripts/test.sh
```

### Test Individual Agents
```bash
# Test AI agents directly
uv run python examples/test_agents.py
```

### Test API Endpoints
```bash
# Start server first
uv run uvicorn main:app --reload

# In another terminal
uv run python examples/example_usage.py
```

### Import Postman Collection
Import `backend/examples/api_test_collection.json` into Postman for manual testing.

## 📊 Key API Endpoints

### Create User & Profile
```bash
POST /api/v1/users/
POST /api/v1/users/{user_id}/profile
```

### Search Jobs
```bash
GET /api/v1/jobs/search?user_id={id}&limit=10&min_score=0.7
```

### Create Application
```bash
POST /api/v1/applications/
```

### Get AI Insights
```bash
GET /api/v1/intelligence/compatibility/{user_id}/{job_id}
GET /api/v1/intelligence/recommendations/{user_id}
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Required
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Database (auto-configured for local dev)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/job_copilot
REDIS_URL=redis://localhost:6379/0

# Optional
APP_ENV=development
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=60
```

## 🎓 Learning Path

### Day 1: Understand the Basics
1. Read [README.md](README.md) - Overview
2. Read [ARCHITECTURE.md](backend/ARCHITECTURE.md) - System design
3. Run `examples/test_agents.py` - See agents in action

### Day 2: Explore the API
1. Start the server
2. Visit http://localhost:8000/docs
3. Run `examples/example_usage.py`
4. Try the Postman collection

### Day 3: Dive into Code
1. Read `agents/job_analyzer.py` - See how AI agents work
2. Read `embeddings/matcher.py` - Understand semantic search
3. Read `api/jobs.py` - See API implementation

### Day 4: Extend It
1. Add a new agent in `agents/`
2. Create a new API endpoint in `api/`
3. Write tests in `tests/`

## 🚢 Deployment

### Local Development
```bash
docker-compose up -d
uv run uvicorn main:app --reload
```

### Production (Docker)
```bash
docker build -t job-copilot-backend .
docker run -p 8000:8000 --env-file .env job-copilot-backend
```

### Cloud Platforms
See [DEPLOYMENT.md](backend/DEPLOYMENT.md) for:
- AWS ECS/Fargate
- GCP Cloud Run
- Azure Container Instances

## 🐛 Troubleshooting

### Database Connection Error
```bash
# Ensure PostgreSQL is running
docker-compose ps

# Check connection
docker exec job_copilot_db psql -U postgres -d job_copilot -c "SELECT 1;"
```

### Redis Connection Error
```bash
# Ensure Redis is running
docker-compose ps

# Test connection
docker exec job_copilot_redis redis-cli ping
```

### API Key Errors
```bash
# Verify .env file exists and has keys
cat .env | grep API_KEY
```

### Import Errors
```bash
# Reinstall dependencies
uv sync --reinstall
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [uv Documentation](https://docs.astral.sh/uv/)

## 💡 Next Steps

1. **Add Job Scrapers**: Implement scrapers for LinkedIn, Indeed, etc.
2. **Enhance Agents**: Add more sophisticated AI logic
3. **Build Frontend**: Create Chrome extension or web UI
4. **Add Analytics**: Track application success rates
5. **Implement Webhooks**: Real-time notifications
6. **Add Authentication**: JWT-based auth system

## 🤝 Need Help?

- Check [ARCHITECTURE.md](backend/ARCHITECTURE.md) for system design
- Check [DEPLOYMENT.md](backend/DEPLOYMENT.md) for deployment issues
- Review examples in `backend/examples/`
- Check API docs at http://localhost:8000/docs

## ✨ What Makes This Special?

Unlike basic auto-fill tools, this system:

1. **Learns**: Builds persistent knowledge about your career
2. **Thinks**: Multi-agent AI for strategic decisions
3. **Matches**: Semantic search beyond keywords
4. **Scales**: Production-ready architecture
5. **Adapts**: Extensible agent system

---

**Ready to build the future of job applications? Let's go!** 🚀
