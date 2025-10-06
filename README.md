# AI-Powered Universal Job Application Copilot

Production-ready backend for an intelligent job application automation platform using modern agentic AI architecture.

## 🎯 Overview

This system leverages LangGraph, LangChain, and state-of-the-art LLMs to create a comprehensive career intelligence platform that:

- **Learns from each application** to improve matching and recommendations
- **Builds persistent context** about your career trajectory
- **Provides strategic guidance** throughout the job search lifecycle
- **Automates repetitive tasks** while maintaining authenticity

## ✨ Key Features

### 🤖 Agentic AI Architecture
- Multi-agent workflow orchestration with LangGraph
- Specialized agents for job analysis, resume optimization, and cover letter generation
- Human-in-the-loop capabilities for quality control

### 🔍 Advanced Semantic Matching
- Multi-dimensional vector embeddings (skills, experience, career goals)
- Weighted similarity scoring for nuanced job-candidate matching
- PostgreSQL + pgvector for production-grade vector search

### 📊 Career Intelligence
- Real-time compatibility analysis
- Skill gap identification
- Strategic application recommendations
- Company research and insights

### 🎮 Freemium + Community Model ⭐ NEW
- **Free Tier**: Fully featured, no paywalls on core functionality
- **Pro Tier**: Optional subscription with advanced features
- **Community**: Activity feed, leaderboards, badges, and streaks
- **Gamification**: Points, challenges, and achievements
- **Agent Marketplace**: Create, share, and remix agent templates
- **Viral Growth**: Referral system with rewards

### ⚡ Production-Ready
- Async/await throughout for high concurrency
- Horizontal scaling support
- Prometheus metrics and structured logging
- Comprehensive error handling and retry logic
- 100% logging coverage with distributed tracing

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     FastAPI Backend                      │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │   Jobs   │  │   Apps   │  │  Users  │  │  Intel  │ │
│  │   API    │  │   API    │  │   API   │  │   API   │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼────────┐ ┌──────▼──────┐ ┌───────▼────────┐
│   LangGraph    │ │  Embeddings │ │   PostgreSQL   │
│    Agents      │ │   Service   │ │   + pgvector   │
│                │ │             │ │                │
│ • Job Analyzer │ │ • OpenAI    │ │ • Users        │
│ • Resume Opt.  │ │   Embeddings│ │ • Jobs         │
│ • Cover Letter │ │ • Semantic  │ │ • Applications │
└────────────────┘ │   Matching  │ │ • Intelligence │
                   └─────────────┘ └────────────────┘
                          │
                   ┌──────▼──────┐
                   │    Redis    │
                   │   Caching   │
                   └─────────────┘
```

## 🚀 Quick Start

```bash
cd backend

# Automated setup (recommended)
./scripts/setup.sh

# Start the server
uv run uvicorn main:app --reload

# Visit API docs
open http://localhost:8000/docs
```

## 📚 Documentation

### Quick Access
- **[QUICK_START.md](QUICK_START.md)** ⭐ - Get running in 5 minutes
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Complete documentation index
- **[PRODUCTION_READY_SUMMARY.md](PRODUCTION_READY_SUMMARY.md)** ⭐ - Validation results

### Core Documentation
- [Backend README](backend/README.md) - Setup and development guide
- [Architecture](backend/docs/ARCHITECTURE.md) - System design and patterns
- [Deployment](backend/docs/DEPLOYMENT.md) - Production deployment guide
- [Production Readiness](backend/docs/PRODUCTION_READINESS.md) - Production checklist
- [Logging Guide](backend/docs/LOGGING_GUIDE.md) ⭐ - Comprehensive logging documentation
- [Getting Started](backend/docs/GETTING_STARTED.md) - Detailed setup guide
- [API Examples](backend/examples/) - Usage examples

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **API Framework** | FastAPI + Uvicorn (async) |
| **AI Orchestration** | LangGraph + LangChain |
| **LLM Providers** | OpenAI GPT-4o, Anthropic Claude 3.5 |
| **Embeddings** | OpenAI text-embedding-3-small (768-dim) |
| **Database** | PostgreSQL 16 + pgvector |
| **Cache/State** | Redis 7 |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Package Manager** | uv |
| **Python** | 3.12+ |

## 📦 Project Structure

```
backend/
├── api/                    # FastAPI routes
│   ├── jobs.py            # Job search and parsing
│   ├── applications.py    # Application management
│   ├── users.py           # User and profile management
│   └── intelligence.py    # AI insights and recommendations
├── agents/                 # LangGraph agent definitions
│   ├── job_analyzer.py    # Job posting analysis
│   ├── resume_optimizer.py # Resume tailoring
│   ├── cover_letter_generator.py # Cover letter creation
│   ├── workflow.py        # Agent orchestration
│   └── state.py           # State management
├── db/                     # Database layer
│   ├── models.py          # SQLAlchemy models
│   └── database.py        # Connection management
├── embeddings/             # Vector search
│   ├── service.py         # Embedding generation
│   └── matcher.py         # Semantic matching
├── config/                 # Configuration
│   └── settings.py        # Environment settings
├── tests/                  # Test suite
├── examples/               # Usage examples
├── scripts/                # Utility scripts
├── alembic/                # Database migrations
├── main.py                 # Application entry point
├── pyproject.toml          # Dependencies (uv)
└── docker-compose.yml      # Local infrastructure
```

## 🔑 Key Endpoints

### Core Features
**Jobs API** - Job search and analysis
- `POST /api/v1/jobs/parse` - Parse job posting
- `POST /api/v1/jobs/analyze/{job_id}` - AI analysis
- `GET /api/v1/jobs/search` - Semantic search
- `GET /api/v1/jobs/{job_id}` - Job details

**Applications API** - Application management
- `POST /api/v1/applications/` - Create application
- `GET /api/v1/applications/{id}` - Get details
- `PATCH /api/v1/applications/{id}/status` - Update status
- `GET /api/v1/applications/user/{user_id}` - List applications

**Users API** - User and profile management
- `POST /api/v1/users/` - Create user
- `GET /api/v1/users/{id}` - Get user
- `POST /api/v1/users/{id}/profile` - Create/update profile
- `GET /api/v1/users/{id}/profile` - Get profile

**Intelligence API** - AI insights
- `GET /api/v1/intelligence/compatibility/{user_id}/{job_id}` - Compatibility
- `GET /api/v1/intelligence/recommendations/{user_id}` - Recommendations
- `GET /api/v1/intelligence/insights/{application_id}` - Insights

### Community & Gamification ⭐ NEW
**Community API** - Social features
- `GET /api/v1/community/feed` - Activity feed
- `GET /api/v1/community/leaderboard` - Leaderboards
- `GET /api/v1/community/badges/{user_id}` - User badges
- `GET /api/v1/community/stats` - Community stats

**Templates API** - Agent marketplace
- `POST /api/v1/templates/` - Create template
- `GET /api/v1/templates/` - Browse templates
- `GET /api/v1/templates/{id}` - Get template
- `POST /api/v1/templates/{id}/vote` - Vote on template
- `POST /api/v1/templates/{id}/remix` - Remix template

**Challenges API** - Gamification
- `GET /api/v1/challenges/current` - Active challenges
- `GET /api/v1/challenges/{user_id}/progress` - User progress
- `POST /api/v1/challenges/{id}/complete` - Complete challenge

**Referrals API** - Viral growth
- `POST /api/v1/referrals/invite` - Create referral
- `GET /api/v1/referrals/{user_id}` - Get referrals
- `POST /api/v1/referrals/{id}/claim` - Claim reward

### Monetization ⭐ NEW
**Subscriptions API** - Pro tier management
- `POST /api/v1/subscriptions/subscribe` - Subscribe to Pro
- `GET /api/v1/subscriptions/status/{user_id}` - Check status
- `POST /api/v1/subscriptions/cancel/{user_id}` - Cancel subscription
- `POST /api/v1/subscriptions/trial/{user_id}` - Start trial

## 🧪 Testing

```bash
# Run all tests
./scripts/test.sh

# Run specific tests
uv run pytest tests/test_api.py -v

# Test agents directly
uv run python examples/test_agents.py
```

## 🔐 Security Features

- Environment-based secrets management
- CORS configuration for extension security
- Rate limiting via Redis
- Input validation with Pydantic
- SQL injection prevention (ORM)
- PII encryption at rest

## 📈 Scalability

- **Horizontal scaling**: Stateless API servers
- **Connection pooling**: Optimized DB and Redis connections
- **Async I/O**: Non-blocking operations throughout
- **Vector indexes**: Efficient similarity search
- **Caching**: LLM response and embedding caching

## 🎯 Competitive Advantages

Unlike basic auto-fill tools (LazyApply, Simplify), this copilot provides:

1. **Persistent Career Intelligence** - Builds knowledge graph of your career
2. **Multi-Dimensional Matching** - Beyond keyword matching
3. **Strategic Guidance** - Skill gap analysis and career trajectory mapping
4. **Proactive Insights** - Optimal application timing and company intelligence
5. **Quality Over Quantity** - Authentic, tailored applications

## 🚢 Deployment

### Docker
```bash
docker build -t job-copilot-backend .
docker run -p 8000:8000 job-copilot-backend
```

### Cloud Platforms
- AWS ECS/Fargate
- GCP Cloud Run
- Azure Container Instances

See [DEPLOYMENT.md](backend/DEPLOYMENT.md) for detailed instructions.

## 📊 Monitoring

- **Metrics**: Prometheus endpoint at `/metrics`
- **Health Checks**: `/health`, `/health/db`, `/health/redis`
- **Logging**: Structured JSON logs with request tracing

## 🤝 Contributing

This is a production-ready foundation. To extend:

1. Add new agents in `agents/`
2. Create new API endpoints in `api/`
3. Extend database models in `db/models.py`
4. Add tests in `tests/`

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [LangChain](https://www.langchain.com/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [pgvector](https://github.com/pgvector/pgvector)
- [uv](https://github.com/astral-sh/uv)

---

**Ready to revolutionize job applications with AI? Get started now!** 🚀
