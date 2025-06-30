import statistics
import time
from typing import List

import pytest
from fastmcp import FastMCP

from tramlines.guardrail.dsl.evaluator import evaluate_call
from tramlines.proxy import create_guarded_proxy
from tramlines.session import ToolCall


def create_performance_server() -> FastMCP:
    """Server optimized for performance testing with various operations."""
    server = FastMCP(name="PerformanceServer")

    @server.tool
    def fast_add(a: int, b: int) -> int:
        """Fast addition operation."""
        return a + b

    @server.tool
    def medium_computation(n: int) -> int:
        """Medium complexity computation."""
        result = 0
        for i in range(n):
            result += i * i
        return result

    @server.tool
    def slow_operation(duration: float = 0.01) -> str:
        """Simulated slow operation."""
        time.sleep(duration)
        return f"Completed slow operation in {duration}s"

    @server.tool
    def memory_operation(size: int = 1000) -> List[int]:
        """Memory-intensive operation."""
        return list(range(size))

    @server.tool
    def string_operation(text: str = "test") -> str:
        """String processing operation."""
        return text.upper() + text.lower() + str(len(text))

    return server


@pytest.mark.performance
class TestPerformance:
    def test_proxy_creation_is_performant(self, mock_server_manager):
        servers = {
            "perf_server": create_performance_server(),
        }
        for name, server in servers.items():
            mock_server_manager.add_server(name, server)
        config = mock_server_manager.get_config()

        creation_times = []
        for _ in range(10):
            start_time = time.perf_counter()
            create_guarded_proxy(mcp_config=config)
            creation_time = time.perf_counter() - start_time
            creation_times.append(creation_time)

        avg_creation_time_ms = statistics.mean(creation_times) * 1000
        assert avg_creation_time_ms < 100

    def test_middleware_processing_overhead_is_low_for_many_calls(
        self, mock_server_manager
    ):
        mock_server_manager.add_server("performance", create_performance_server())
        config = mock_server_manager.get_config()
        proxy = create_guarded_proxy(mcp_config=config)
        middleware = proxy.middleware[0]

        call_times = []
        for i in range(100):
            tool_call = ToolCall(name="fast_add", arguments={"a": i, "b": i + 1})
            session_id = middleware.sessions.get_session_id()
            history = middleware.sessions.get_history(session_id)

            start_time = time.perf_counter()
            history.add_call(tool_call)
            if middleware.policy:
                evaluate_call(middleware.policy, history)
            call_time = time.perf_counter() - start_time
            call_times.append(call_time)

        avg_call_time_ms = statistics.mean(call_times) * 1000
        assert avg_call_time_ms < 10

    def test_policy_evaluation_performance_with_growing_history(
        self, mock_server_manager, strict_security_policy
    ):
        mock_server_manager.add_server("performance", create_performance_server())
        config = mock_server_manager.get_config()
        proxy = create_guarded_proxy(mcp_config=config, policy=strict_security_policy)
        middleware = proxy.middleware[0]

        session_id = middleware.sessions.get_session_id()
        history = middleware.sessions.get_history(session_id)

        call_times = []
        for i in range(100):
            tool_call = ToolCall(name="fast_add", arguments={"a": i, "b": i + 1})
            history.add_call(tool_call)

            start_time = time.perf_counter()
            evaluate_call(middleware.policy, history)
            call_time = time.perf_counter() - start_time
            call_times.append(call_time)

        avg_call_time_ms = statistics.mean(call_times) * 1000
        assert avg_call_time_ms < 20

    def test_session_management_overhead_is_low(self, mock_server_manager):
        mock_server_manager.add_server("performance", create_performance_server())
        config = mock_server_manager.get_config()
        proxy = create_guarded_proxy(mcp_config=config)
        middleware = proxy.middleware[0]

        session_creation_times = []
        for i in range(100):
            start_time = time.perf_counter()
            session_id = f"session_{i}"
            middleware.sessions.get_history(session_id)
            call_time = time.perf_counter() - start_time
            session_creation_times.append(call_time)

        avg_session_time_ms = statistics.mean(session_creation_times) * 1000
        assert avg_session_time_ms < 5
