"""
Test security policy enforcement.
"""

from tramlines.guardrail.dsl.evaluator import evaluate_call
from tramlines.middleware import GuardRailMiddleware
from tramlines.proxy import create_guarded_proxy
from tramlines.session import ToolCall

from .conftest import create_file_server, create_system_server


class TestSecurityPolicies:
    """Test security policy enforcement."""

    def test_strict_policy_is_applied_and_blocks_dangerous_tools(
        self, mock_server_manager, strict_security_policy
    ):
        """Test that strict policy blocks dangerous operations."""
        servers = {"file": create_file_server(), "system": create_system_server()}

        for name, server in servers.items():
            mock_server_manager.add_server(name, server)

        config = mock_server_manager.get_config()
        proxy = create_guarded_proxy(mcp_config=config, policy=strict_security_policy)

        assert proxy is not None

        # Verify policy is attached
        for middleware in proxy.middleware:
            if isinstance(middleware, GuardRailMiddleware):
                assert middleware.policy is not None
                assert len(middleware.policy.rules) == 5
                break

    def test_policy_can_be_combined_with_disabled_tools(
        self, mock_server_manager, strict_security_policy
    ):
        """Test combining security policy with disabled tools."""
        server = create_system_server()
        mock_server_manager.add_server("system", server)

        disabled_tools = ["list_processes", "get_system_info"]  # Disable safe tools

        config = mock_server_manager.get_config()
        proxy = create_guarded_proxy(
            mcp_config=config,
            policy=strict_security_policy,
            disabled_tools=disabled_tools,
        )

        assert proxy is not None
        for middleware in proxy.middleware:
            if isinstance(middleware, GuardRailMiddleware):
                assert middleware.disabled_tools == set(disabled_tools)
                break

    def test_policy_rules_are_evaluated_correctly_for_safe_and_dangerous_calls(
        self, mock_server_manager, strict_security_policy
    ):
        """Test that policy rules are properly evaluated."""
        server = create_file_server()
        mock_server_manager.add_server("file", server)

        config = mock_server_manager.get_config()
        proxy = create_guarded_proxy(mcp_config=config, policy=strict_security_policy)

        # Get middleware for testing
        middleware = None
        for mw in proxy.middleware:
            if isinstance(mw, GuardRailMiddleware):
                middleware = mw
                break

        assert middleware is not None
        assert middleware.policy is not None

        # Test rule evaluation directly
        session_id = middleware.sessions.get_session_id()
        history = middleware.sessions.get_history(session_id)

        # Test safe call
        safe_call = ToolCall(name="read_file", arguments={"filename": "test.txt"})
        history.add_call(safe_call)
        result = evaluate_call(middleware.policy, history)
        assert result.is_allowed

        # Test dangerous call
        dangerous_call = ToolCall(
            name="delete_file", arguments={"filename": "test.txt"}
        )
        history.add_call(dangerous_call)
        result = evaluate_call(middleware.policy, history)
        assert result.is_blocked
