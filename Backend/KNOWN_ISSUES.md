# Known Issues and Expected Behaviors

## Overview
This document tracks known issues, expected behaviors, and items that require attention before the backend can be fully operational.

**Last Updated**: 2026-04-30

---

## ✅ Expected Pylint/Import Errors (Pre-Installation)

The following import errors are **EXPECTED** until dependencies are installed:

### 1. Database Models and Configuration
**Files Affected**:
- `scripts/init_db.py`
- `alembic/env.py`
- `app/storage/database.py`
- `app/storage/models.py`

**Errors**:
```
Unable to import 'app.storage.database'
Unable to import 'app.storage.models'
Unable to import 'app.config.settings'
Unable to import 'sqlalchemy'
Unable to import 'alembic'
```

**Reason**: Dependencies not yet installed. These will resolve after running:
```bash
pip install -r requirements.txt
```

### 2. Middleware and FastAPI
**Files Affected**:
- `app/main.py`
- `app/middleware/error_handler.py`
- `app/middleware/logging_middleware.py`

**Errors**:
```
Unable to import 'fastapi'
Unable to import 'starlette'
Unable to import 'pydantic'
```

**Reason**: FastAPI and dependencies not installed yet.

---

## ⚠️ Missing Components (To Be Implemented)

### 1. API Routers (Week 1 - In Progress)
**Status**: Stub files need to be created

**Required Files**:
- `app/api/__init__.py`
- `app/api/v1/__init__.py`
- `app/api/v1/upload.py`
- `app/api/v1/analyze.py`
- `app/api/v1/jobs.py`
- `app/api/v1/query.py`
- `app/api/v1/report.py`

**Impact**: Main application references these but they don't exist yet (commented out in main.py)

### 2. Pydantic Schemas (Week 1 - In Progress)
**Status**: Need to be created from DATA_MODELS.md

**Required Files**:
- `app/schemas/__init__.py`
- `app/schemas/upload.py`
- `app/schemas/analyze.py`
- `app/schemas/job.py`
- `app/schemas/query.py`
- `app/schemas/report.py`
- `app/schemas/common.py`

**Impact**: API endpoints will need these for request/response validation

### 3. Repository Pattern (Week 1 - In Progress)
**Status**: Need to be implemented

**Required Files**:
- `app/storage/repositories.py`

**Impact**: Services will need this for database access abstraction

### 4. LangGraph Agent (Week 2)
**Status**: Not started

**Required Files**:
- `app/agents/agent_state.py`
- `app/agents/modernization_agent.py`
- `app/agents/agent_nodes.py`
- `app/agents/agent_tools.py`

**Impact**: Core analysis functionality depends on this

### 5. MCP Integration (Week 3)
**Status**: Not started

**Required Files**:
- `app/mcp/client.py`
- `app/mcp/types.py`

**Impact**: Solution storage and retrieval functionality

### 6. Parsers (Week 3)
**Status**: Not started

**Required Files**:
- `app/parsers/java_parser.py`
- `app/parsers/cobol_parser.py`
- `app/parsers/rpg_parser.py`
- `app/parsers/mainframe_parser.py`

**Impact**: Language-specific code analysis

### 7. LLM Providers (Week 4)
**Status**: Not started

**Required Files**:
- `app/llm/primary_provider.py`
- `app/llm/groq_provider.py`
- `app/llm/rule_based_provider.py`
- `app/llm/provider_chain.py`

**Impact**: AI-powered analysis and recommendations

### 8. Services (Week 5)
**Status**: Not started

**Required Files**:
- `app/services/upload_service.py`
- `app/services/analysis_service.py`
- `app/services/query_service.py`
- `app/services/report_service.py`

**Impact**: Business logic layer

### 9. Job Queue (Week 5)
**Status**: Not started

**Required Files**:
- `app/queue/job_manager.py`
- `app/queue/worker.py`

**Impact**: Asynchronous job processing

---

## 🔧 Configuration Issues

### 1. Environment Variables
**Status**: Template provided in `.env.example`

**Action Required**: 
- Copy `.env.example` to `.env`
- Fill in actual API keys and configuration values

**Critical Variables**:
```bash
PRIMARY_LLM_API_KEY=your-openai-key
GROQ_LLM_API_KEY=your-groq-key
DATABASE_URL=postgresql://user:pass@localhost:5432/db
REDIS_URL=redis://localhost:6379/0
```

### 2. Database Not Initialized
**Status**: Script created but not run

**Action Required**:
```bash
python scripts/init_db.py
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

---

## 🐛 Potential Runtime Issues

### 1. CORS Configuration
**Current State**: Allows all origins in development

**Production Consideration**: Update `CORS_ORIGINS` in `.env` to specific domains

### 2. Database Connection Pool
**Current State**: Default pool settings

**Production Consideration**: May need tuning for high load:
```python
pool_size=20
max_overflow=10
pool_pre_ping=True
```

### 3. Redis Connection
**Current State**: Not yet implemented

**Action Required**: Add Redis connection management in Week 5

### 4. File Upload Limits
**Current State**: Not configured

**Action Required**: Add file size limits in settings:
```python
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
```

---

## 📝 Documentation Gaps

### 1. API Documentation
**Status**: OpenAPI/Swagger will auto-generate from FastAPI

**Action Required**: Add detailed docstrings to all endpoints

### 2. Deployment Guide
**Status**: Basic Docker setup provided

**Action Required**: Add production deployment guide (Week 6)

### 3. Testing Documentation
**Status**: Not created

**Action Required**: Add testing guide and examples (Week 6)

---

## ✅ Resolution Checklist

### Before First Run
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Copy environment file: `cp .env.example .env`
- [ ] Configure API keys in `.env`
- [ ] Initialize database: `python scripts/init_db.py`
- [ ] Run migrations: `alembic upgrade head`
- [ ] Start Redis: `docker-compose up -d redis`
- [ ] Start PostgreSQL: `docker-compose up -d postgres`

### Before Development
- [ ] Create API router stubs
- [ ] Implement Pydantic schemas
- [ ] Create repository pattern
- [ ] Test database connectivity
- [ ] Test Redis connectivity

### Before Testing
- [ ] Implement LangGraph agent
- [ ] Implement MCP integration
- [ ] Implement at least one parser (Java)
- [ ] Implement LLM provider chain
- [ ] Implement core services

### Before Production
- [ ] Complete all components
- [ ] Write comprehensive tests (>80% coverage)
- [ ] Security audit
- [ ] Performance testing
- [ ] Load testing
- [ ] Documentation review

---

## 🎯 Current Status Summary

**Phase**: Week 1 - Foundation & Setup
**Completion**: ~80% (4.5/5 days)

**Completed**:
✅ Project structure
✅ Configuration management
✅ Database models and migrations
✅ FastAPI application skeleton
✅ Middleware (error handling, logging)
✅ Docker configuration
✅ Comprehensive documentation

**In Progress**:
🔄 API router stubs
🔄 Pydantic schemas
🔄 Repository pattern

**Pending**:
⏳ Database initialization
⏳ First migration
⏳ All Week 2-6 components

---

## 📞 Support

For issues or questions:
1. Check this document first
2. Review IMPLEMENTATION_ROADMAP.md for planned features
3. Check ARCHITECTURE_PLAN.md for design decisions
4. Review DATA_MODELS.md for schema specifications

---

## 🔄 Update History

- **2026-04-30**: Initial document created
  - Documented expected import errors
  - Listed missing components
  - Created resolution checklist