"""
Test error handling and edge cases.
"""

import pytest
from tramlines.middleware import GuardRailMiddleware
from tramlines.proxy import create_guarded_proxy


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_proxy_creation_does_not_fail_with_invalid_server_config(self):
        """Test proxy behavior with invalid server configuration."""
        # Create config with invalid server configuration
        config = {
            "mcpServers": {
                "invalid": {
                    "command": "nonexistent_command",
                    "args": ["--invalid-arg"],
                    "transport": "stdio",
                }
            }
        }

        # Proxy creation should handle this gracefully
        proxy = create_guarded_proxy(mcp_config=config)
        assert proxy is not None

    def test_proxy_creation_handles_various_invalid_configurations(self):
        """Test proxy with various invalid configurations."""
        invalid_configs = [
            {},  # Empty config
            {"mcpServers": {}},  # Empty servers
        ]

        for config in invalid_configs:
            with pytest.raises(ValueError):
                create_guarded_proxy(mcp_config=config)

        with pytest.raises(Exception):
            create_guarded_proxy(mcp_config={"invalid": "config"})

    def test_middleware_initializes_correctly_without_a_policy(self):
        """Test middleware behavior with no policy loaded."""
        config = {
            "mcpServers": {
                "test": {
                    "command": "python",
                    "args": ["-m", "test_server"],
                    "transport": "stdio",
                }
            }
        }

        proxy = create_guarded_proxy(mcp_config=config, policy=None)
        assert proxy is not None

        # Find middleware
        middleware = None
        for mw in proxy.middleware:
            if isinstance(mw, GuardRailMiddleware):
                middleware = mw
                break

        assert middleware is not None
        assert middleware.policy is None

    def test_middleware_initializes_correctly_with_empty_disabled_tools_list(self):
        """Test middleware with empty disabled tools list."""
        config = {
            "mcpServers": {
                "test": {
                    "command": "python",
                    "args": ["-m", "test_server"],
                    "transport": "stdio",
                }
            }
        }

        proxy = create_guarded_proxy(mcp_config=config, disabled_tools=[])
        assert proxy is not None

        # Find middleware
        middleware = None
        for mw in proxy.middleware:
            if isinstance(mw, GuardRailMiddleware):
                middleware = mw
                break

        assert middleware is not None
        assert middleware.disabled_tools == set()
