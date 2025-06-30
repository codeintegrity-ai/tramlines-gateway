from typing import Any

from fastmcp import FastMCP
from fastmcp.client import Client

from tramlines.guardrail.dsl.types import Policy
from tramlines.logger import logger
from tramlines.middleware import GuardRailMiddleware


def create_guarded_proxy(
    mcp_config: dict[str, Any],
    policy: Policy | None = None,
    disabled_tools: list[str] = [],
) -> FastMCP:
    """
    Create a FastMCP proxy with unified security middleware.

    Args:
        mcp_config: MCP server configuration
        policy: Optional security policy to enforce
        disabled_tools: List of tools to disable

    Returns:
        FastMCP proxy server with security middleware applied
    """
    client: Client = Client(mcp_config)

    # Create the base proxy
    proxy = FastMCP.as_proxy(client)

    # Add single unified middleware
    guard_rail_middleware = GuardRailMiddleware(
        policy=policy, disabled_tools=disabled_tools
    )
    proxy.add_middleware(guard_rail_middleware)

    # Log initialization
    logger.info("GUARD_PROXY_INIT | Initializing unified middleware proxy")
    logger.info(
        f"GUARD_PROXY_INIT | MCP servers: {len(mcp_config.get('mcpServers', {}))}"
    )
    logger.info(f"GUARD_PROXY_INIT | Guard policy loaded: {policy is not None}")
    logger.info(f"GUARD_PROXY_INIT | Disabled tools: {len(disabled_tools)}")

    return proxy


if __name__ == "__main__":
    create_guarded_proxy({}, None, [])
