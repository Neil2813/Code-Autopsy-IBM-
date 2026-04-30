"""
MCP (Model Context Protocol) Integration

This package provides integration with the MCP solution server
for retrieving solved migration examples and patterns.
"""

from app.mcp.client import MCPClient, get_mcp_client
from app.mcp.types import (
    MCPSolution,
    MCPQuery,
    MCPSearchResult,
    MCPViolation
)

__all__ = [
    "MCPClient",
    "get_mcp_client",
    "MCPSolution",
    "MCPQuery",
    "MCPSearchResult",
    "MCPViolation"
]

# Made with Bob
