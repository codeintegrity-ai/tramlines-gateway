import time
from datetime import datetime, timedelta
from typing import Dict

import mcp.types as mt
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_context
from fastmcp.server.middleware import Middleware, MiddlewareContext

from tramlines.guardrail.dsl.evaluator import evaluate_call
from tramlines.guardrail.dsl.types import Policy
from tramlines.logger import logger
from tramlines.session import CallHistory, CallStatus, ToolCall


class SessionManager:
    """Manages session-based call histories with automatic cleanup."""

    def __init__(self, max_calls_per_session: int = 30, cleanup_hours: int = 24):
        self.max_calls_per_session = max_calls_per_session
        self.cleanup_interval = timedelta(hours=cleanup_hours)
        self.histories: Dict[str, CallHistory] = {}
        self.last_cleanup = datetime.now()

    def get_session_id(self) -> str:
        """Get session ID from FastMCP context with fallbacks."""
        try:
            context = get_context()
            return context.session_id or context.client_id or "default_session"
        except RuntimeError:
            return "fallback_session"

    def get_history(self, session_id: str) -> CallHistory:
        """Get or create call history for session."""
        if session_id not in self.histories:
            self.histories[session_id] = CallHistory(
                max_calls=self.max_calls_per_session
            )
            logger.debug(
                f"SESSION_CREATE | session_id={session_id} | Creating new call history"
            )
        return self.histories[session_id]

    def cleanup_stale_sessions(self) -> None:
        """Remove sessions inactive beyond cleanup interval."""
        if datetime.now() - self.last_cleanup < self.cleanup_interval:
            return

        cutoff = datetime.now() - self.cleanup_interval
        stale = [
            sid
            for sid, hist in self.histories.items()
            if not hist.calls or hist.calls[-1].timestamp < cutoff
        ]

        for session_id in stale:
            del self.histories[session_id]

        self.last_cleanup = datetime.now()

    def stats(self) -> dict:
        """Get session statistics."""
        return {
            "active_sessions": len(self.histories),
            "total_calls": sum(len(h.calls) for h in self.histories.values()),
            "max_calls_per_session": self.max_calls_per_session,
        }


class GuardRailMiddleware(Middleware):
    """
    Unified middleware that handles security policies, performance monitoring,
    and call history tracking in a single clean implementation.

    Now with session-based call history management for multi-user support.
    """

    def __init__(
        self,
        policy: Policy | None = None,
        disabled_tools: list[str] | None = None,
        **kwargs,
    ):
        self.policy = policy
        self.disabled_tools = set(disabled_tools or [])
        self.sessions = SessionManager(**kwargs)

    async def on_call_tool(
        self, context: MiddlewareContext[mt.CallToolRequestParams], call_next
    ) -> mt.CallToolResult:
        """Handle tool call with security and tracking."""
        session_id = self.sessions.get_session_id()
        history = self.sessions.get_history(session_id)
        self.sessions.cleanup_stale_sessions()

        tool_call = ToolCall(
            name=context.message.name, arguments=context.message.arguments or {}
        )
        history.add_call(tool_call)

        # Step 1: Pre-execution guardrail evaluation (only if policy exists)
        if self.policy:
            result = evaluate_call(self.policy, history)

            if result.is_blocked:
                tool_call.status = CallStatus.BLOCK
                raise ToolError(f"Tool blocked by policy: {result.message}")

        # Step 2: Execute the tool
        start_time = time.time()
        try:
            call_result = await call_next(context)
        except Exception:
            tool_call.status = CallStatus.BLOCK
            raise
        finally:
            tool_call.execution_duration = round((time.time() - start_time) * 1000, 3)

        # Step 3: If all checks passed, mark as allowed and return result
        tool_call.status = CallStatus.ALLOW
        return call_result  # type: ignore[no-any-return]

    async def on_list_tools(
        self, context: MiddlewareContext[mt.ListToolsRequest], call_next
    ):
        """Filter disabled tools."""
        result = await call_next(context)
        return (
            [tool for tool in result if tool.name not in self.disabled_tools]
            if self.disabled_tools
            else result
        )

    def get_session_stats(self) -> dict:
        """Get session statistics."""
        return self.sessions.stats()
