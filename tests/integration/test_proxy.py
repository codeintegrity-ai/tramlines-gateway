"""
Test basic proxy functionality.
"""

from tramlines.middleware import GuardRailMiddleware
from tramlines.proxy import create_guarded_proxy

from .conftest import create_calculator_server, create_file_server, create_system_server


class TestProxyBasics:
    """Test basic proxy functionality without security policies."""

    def test_proxy_creation_with_single_server_is_successful(self, mock_server_manager):
        """Test creating proxy with a single server."""
        server = create_calculator_server()
        mock_server_manager.add_server("calculator", server)

        config = mock_server_manager.get_config()
        proxy = create_guarded_proxy(mcp_config=config)

        assert proxy is not None

    def test_proxy_creation_with_multiple_servers_is_successful(
        self, mock_server_manager
    ):
        """Test creating proxy with multiple servers."""
        servers = {
            "calculator": create_calculator_server(),
            "file": create_file_server(),
            "system": create_system_server(),
        }

        for name, server in servers.items():
            mock_server_manager.add_server(name, server)

        config = mock_server_manager.get_config()
        proxy = create_guarded_proxy(mcp_config=config)

        assert proxy is not None
        assert len(config["mcpServers"]) == 3

    def test_proxy_creation_with_disabled_tools_is_successful(
        self, mock_server_manager
    ):
        """Test proxy with specific tools disabled."""
        server = create_file_server()
        mock_server_manager.add_server("file", server)

        disabled_tools = ["delete_file", "delete_all_files", "format_disk"]

        config = mock_server_manager.get_config()
        proxy = create_guarded_proxy(mcp_config=config, disabled_tools=disabled_tools)

        assert proxy is not None
        middleware = proxy.middleware[0]
        assert isinstance(middleware, GuardRailMiddleware)
        assert middleware.disabled_tools == set(disabled_tools)


class TestMultiServerIntegration:
    """Test integration with multiple different servers."""

    def test_proxy_integrates_correctly_with_multiple_server_types(
        self, mock_server_manager, strict_security_policy
    ):
        """Test proxy with multiple different server types."""
        servers = {
            "calculator": create_calculator_server(),
            "file": create_file_server(),
            "system": create_system_server(),
        }

        # Add all servers
        for name, server in servers.items():
            mock_server_manager.add_server(name, server)

        config = mock_server_manager.get_config()
        proxy = create_guarded_proxy(mcp_config=config, policy=strict_security_policy)

        assert proxy is not None
        assert len(config["mcpServers"]) == len(servers)

    def test_proxy_handles_various_configurations_correctly(
        self, mock_server_manager, strict_security_policy
    ):
        """Test proxy with different configurations for different scenarios."""
        # Add a couple of servers
        mock_server_manager.add_server("calc", create_calculator_server())
        mock_server_manager.add_server("file", create_file_server())

        config = mock_server_manager.get_config()

        # Test different proxy configurations
        configurations = [
            {"mcp_config": config},  # No security
            {"mcp_config": config, "policy": strict_security_policy},  # With policy
            {
                "mcp_config": config,
                "disabled_tools": ["add", "multiply"],
            },  # Disabled tools
            {
                "mcp_config": config,
                "policy": strict_security_policy,
                "disabled_tools": ["read_file"],
            },  # Both
        ]

        for proxy_config in configurations:
            proxy = create_guarded_proxy(**proxy_config)
            assert proxy is not None
