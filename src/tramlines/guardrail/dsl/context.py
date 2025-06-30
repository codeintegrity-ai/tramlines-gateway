from __future__ import annotations

from typing import Pattern

from .predicates import HistoryQueryBuilder, StringValueBuilder

# --- Call (Live) Context ---


class _CallContext:
    """
    The top-level context object for building predicates about the live tool call.
    """

    @property
    def name(self) -> StringValueBuilder:
        """Accesses the tool's name."""
        return StringValueBuilder(lambda call, hist: call.name)

    def arg(self, key: str) -> StringValueBuilder:
        """Accesses a specific argument by its key."""

        def extractor(call, hist):
            value = call.arguments.get(key)
            return str(value) if value is not None else ""

        return StringValueBuilder(extractor)


call = _CallContext()


# --- Historical Call Context (for use in history queries) ---


class _HistoricalCallContext:
    """
    Context object for accessing historical call properties within where clauses.
    Uses the same pattern as the live call context for consistency.
    """

    @property
    def name(self) -> StringValueBuilder:
        """Accesses the historical call's name."""
        return StringValueBuilder(lambda call, hist: call.name)

    def arg(self, key: str) -> StringValueBuilder:
        """Accesses a specific argument from the historical call."""

        def extractor(call, hist):
            value = call.arguments.get(key)
            return str(value) if value is not None else ""

        return StringValueBuilder(extractor)


# --- History Context ---


class _HistoryContext:
    """
    The top-level context object for building predicates about the session history.
    """

    @property
    def call(self) -> _HistoricalCallContext:
        """Access historical call properties with consistent syntax."""
        return _HistoricalCallContext()

    def select(self, name_pattern: str | Pattern[str]) -> HistoryQueryBuilder:
        """
        Selects a subset of calls from history matching a tool name pattern.

        Args:
            name_pattern: A regex pattern to match against tool names.

        Returns:
            A query builder to further refine the selection.
        """
        return HistoryQueryBuilder(name_pattern)


history = _HistoryContext()
