from tramlines.guardrail.dsl.evaluator import evaluate_call
from tramlines.middleware import GuardRailMiddleware
from tramlines.proxy import create_guarded_proxy
from tramlines.session import ToolCall

from .conftest import (
    create_calculator_server,
    create_file_server,
    create_system_server,
)


class TestSystemIntegration:
    def test_end_to_end_pipeline_initializes_correctly_with_multiple_servers(
        self, mock_server_manager, strict_security_policy
    ):
        servers = {
            "calculator": create_calculator_server(),
            "file": create_file_server(),
            "system": create_system_server(),
        }

        for name, server in servers.items():
            mock_server_manager.add_server(name, server)

        config = mock_server_manager.get_config()
        proxy = create_guarded_proxy(
            mcp_config=config,
            policy=strict_security_policy,
            disabled_tools=["very_dangerous_tool"],
        )

        assert proxy is not None
        assert len(config["mcpServers"]) == 3
        assert len(strict_security_policy.rules) == 5
        assert len(servers) == 3

    def test_tool_calls_are_correctly_allowed_or_blocked_by_policy(
        self, mock_server_manager, strict_security_policy
    ):
        calc_server = create_calculator_server()
        file_server = create_file_server()

        mock_server_manager.add_server("calculator", calc_server)
        mock_server_manager.add_server("file", file_server)

        config = mock_server_manager.get_config()
        proxy = create_guarded_proxy(mcp_config=config, policy=strict_security_policy)

        middleware = None
        for mw in proxy.middleware:
            if isinstance(mw, GuardRailMiddleware):
                middleware = mw
                break
        assert middleware is not None

        session_id = middleware.sessions.get_session_id()
        history = middleware.sessions.get_history(session_id)

        safe_call = ToolCall(name="add", arguments={"a": 5, "b": 3})
        history.add_call(safe_call)
        result = evaluate_call(middleware.policy, history)
        assert result.is_allowed

        dangerous_call = ToolCall(
            name="delete_file", arguments={"filename": "important.txt"}
        )
        history.add_call(dangerous_call)
        result = evaluate_call(middleware.policy, history)
        assert result.is_blocked

        for i in range(3):
            safe_call = ToolCall(name="multiply", arguments={"a": i, "b": i + 1})
            history.add_call(safe_call)
        result = evaluate_call(middleware.policy, history)
        assert result.is_allowed

    def test_middleware_correctly_tracks_session_statistics(
        self, mock_server_manager, strict_security_policy
    ):
        calc_server = create_calculator_server()
        mock_server_manager.add_server("calculator", calc_server)

        config = mock_server_manager.get_config()
        proxy = create_guarded_proxy(mcp_config=config, policy=strict_security_policy)

        middleware = None
        for mw in proxy.middleware:
            if isinstance(mw, GuardRailMiddleware):
                middleware = mw
                break
        assert middleware is not None

        session_id = middleware.sessions.get_session_id()
        history = middleware.sessions.get_history(session_id)

        test_calls = [
            ToolCall(name="add", arguments={"a": 1, "b": 2}),
            ToolCall(name="multiply", arguments={"a": 3, "b": 4}),
            ToolCall(name="divide", arguments={"a": 10, "b": 2}),
        ]

        for call in test_calls:
            history.add_call(call)

        final_stats = middleware.get_session_stats()

        assert final_stats["active_sessions"] >= 1
        assert final_stats["total_calls"] >= len(test_calls)
        assert len(history.calls) == len(test_calls)
