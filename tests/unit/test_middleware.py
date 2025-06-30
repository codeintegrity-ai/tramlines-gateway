from unittest.mock import AsyncMock, MagicMock, patch

import mcp.types as mt
import pytest
from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import MiddlewareContext

from tramlines.guardrail.dsl.context import call
from tramlines.guardrail.dsl.rules import rule
from tramlines.guardrail.dsl.types import Policy
from tramlines.middleware import GuardRailMiddleware


class TestGuardRailMiddlewareFunctionality:
    @pytest.fixture
    def middleware(self):
        return GuardRailMiddleware()

    @pytest.fixture
    def middleware_with_policy(self):
        policy = Policy(
            name="Test Policy",
            description="Policy for testing",
            rules=[
                rule("Block delete operations")
                .when(call.name == "delete_file")
                .block("Delete operations are not allowed")
            ],
        )
        return GuardRailMiddleware(policy=policy)

    @pytest.fixture
    def middleware_with_disabled_tools(self):
        return GuardRailMiddleware(disabled_tools=["dangerous_tool", "another_tool"])

    @pytest.fixture
    def mock_context(self):
        context = MagicMock(spec=MiddlewareContext)
        context.message = MagicMock()
        context.message.name = "test_tool"
        context.message.arguments = {"arg1": "value1"}
        return context

    @pytest.mark.asyncio
    @patch("tramlines.middleware.get_context")
    async def test_on_call_tool_allows_call_when_no_policy_violated(
        self, mock_get_context, middleware, mock_context
    ):
        mock_fastmcp_context = MagicMock()
        mock_fastmcp_context.session_id = "test_session"
        mock_get_context.return_value = mock_fastmcp_context

        call_next = AsyncMock(return_value=mt.CallToolResult(content=[]))

        result = await middleware.on_call_tool(mock_context, call_next)

        assert isinstance(result, mt.CallToolResult)
        call_next.assert_called_once_with(mock_context)

    @pytest.mark.asyncio
    @patch("tramlines.middleware.get_context")
    async def test_on_call_tool_blocks_call_when_policy_is_violated(
        self, mock_get_context, middleware_with_policy, mock_context
    ):
        mock_fastmcp_context = MagicMock()
        mock_fastmcp_context.session_id = "test_session"
        mock_get_context.return_value = mock_fastmcp_context

        mock_context.message.name = "delete_file"

        call_next = AsyncMock()

        with pytest.raises(
            ToolError, match="Tool blocked by policy: Delete operations are not allowed"
        ):
            await middleware_with_policy.on_call_tool(mock_context, call_next)

        call_next.assert_not_called()

    @pytest.mark.asyncio
    @patch("tramlines.middleware.get_context")
    async def test_on_call_tool_maintains_separate_histories_for_different_sessions(
        self, mock_get_context, middleware
    ):
        call_next = AsyncMock(return_value=mt.CallToolResult(content=[]))

        mock_fastmcp_context1 = MagicMock()
        mock_fastmcp_context1.session_id = "session_1"
        mock_get_context.return_value = mock_fastmcp_context1

        mock_context1 = MagicMock(spec=MiddlewareContext)
        mock_context1.message = MagicMock()
        mock_context1.message.name = "tool1"
        mock_context1.message.arguments = {}

        await middleware.on_call_tool(mock_context1, call_next)

        mock_fastmcp_context2 = MagicMock()
        mock_fastmcp_context2.session_id = "session_2"
        mock_get_context.return_value = mock_fastmcp_context2

        mock_context2 = MagicMock(spec=MiddlewareContext)
        mock_context2.message = MagicMock()
        mock_context2.message.name = "tool2"
        mock_context2.message.arguments = {}

        await middleware.on_call_tool(mock_context2, call_next)

        mock_get_context.return_value = mock_fastmcp_context1
        mock_context1.message.name = "tool1_again"

        await middleware.on_call_tool(mock_context1, call_next)

        stats = middleware.get_session_stats()
        assert stats["active_sessions"] == 2
        assert stats["total_calls"] == 3

        session1_history = middleware.sessions.get_history("session_1")
        session2_history = middleware.sessions.get_history("session_2")
        assert len(session1_history.calls) == 2
        assert len(session2_history.calls) == 1
        assert session1_history.calls[0].name == "tool1"
        assert session1_history.calls[1].name == "tool1_again"
        assert session2_history.calls[0].name == "tool2"

    @pytest.mark.asyncio
    async def test_on_list_tools_returns_all_tools_when_none_are_disabled(
        self, middleware
    ):
        mock_tools = [
            MagicMock(name="tool1"),
            MagicMock(name="tool2"),
            MagicMock(name="tool3"),
        ]

        call_next = AsyncMock(return_value=mock_tools)
        context = MagicMock()

        result = await middleware.on_list_tools(context, call_next)

        assert result == mock_tools
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_on_list_tools_filters_out_disabled_tools(
        self, middleware_with_disabled_tools
    ):
        safe_tool = MagicMock()
        safe_tool.name = "safe_tool"

        dangerous_tool = MagicMock()
        dangerous_tool.name = "dangerous_tool"

        another_tool = MagicMock()
        another_tool.name = "another_tool"

        normal_tool = MagicMock()
        normal_tool.name = "normal_tool"

        mock_tools = [safe_tool, dangerous_tool, another_tool, normal_tool]

        call_next = AsyncMock(return_value=mock_tools)
        context = MagicMock()

        result = await middleware_with_disabled_tools.on_list_tools(context, call_next)

        assert len(result) == 2
        tool_names = {tool.name for tool in result}
        assert tool_names == {"safe_tool", "normal_tool"}

    def test_get_session_stats_returns_correct_statistics(self, middleware):
        stats = middleware.get_session_stats()

        assert "active_sessions" in stats
        assert "total_calls" in stats
        assert "max_calls_per_session" in stats
        assert isinstance(stats["active_sessions"], int)
        assert isinstance(stats["total_calls"], int)

    @pytest.mark.asyncio
    @patch("tramlines.middleware.get_context")
    async def test_middleware_handles_concurrent_calls_from_multiple_sessions_correctly(
        self, mock_get_context, middleware
    ):
        call_next = AsyncMock(return_value=mt.CallToolResult(content=[]))

        alice_context = MagicMock()
        alice_context.session_id = "alice_session"
        alice_mock_context = MagicMock(spec=MiddlewareContext)
        alice_mock_context.message = MagicMock()
        alice_mock_context.message.arguments = {}

        bob_context = MagicMock()
        bob_context.session_id = "bob_session"
        bob_mock_context = MagicMock(spec=MiddlewareContext)
        bob_mock_context.message = MagicMock()
        bob_mock_context.message.arguments = {}

        mock_get_context.return_value = alice_context
        alice_mock_context.message.name = "alice_tool_1"
        await middleware.on_call_tool(alice_mock_context, call_next)

        mock_get_context.return_value = bob_context
        bob_mock_context.message.name = "bob_tool_1"
        await middleware.on_call_tool(bob_mock_context, call_next)

        mock_get_context.return_value = alice_context
        alice_mock_context.message.name = "alice_tool_2"
        await middleware.on_call_tool(alice_mock_context, call_next)

        mock_get_context.return_value = bob_context
        bob_mock_context.message.name = "bob_tool_2"
        await middleware.on_call_tool(bob_mock_context, call_next)

        mock_get_context.return_value = alice_context
        alice_mock_context.message.name = "alice_tool_3"
        await middleware.on_call_tool(alice_mock_context, call_next)

        alice_history = middleware.sessions.get_history("alice_session")
        bob_history = middleware.sessions.get_history("bob_session")

        assert len(alice_history.calls) == 3
        assert len(bob_history.calls) == 2

        assert alice_history.calls[0].name == "alice_tool_1"
        assert alice_history.calls[1].name == "alice_tool_2"
        assert alice_history.calls[2].name == "alice_tool_3"

        assert bob_history.calls[0].name == "bob_tool_1"
        assert bob_history.calls[1].name == "bob_tool_2"
