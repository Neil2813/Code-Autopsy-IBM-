# MCP (Model Context Protocol) Layer

## Overview

The MCP layer provides a knowledge base for storing and retrieving code modernization solutions. It enables the system to learn from past migrations and provide relevant solutions for similar code patterns.

## Current Status: MVP MOCK IMPLEMENTATION

**IMPORTANT**: This is a **MOCK-ONLY** implementation for MVP. All operations return empty or simulated results.

### Configuration

MCP is controlled by settings in `app/config/settings.py`:

```python
mcp_enabled: bool = False          # Enable/disable MCP functionality
mcp_mock_mode: bool = True         # Use mock responses (MVP default)
mcp_server_path: str = "./mcp_server"
mcp_db_dsn: str = "sqlite:///./mcp.db"
mcp_timeout: int = 30              # Connection timeout in seconds
mcp_max_retries: int = 3           # Maximum connection retry attempts
mcp_retry_delay: int = 5           # Delay between retries in seconds
```

### Architecture

```
app/mcp/
├── __init__.py          # Package initialization
├── client.py            # MCP client implementation
├── types.py             # Pydantic models for MCP data structures
└── README.md            # This file
```

## Components

### 1. MCP Client (`client.py`)

The `MCPClient` class provides the interface for interacting with the MCP solution server.

#### Key Features:
- **Connection Management**: Handles connection lifecycle with retry logic
- **Connection States**: DISCONNECTED, CONNECTING, CONNECTED, ERROR
- **Mock Mode**: Returns simulated data for MVP without real backend
- **Graceful Degradation**: Returns empty results on errors rather than failing

#### Main Methods:

```python
# Connection
await client.connect()              # Establish connection
await client.disconnect()           # Close connection
client.is_available()               # Check if connected
await client.health_check()         # Get health status

# Search
result = await client.search_solutions(query)  # Search for solutions

# Storage
solution = await client.store_solution(request)  # Store new solution

# Feedback
success = await client.provide_feedback(feedback)  # Record feedback

# Statistics
stats = await client.get_statistics()  # Get usage statistics
```

#### Usage Example:

```python
from app.mcp.client import initialize_mcp_client
from app.mcp.types import MCPQuery

# Initialize client
client = await initialize_mcp_client()

# Search for solutions
query = MCPQuery(
    violation_name="deprecated-api",
    language="java",
    code_snippet="old code pattern",
    limit=5
)
result = await client.search_solutions(query)

# Process results
for solution in result.solutions:
    print(f"Solution: {solution.solution_id}")
    print(f"Original: {solution.original_code}")
    print(f"Updated: {solution.updated_code}")
```

### 2. MCP Types (`types.py`)

Pydantic models defining the data structures for MCP operations.

#### Core Types:

- **MCPViolation**: Represents a code violation
- **MCPSolution**: A complete solution with code, explanation, and metadata
- **MCPQuery**: Search parameters for finding solutions
- **MCPSearchResult**: Search results with metadata
- **MCPStoreSolutionRequest**: Request to store a new solution
- **MCPSolutionFeedback**: User feedback on solution effectiveness
- **MCPBatchStorageRequest**: Bulk storage request
- **MCPBatchStorageResult**: Bulk storage results

#### Key Fields for Real Implementation:

**MCPSolution**:
- `embedding_vector`: Code embedding for similarity search
- `embedding_model`: Model used for embedding
- `confidence_score`: AI confidence in solution
- `success_rate`: Based on user feedback
- `times_used`, `times_helpful`, `times_applied`: Usage metrics

**MCPQuery**:
- `use_semantic_search`: Enable vector similarity search
- `similarity_threshold`: Minimum similarity score
- `sort_by`: Sort field (relevance, confidence, success_rate, etc.)

## MVP Behavior

### When MCP is Disabled (`mcp_enabled=False`):
- All operations return immediately with empty results
- No connection attempts are made
- Logs indicate MCP is disabled

### When MCP is in Mock Mode (`mcp_mock_mode=True`):
- Simulates successful connection
- `search_solutions()`: Returns empty list
- `store_solution()`: Returns mock solution object with ID
- `provide_feedback()`: Returns True (simulated success)
- `get_statistics()`: Returns mock statistics
- `health_check()`: Returns healthy status

## Real Implementation Requirements

To implement real MCP functionality:

### 1. Backend Infrastructure

```python
# Required components:
- Vector database (e.g., Pinecone, Weaviate, Chroma)
- Embedding model (e.g., CodeBERT, GraphCodeBERT)
- PostgreSQL or similar for metadata
- Redis for caching
```

### 2. Code Changes

**In `client.py`**:
```python
# Replace TODO sections with:
from mcp import Client  # Actual MCP library
import numpy as np
from sentence_transformers import SentenceTransformer

class MCPClient:
    def __init__(self):
        # ... existing code ...
        self.embedding_model = SentenceTransformer('microsoft/codebert-base')
        self.vector_db = None  # Initialize vector DB client
    
    async def connect(self):
        # Implement real connection
        self._connection = await Client.connect(self.db_dsn)
        self.vector_db = await VectorDB.connect(...)
    
    async def search_solutions(self, query):
        # Generate embedding for code snippet
        if query.code_snippet:
            embedding = self.embedding_model.encode(query.code_snippet)
            # Perform vector similarity search
            results = await self.vector_db.search(
                embedding,
                threshold=query.similarity_threshold,
                limit=query.limit
            )
        # Filter by metadata
        # Rank by confidence and success rate
        # Return results
```

### 3. Database Schema

```sql
-- Solutions table
CREATE TABLE mcp_solutions (
    solution_id VARCHAR(255) PRIMARY KEY,
    violation_id VARCHAR(255),
    original_code TEXT,
    updated_code TEXT,
    explanation TEXT,
    language VARCHAR(50),
    framework_from VARCHAR(100),
    framework_to VARCHAR(100),
    confidence_score FLOAT,
    times_used INT DEFAULT 0,
    times_helpful INT DEFAULT 0,
    times_applied INT DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    embedding_vector VECTOR(768),  -- For vector search
    metadata JSONB
);

-- Feedback table
CREATE TABLE mcp_feedback (
    feedback_id SERIAL PRIMARY KEY,
    solution_id VARCHAR(255) REFERENCES mcp_solutions(solution_id),
    was_helpful BOOLEAN,
    was_applied BOOLEAN,
    user_notes TEXT,
    timestamp TIMESTAMP,
    user_id VARCHAR(255),
    session_id VARCHAR(255)
);

-- Indexes
CREATE INDEX idx_solutions_language ON mcp_solutions(language);
CREATE INDEX idx_solutions_framework ON mcp_solutions(framework_from, framework_to);
CREATE INDEX idx_solutions_success_rate ON mcp_solutions(success_rate DESC);
CREATE INDEX idx_vector_search ON mcp_solutions USING ivfflat (embedding_vector vector_cosine_ops);
```

### 4. Configuration

Update `.env`:
```bash
# Enable real MCP
MCP_ENABLED=true
MCP_MOCK_MODE=false

# Vector database
MCP_VECTOR_DB_URL=postgresql://user:pass@localhost:5432/mcp
MCP_VECTOR_DB_TYPE=pgvector

# Embedding model
MCP_EMBEDDING_MODEL=microsoft/codebert-base
MCP_EMBEDDING_DIMENSION=768

# Connection settings
MCP_TIMEOUT=30
MCP_MAX_RETRIES=3
MCP_RETRY_DELAY=5
```

## Testing

Run MCP tests:
```bash
cd Backend
python -m pytest tests/test_mcp/test_client.py -v
```

All tests should pass in mock mode.

## Integration Points

The MCP layer integrates with:

1. **Analysis Service**: Stores solutions from successful migrations
2. **LLM Providers**: Retrieves similar solutions to guide code generation
3. **Agent System**: Uses solutions as examples in prompts
4. **API Endpoints**: Exposes search and feedback capabilities

## Future Enhancements

1. **Semantic Search**: Vector similarity for code patterns
2. **Solution Ranking**: ML-based ranking by relevance and success
3. **Batch Operations**: Bulk import/export of solutions
4. **Analytics Dashboard**: Visualize solution usage and effectiveness
5. **Solution Versioning**: Track solution evolution over time
6. **Multi-tenancy**: Separate solution spaces per organization
7. **Solution Validation**: Automated testing of stored solutions
8. **Collaborative Filtering**: Recommend solutions based on user patterns

## Troubleshooting

### MCP Not Working
1. Check `mcp_enabled` setting
2. Verify `mcp_mock_mode` is set correctly
3. Check logs for connection errors
4. Verify database connectivity (when real mode)

### Empty Search Results
- In mock mode: Expected behavior
- In real mode: Check database has solutions, verify query parameters

### Connection Timeouts
- Increase `mcp_timeout` setting
- Check network connectivity to MCP server
- Verify MCP server is running

## References

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Vector Databases for Code Search](https://arxiv.org/abs/2002.08653)
- [CodeBERT: Pre-trained Model for Programming Languages](https://arxiv.org/abs/2002.08155)

---

**Last Updated**: 2026-05-02  
**Status**: MVP Mock Implementation  
**Next Steps**: Implement real vector search and storage