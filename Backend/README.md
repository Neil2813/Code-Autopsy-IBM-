# for IBM hackathon
# AI Legacy Modernization Copilot - Backend

## Overview

A **production-ready FastAPI backend** that analyzes legacy codebases (Java, COBOL, RPG, mainframe) and provides AI-powered modernization guidance using **LangGraph** for agent orchestration and **MCP (Model Context Protocol)** for solution storage and retrieval.

### Key Features

✅ **LangGraph AI Agent** - Orchestrates multi-stage analysis pipeline with state management
✅ **MCP Integration** - Stores and retrieves proven modernization solutions (RAG)
✅ **Multi-LLM Fallback** - Primary LLM → Groq → Rule-based analysis
✅ **Comprehensive Java Support** - Deep analysis with framework detection
✅ **Basic Legacy Language Support** - COBOL, RPG, Mainframe/JCL parsing
✅ **Asynchronous Job Processing** - Redis-based queue for scalability
✅ **Flexible Storage** - PostgreSQL (production) + SQLite (development)
✅ **RESTful API** - OpenAPI/Swagger documentation
✅ **Production-Ready** - Error handling, logging, monitoring, Docker support

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI REST API                          │
│  Upload → Analyze → Jobs → Query → Report                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              LangGraph AI Agent (StateGraph)                 │
│  Ingest → Parse → Classify → Analyze → Explain →            │
│  Recommend → Validate                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  MCP Solution Server (Solution Storage & Retrieval)          │
│  Store successful solutions | Retrieve similar patterns      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LLM Provider Chain: Primary → Groq → Rule-Based            │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Framework**: FastAPI 0.109+
- **AI Orchestration**: LangGraph 0.0.40+
- **LLM Integration**: LangChain, OpenAI, Anthropic, Groq
- **Solution Protocol**: MCP (Model Context Protocol) 0.9+
- **Database**: PostgreSQL / SQLite with SQLAlchemy
- **Queue**: Redis for job management
- **Validation**: Pydantic 2.5+
- **Testing**: Pytest with async support
- **Containerization**: Docker & Docker Compose

---

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16+ (or use SQLite for development)
- Redis 7+
- Git

### Installation

```bash
# 1. Clone repository
git clone <repository-url>
cd Backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# 5. Initialize database
python scripts/init_db.py
alembic upgrade head

# 6. Start Redis (in separate terminal)
redis-server

# 7. Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 8. Start background worker (in separate terminal)
python scripts/run_worker.py
```

### Using Docker

```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

---

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Application
APP_NAME=ai-legacy-modernization-copilot
ENVIRONMENT=development
DEBUG=true

# API
API_HOST=0.0.0.0
API_PORT=8000

# Database (choose one)
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:password@localhost:5432/legacy_copilot
# Or for SQLite:
# DATABASE_TYPE=sqlite
# DATABASE_URL=sqlite:///./legacy_copilot.db

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM Providers
PRIMARY_LLM_PROVIDER=openai
PRIMARY_LLM_MODEL=gpt-4
PRIMARY_LLM_API_KEY=sk-...

GROQ_LLM_API_KEY=gsk_...
GROQ_LLM_MODEL=mixtral-8x7b-32768

# MCP
MCP_SERVER_PATH=./mcp_server
MCP_DB_DSN=postgresql://user:password@localhost:5432/mcp_solutions

# Storage
STORAGE_TYPE=local
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=100

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

---

## API Usage

### 1. Upload Code

```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@legacy-app.zip" \
  -F "upload_type=zip"
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "uploaded",
  "file_count": 45,
  "detected_languages": ["java"]
}
```

### 2. Start Analysis

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "analysis_options": {
      "include_dependencies": true,
      "include_security_scan": true,
      "use_mcp_solutions": true
    }
  }'
```

### 3. Check Job Status

```bash
curl http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress_percentage": 65.0,
  "current_stage": "recommendation",
  "stages_completed": ["ingestion", "parsing", "classification", "analysis", "explanation"]
}
```

### 4. Get Results

```bash
curl http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/results
```

### 5. Query Codebase

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "Where is authentication handled?"
  }'
```

### 6. Generate Report

```bash
curl -X POST http://localhost:8000/api/v1/report \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "format": "markdown"
  }'
```

---

## Project Structure

```
Backend/
├── app/
│   ├── main.py                    # FastAPI application
│   ├── config/                    # Configuration management
│   ├── api/v1/                    # API endpoints
│   ├── agents/                    # LangGraph agents
│   ├── mcp/                       # MCP integration
│   ├── schemas/                   # Pydantic models
│   ├── services/                  # Business logic
│   ├── parsers/                   # Language parsers
│   ├── analyzers/                 # Code analyzers
│   ├── llm/                       # LLM providers
│   ├── storage/                   # Database & file storage
│   ├── queue/                     # Job queue
│   ├── utils/                     # Utilities
│   └── middleware/                # Middleware
├── mcp_server/                    # Local MCP solution server
├── tests/                         # Test suite
├── docs/                          # Documentation
├── scripts/                       # Utility scripts
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container image
├── docker-compose.yml             # Multi-container setup
└── README.md                      # This file
```

---

## Documentation

### Planning Documents
- [`ARCHITECTURE_PLAN.md`](ARCHITECTURE_PLAN.md) - Complete system architecture with LangGraph & MCP
- [`DATA_MODELS.md`](DATA_MODELS.md) - All data models, schemas, and database structures
- [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md) - Week-by-week implementation plan

### Technical Documentation
- [`docs/API.md`](docs/API.md) - Complete API reference
- [`docs/LANGGRAPH_DESIGN.md`](docs/LANGGRAPH_DESIGN.md) - LangGraph agent design
- [`docs/MCP_INTEGRATION.md`](docs/MCP_INTEGRATION.md) - MCP integration details
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) - Deployment guide

---

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_agents/test_modernization_agent.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint code
ruff check app/ tests/

# Type checking
mypy app/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---

## LangGraph Agent Workflow

The analysis pipeline is orchestrated by a LangGraph agent with the following stages:

1. **Ingest** - Load and validate uploaded files
2. **Parse** - Extract code structure using language-specific parsers
3. **Classify** - Categorize components (controller, service, etc.)
4. **Analyze** - Detect risks, smells, and issues (queries MCP for similar solutions)
5. **Explain** - Generate human-readable explanations using LLM
6. **Recommend** - Suggest modernization strategies (uses MCP solutions as context)
7. **Validate** - Verify recommendations and store successful solutions to MCP
8. **Report** - Generate final deliverables

**Error Handling**: Each stage has error recovery with retry logic and graceful degradation.

---

## MCP Integration

The backend integrates with an MCP solution server to:

- **Store** successful modernization solutions for future reuse
- **Retrieve** similar past solutions (RAG) to improve recommendations
- **Track** success rates for different modernization patterns
- **Build** organizational knowledge base over time

MCP operations are integrated into the LangGraph agent workflow at the analysis and recommendation stages.

---

## Multi-LLM Fallback Chain

The system implements a robust fallback strategy:

1. **Primary LLM** (OpenAI GPT-4, Anthropic Claude, etc.)
2. **Groq LLM** (Fast, cost-effective fallback)
3. **Rule-Based Analysis** (Deterministic fallback when LLMs unavailable)

This ensures the system continues functioning even if external LLM providers are unavailable.

---

## Supported Languages

### Comprehensive Support
- **Java** - Full AST parsing, framework detection (Spring Boot, Jakarta EE), dependency analysis

### Basic Support
- **COBOL** - Division/section extraction, copybook detection
- **RPG** - Spec parsing, procedure identification
- **Mainframe/JCL** - Job structure, step parsing

---

## Performance

- API response time: < 200ms (excluding analysis)
- Small project analysis: < 2 minutes
- Medium project analysis: < 5 minutes
- Large project analysis: < 15 minutes (with chunking)
- Concurrent jobs: Up to 5 (configurable)

---

## Security

- Input validation on all endpoints
- File upload size limits
- Sanitized file paths
- No code execution
- Secrets in environment variables
- CORS configuration
- Rate limiting (optional)

---

## Monitoring & Logging

- Structured JSON logging
- Request/response logging
- Error tracking
- Job status tracking
- LLM provider usage tracking
- MCP operation logging

---

## Troubleshooting

### Common Issues

**Issue**: Database connection error
```bash
# Check PostgreSQL is running
pg_isready

# Check connection string in .env
echo $DATABASE_URL
```

**Issue**: Redis connection error
```bash
# Check Redis is running
redis-cli ping

# Should return: PONG
```

**Issue**: LLM API errors
```bash
# Check API keys are set
echo $PRIMARY_LLM_API_KEY
echo $GROQ_LLM_API_KEY

# Test fallback chain
curl http://localhost:8000/api/v1/status
```

**Issue**: MCP server not connecting
```bash
# Check MCP server path
echo $MCP_SERVER_PATH

# Test MCP connection
python -m mcp_server.server
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Write tests for new features
- Update documentation
- Use type hints
- Add docstrings to functions

---

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check documentation in [`docs/`](docs/)
- Review planning documents for architecture details

---

## Acknowledgments

- **LangGraph** - AI agent orchestration framework
- **MCP** - Model Context Protocol for solution storage
- **FastAPI** - Modern Python web framework
- **Konveyor/Kai** - Reference architecture inspiration

---

## Roadmap

### Current Version (v1.0)
- ✅ LangGraph agent orchestration
- ✅ MCP integration
- ✅ Multi-LLM fallback
- ✅ Java comprehensive support
- ✅ Basic COBOL/RPG/Mainframe support

### Future Enhancements (v2.0+)
- [ ] Real-time progress updates via WebSocket
- [ ] Advanced architecture visualization
- [ ] Automated code refactoring with approval workflow
- [ ] Additional language support (Python, C#, etc.)
- [ ] IDE plugin integration
- [ ] Team collaboration features
- [ ] Historical analysis comparison

---

**Built with ❤️ for legacy code modernization**
# made with bob
