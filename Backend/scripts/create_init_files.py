"""
Script to create __init__.py files in all package directories
"""
import os
from pathlib import Path

# Get the Backend directory
backend_dir = Path(__file__).parent.parent

# List of directories that need __init__.py
directories = [
    "app/config",
    "app/api",
    "app/api/v1",
    "app/agents",
    "app/mcp",
    "app/schemas",
    "app/services",
    "app/parsers",
    "app/analyzers",
    "app/llm",
    "app/storage",
    "app/queue",
    "app/utils",
    "app/middleware",
    "mcp_server",
    "tests",
    "tests/test_agents",
    "tests/test_mcp",
    "tests/test_api",
    "tests/test_services",
    "tests/test_parsers",
    "tests/fixtures",
]

for directory in directories:
    init_file = backend_dir / directory / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""\nPackage initialization\n"""\n')
        print(f"Created: {init_file}")
    else:
        print(f"Already exists: {init_file}")

print("\nAll __init__.py files created successfully!")

# Made with Bob
