"""
Shared test fixtures and utilities for integration tests.
"""

from typing import Any, Dict, List

import pytest
from fastmcp import FastMCP

from tramlines.guardrail.dsl.context import call
from tramlines.guardrail.dsl.rules import rule
from tramlines.guardrail.dsl.types import Policy

# ============================================================================
# Test MCP Servers (for direct testing without HTTP)
# ============================================================================


def create_calculator_server() -> FastMCP:
    """Simple calculator server with safe operations."""
    server = FastMCP(name="CalculatorServer")

    @server.tool
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    @server.tool
    def multiply(a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b

    @server.tool
    def divide(a: int, b: int) -> float:
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    return server


def create_file_server() -> FastMCP:
    """File server with dangerous operations that should be blocked."""
    server = FastMCP(name="FileServer")

    @server.tool
    def read_file(filename: str) -> str:
        """Safe: Read file contents."""
        return f"Contents of {filename}"

    @server.tool
    def list_files(directory: str = ".") -> List[str]:
        """Safe: List files in directory."""
        return ["file1.txt", "file2.txt", "file3.txt"]

    @server.tool
    def delete_file(filename: str) -> str:
        """DANGEROUS: Delete a file."""
        return f"File {filename} has been deleted"

    @server.tool
    def delete_all_files() -> str:
        """DANGEROUS: Delete all files."""
        return "All files have been deleted"

    @server.tool
    def format_disk() -> str:
        """DANGEROUS: Format the disk."""
        return "Disk has been formatted"

    return server


def create_system_server() -> FastMCP:
    """System server with administrative operations."""
    server = FastMCP(name="SystemServer")

    @server.tool
    def get_system_info() -> Dict[str, Any]:
        """Safe: Get system information."""
        return {"os": "TestOS", "version": "1.0", "uptime": "1 day", "memory": "8GB"}

    @server.tool
    def list_processes() -> List[str]:
        """Safe: List running processes."""
        return ["process1", "process2", "process3"]

    @server.tool
    def kill_process(pid: int) -> str:
        """DANGEROUS: Kill a process."""
        return f"Process {pid} has been terminated"

    @server.tool
    def shutdown_system() -> str:
        """DANGEROUS: Shutdown the system."""
        return "System is shutting down"

    @server.tool
    def execute_command(command: str) -> str:
        """DANGEROUS: Execute arbitrary command."""
        return f"Executed: {command}"

    return server


# ============================================================================
# Mock Server Manager (for stdio-only testing)
# ============================================================================


class MockServerManager:
    """Mock server manager for stdio-only testing."""

    def __init__(self):
        self.servers: Dict[str, FastMCP] = {}

    def add_server(self, name: str, server: FastMCP) -> None:
        """Add a server to the mock configuration."""
        self.servers[name] = server

    def get_config(self) -> Dict[str, Any]:
        """Get mock MCP configuration for stdio transport."""
        return {
            "mcpServers": {
                name: {
                    "command": "python",
                    "args": ["-m", "mock_server"],
                    "transport": "stdio",
                }
                for name in self.servers.keys()
            }
        }

    def get_server_names(self) -> List[str]:
        """Get list of server names."""
        return list(self.servers.keys())

    def get_server(self, name: str) -> FastMCP | None:
        """Get a server by name."""
        return self.servers.get(name)


# ============================================================================
# Shared Fixtures
# ============================================================================


@pytest.fixture
def strict_security_policy():
    """Strict security policy that blocks dangerous operations."""
    return Policy(
        name="Strict Security Policy",
        description="Blocks all dangerous operations",
        rules=[
            rule("Block file deletion")
            .when(call.name.contains("delete"))
            .block("File deletion is prohibited"),
            rule("Block system shutdown")
            .when(call.name.contains("shutdown"))
            .block("System shutdown is not allowed"),
            rule("Block command execution")
            .when(call.name.contains("execute") | call.name.contains("command"))
            .block("Command execution is forbidden"),
            rule("Block disk operations")
            .when(call.name.contains("format") | call.name.contains("disk"))
            .block("Disk operations are restricted"),
            rule("Block process killing")
            .when(call.name.contains("kill"))
            .block("Process killing is blocked"),
        ],
    )


@pytest.fixture
def mock_server_manager():
    """Fixture that provides a mock server manager for stdio-only testing."""
    return MockServerManager()


@pytest.fixture
def calculator_server():
    """Fixture that provides a calculator server."""
    return create_calculator_server()


@pytest.fixture
def file_server():
    """Fixture that provides a file server."""
    return create_file_server()


@pytest.fixture
def system_server():
    """Fixture that provides a system server."""
    return create_system_server()
