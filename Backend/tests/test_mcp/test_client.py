"""
Tests for MCP Client

Verifies mock behavior and configuration handling.
"""

import pytest
import asyncio
from datetime import datetime

from app.mcp.client import MCPClient, ConnectionState, get_mcp_client, initialize_mcp_client
from app.mcp.types import (
    MCPQuery,
    MCPViolation,
    MCPStoreSolutionRequest,
    MCPSolutionFeedback
)
from app.config.settings import settings


class TestMCPClientInitialization:
    """Test MCP client initialization and configuration."""
    
    def test_client_initialization_disabled(self):
        """Test client initialization when MCP is disabled."""
        # Temporarily override settings
        original_enabled = settings.mcp_enabled
        settings.mcp_enabled = False
        
        try:
            client = MCPClient()
            assert client.enabled is False
            assert client.mock_mode is True
            assert client._connection_state == ConnectionState.DISCONNECTED
        finally:
            settings.mcp_enabled = original_enabled
    
    def test_client_initialization_mock_mode(self):
        """Test client initialization in mock mode."""
        # Temporarily override settings
        original_enabled = settings.mcp_enabled
        original_mock = settings.mcp_mock_mode
        settings.mcp_enabled = True
        settings.mcp_mock_mode = True
        
        try:
            client = MCPClient()
            assert client.enabled is True
            assert client.mock_mode is True
            assert client.timeout == settings.mcp_timeout
            assert client.max_retries == settings.mcp_max_retries
        finally:
            settings.mcp_enabled = original_enabled
            settings.mcp_mock_mode = original_mock
    
    def test_singleton_pattern(self):
        """Test that get_mcp_client returns singleton."""
        client1 = get_mcp_client()
        client2 = get_mcp_client()
        assert client1 is client2


class TestMCPClientConnection:
    """Test MCP client connection management."""
    
    @pytest.mark.asyncio
    async def test_connect_disabled(self):
        """Test connection when MCP is disabled."""
        original_enabled = settings.mcp_enabled
        settings.mcp_enabled = False
        
        try:
            client = MCPClient()
            await client.connect()
            assert client._connection_state == ConnectionState.DISCONNECTED
            assert client._connection is None
        finally:
            settings.mcp_enabled = original_enabled
    
    @pytest.mark.asyncio
    async def test_connect_mock_mode(self):
        """Test connection in mock mode."""
        original_enabled = settings.mcp_enabled
        original_mock = settings.mcp_mock_mode
        settings.mcp_enabled = True
        settings.mcp_mock_mode = True
        
        try:
            client = MCPClient()
            await client.connect()
            assert client._connection_state == ConnectionState.CONNECTED
            assert client._connection == "mock_connection"
            assert client.is_available() is True
        finally:
            settings.mcp_enabled = original_enabled
            settings.mcp_mock_mode = original_mock
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnection."""
        original_enabled = settings.mcp_enabled
        original_mock = settings.mcp_mock_mode
        settings.mcp_enabled = True
        settings.mcp_mock_mode = True
        
        try:
            client = MCPClient()
            await client.connect()
            assert client.is_available() is True
            
            await client.disconnect()
            assert client._connection_state == ConnectionState.DISCONNECTED
            assert client._connection is None
            assert client.is_available() is False
        finally:
            settings.mcp_enabled = original_enabled
            settings.mcp_mock_mode = original_mock


class TestMCPClientOperations:
    """Test MCP client operations in mock mode."""
    
    @pytest.mark.asyncio
    async def test_search_solutions_disabled(self):
        """Test search when MCP is disabled."""
        original_enabled = settings.mcp_enabled
        settings.mcp_enabled = False
        
        try:
            client = MCPClient()
            query = MCPQuery(
                violation_name="test",
                violation_id="test-001",
                category="deprecated",
                severity="high",
                labels=["api"],
                language="java",
                framework_from="legacy",
                framework_to="modern",
                code_snippet="test code"
            )
            result = await client.search_solutions(query)
            
            assert result.solutions == []
            assert result.total_count == 0
            assert result.search_time_ms == 0.0
        finally:
            settings.mcp_enabled = original_enabled
    
    @pytest.mark.asyncio
    async def test_search_solutions_mock_mode(self):
        """Test search in mock mode."""
        original_enabled = settings.mcp_enabled
        original_mock = settings.mcp_mock_mode
        settings.mcp_enabled = True
        settings.mcp_mock_mode = True
        
        try:
            client = MCPClient()
            await client.connect()
            
            query = MCPQuery(
                violation_name="deprecated-api",
                violation_id="dep-001",
                category="deprecated",
                severity="medium",
                labels=["api"],
                language="java",
                framework_from="legacy",
                framework_to="modern",
                code_snippet="deprecated code",
                limit=5
            )
            result = await client.search_solutions(query)
            
            assert isinstance(result.solutions, list)
            assert result.total_count == 0  # Mock returns empty
            assert result.query == query
        finally:
            settings.mcp_enabled = original_enabled
            settings.mcp_mock_mode = original_mock
    
    @pytest.mark.asyncio
    async def test_store_solution_mock_mode(self):
        """Test storing solution in mock mode."""
        original_enabled = settings.mcp_enabled
        original_mock = settings.mcp_mock_mode
        settings.mcp_enabled = True
        settings.mcp_mock_mode = True
        
        try:
            client = MCPClient()
            await client.connect()
            
            violation = MCPViolation(
                violation_name="test-violation",
                description="Test violation description",
                category="test",
                severity="medium",
                labels=["test"],
                file_path="test.java",
                line_number=10,
                line_end=15,
                code_snippet="old code",
                violation_id="test-viol-001",
                rule_id="rule-001"
            )
            
            request = MCPStoreSolutionRequest(
                violation=violation,
                original_code="old code",
                updated_code="new code",
                explanation="Test solution",
                diff="- old code\n+ new code",
                language="java",
                framework_from="legacy",
                framework_to="modern",
                confidence_score=0.9,
                source="test",
                author="test-user"
            )
            
            solution = await client.store_solution(request)
            
            assert solution is not None
            assert solution.solution_id.startswith("mock_sol_")
            assert solution.violation == violation
            assert solution.original_code == "old code"
            assert solution.updated_code == "new code"
        finally:
            settings.mcp_enabled = original_enabled
            settings.mcp_mock_mode = original_mock
    
    @pytest.mark.asyncio
    async def test_provide_feedback_mock_mode(self):
        """Test providing feedback in mock mode."""
        original_enabled = settings.mcp_enabled
        original_mock = settings.mcp_mock_mode
        settings.mcp_enabled = True
        settings.mcp_mock_mode = True
        
        try:
            client = MCPClient()
            await client.connect()
            
            feedback = MCPSolutionFeedback(
                solution_id="test_sol_123",
                was_helpful=True,
                was_applied=True,
                user_notes="Great solution!",
                user_id="test-user",
                session_id="test-session",
                rating=5,
                modifications_made="None"
            )
            
            result = await client.provide_feedback(feedback)
            assert result is True  # Mock returns True
        finally:
            settings.mcp_enabled = original_enabled
            settings.mcp_mock_mode = original_mock
    
    @pytest.mark.asyncio
    async def test_get_statistics_mock_mode(self):
        """Test getting statistics in mock mode."""
        original_enabled = settings.mcp_enabled
        original_mock = settings.mcp_mock_mode
        settings.mcp_enabled = True
        settings.mcp_mock_mode = True
        
        try:
            client = MCPClient()
            await client.connect()
            
            stats = await client.get_statistics()
            
            assert stats["enabled"] is True
            assert stats["mock_mode"] is True
            assert "connection_state" in stats
            assert stats["total_solutions"] == 0
        finally:
            settings.mcp_enabled = original_enabled
            settings.mcp_mock_mode = original_mock
    
    @pytest.mark.asyncio
    async def test_health_check_mock_mode(self):
        """Test health check in mock mode."""
        original_enabled = settings.mcp_enabled
        original_mock = settings.mcp_mock_mode
        settings.mcp_enabled = True
        settings.mcp_mock_mode = True
        
        try:
            client = MCPClient()
            await client.connect()
            
            health = await client.health_check()
            
            assert health["status"] == "healthy"
            assert health["enabled"] is True
            assert health["mock_mode"] is True
            assert health["connected"] is True
        finally:
            settings.mcp_enabled = original_enabled
            settings.mcp_mock_mode = original_mock


class TestMCPClientHelpers:
    """Test MCP client helper functions."""
    
    @pytest.mark.asyncio
    async def test_initialize_mcp_client(self):
        """Test initialize_mcp_client helper."""
        original_enabled = settings.mcp_enabled
        original_mock = settings.mcp_mock_mode
        settings.mcp_enabled = True
        settings.mcp_mock_mode = True
        
        try:
            client = await initialize_mcp_client()
            assert client is not None
            assert client.is_available() is True
        finally:
            settings.mcp_enabled = original_enabled
            settings.mcp_mock_mode = original_mock


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
