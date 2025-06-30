from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Callable, Generic, List, Pattern, TypeVar

from tramlines.guardrail.dsl.types import CallHistory, Predicate, ToolCall

T = TypeVar("T")


# --- Helper Functions ---


def _parse_time_window(window: str) -> timedelta:
    """Parse a time window string (e.g., '1h', '30m', '10s') into a timedelta."""
    match = re.match(r"^(\d+)([smhd])$", window.lower())
    if not match:
        raise ValueError(f"Invalid time window format: {window}")

    value, unit = match.groups()
    value = int(value)

    if unit == "s":
        return timedelta(seconds=value)
    elif unit == "m":
        return timedelta(minutes=value)
    elif unit == "h":
        return timedelta(hours=value)
    elif unit == "d":
        return timedelta(days=value)
    else:
        # This path is technically unreachable due to the regex, but good for safety
        raise ValueError(f"Invalid time unit: {unit}")


# --- Base Predicate Implementation ---


class BasePredicate(Predicate, ABC):
    """Base implementation for all predicates with logical operators."""

    def __and__(self, other: Predicate) -> Predicate:
        return AndPredicate(self, other)

    def __or__(self, other: Predicate) -> Predicate:
        return OrPredicate(self, other)

    def __invert__(self) -> Predicate:
        return NotPredicate(self)

    @abstractmethod
    def __call__(self, call: ToolCall, history: CallHistory) -> bool:
        pass


# --- Composite Predicates ---


class AndPredicate(BasePredicate):
    def __init__(self, left: Predicate, right: Predicate):
        self._left = left
        self._right = right

    def __call__(self, call: ToolCall, history: CallHistory) -> bool:
        return self._left(call, history) and self._right(call, history)


class OrPredicate(BasePredicate):
    def __init__(self, left: Predicate, right: Predicate):
        self._left = left
        self._right = right

    def __call__(self, call: ToolCall, history: CallHistory) -> bool:
        return self._left(call, history) or self._right(call, history)


class NotPredicate(BasePredicate):
    def __init__(self, predicate: Predicate):
        self._predicate = predicate

    def __call__(self, call: ToolCall, history: CallHistory) -> bool:
        return not self._predicate(call, history)


# --- Value Builders ---


class ValueBuilder(Generic[T]):
    """Creates predicates when comparison operators are used."""

    def __init__(self, extractor: Callable[[ToolCall, CallHistory], T]):
        self._extractor = extractor

    def __eq__(self, other: Any) -> Predicate:  # type: ignore[override]
        return ComparisonPredicate(self._extractor, lambda a, b: a == b, other)

    def __ne__(self, other: Any) -> Predicate:  # type: ignore[override]
        return ComparisonPredicate(self._extractor, lambda a, b: a != b, other)

    def __gt__(self, other: Any) -> Predicate:
        return ComparisonPredicate(self._extractor, lambda a, b: a > b, other)

    def __lt__(self, other: Any) -> Predicate:
        return ComparisonPredicate(self._extractor, lambda a, b: a < b, other)

    def __ge__(self, other: Any) -> Predicate:
        return ComparisonPredicate(self._extractor, lambda a, b: a >= b, other)

    def __le__(self, other: Any) -> Predicate:
        return ComparisonPredicate(self._extractor, lambda a, b: a <= b, other)


class StringValueBuilder(ValueBuilder[str]):
    """Value builder with string-specific methods."""

    def matches(self, pattern: str | Pattern[str]) -> Predicate:
        regex = re.compile(pattern) if isinstance(pattern, str) else pattern
        return ComparisonPredicate(
            self._extractor,
            lambda val, p: bool(p.search(val) if isinstance(val, str) else False),
            regex,
        )

    def is_in(self, values: List[str]) -> Predicate:
        return ComparisonPredicate(
            self._extractor,
            lambda val, v_list: val in v_list if isinstance(val, str) else False,
            values,
        )

    def contains(self, *terms: str) -> Predicate:
        return ComparisonPredicate(
            self._extractor,
            lambda val, terms: (
                any(term in val for term in terms) if isinstance(val, str) else False
            ),
            terms,
        )

    def startswith(self, *prefixes: str) -> Predicate:
        return ComparisonPredicate(
            self._extractor,
            lambda val, prefixes: (
                val.startswith(prefixes) if isinstance(val, str) else False
            ),
            prefixes,
        )

    def endswith(self, *suffixes: str) -> Predicate:
        return ComparisonPredicate(
            self._extractor,
            lambda val, suffixes: (
                val.endswith(suffixes) if isinstance(val, str) else False
            ),
            suffixes,
        )


# --- Core Predicates ---


class ComparisonPredicate(BasePredicate, Generic[T]):
    """Predicate for comparing extracted values."""

    def __init__(
        self,
        extractor: Callable[[ToolCall, CallHistory], T],
        comparison: Callable[[T, Any], bool],
        target: Any,
    ):
        self._extractor = extractor
        self._comparison = comparison
        self._target = target

    def __call__(self, call: ToolCall, history: CallHistory) -> bool:
        value = self._extractor(call, history)
        if value is None:
            return False
        try:
            return self._comparison(value, self._target)
        except (TypeError, ValueError):
            return False


# --- History Query System ---


class HistoryQueryBuilder:
    """Simplified history query builder."""

    def __init__(self, pattern: str | Pattern[str]):
        self._pattern = re.compile(pattern) if isinstance(pattern, str) else pattern
        self._condition: Predicate | None = None

    def where(self, condition: Predicate) -> HistoryQueryBuilder:
        """Filter historical calls with a condition."""
        self._condition = condition
        return self

    def exists(self) -> Predicate:
        """Check if any matching calls exist."""
        return HistoryExistsPredicate(self._pattern, self._condition)

    def count(self, within: str | None = None) -> ValueBuilder[int]:
        """Count matching calls, optionally within a time window."""
        time_delta = _parse_time_window(within) if within else None

        def counter(call: ToolCall, history: CallHistory) -> int:
            cutoff = datetime.now() - time_delta if time_delta else None
            count = 0
            for past_call in history.calls:
                # Check time window if applicable
                if cutoff and (not past_call.timestamp or past_call.timestamp < cutoff):
                    continue

                # Check name pattern
                if self._pattern.search(past_call.name):
                    # Check extra condition if applicable
                    if self._condition is None or self._condition(past_call, history):
                        count += 1
            return count

        return ValueBuilder(counter)

    def last(self) -> HistoricalCallBuilder:
        """Get the most recent matching call."""
        return HistoricalCallBuilder(self._pattern, self._condition, reverse=True)

    def first(self) -> HistoricalCallBuilder:
        """Get the oldest matching call."""
        return HistoricalCallBuilder(self._pattern, self._condition, reverse=False)


class HistoryExistsPredicate(BasePredicate):
    """Check if historical calls matching a pattern exist."""

    def __init__(self, pattern: Pattern[str], condition: Predicate | None):
        self._pattern = pattern
        self._condition = condition

    def __call__(self, call: ToolCall, history: CallHistory) -> bool:
        for past_call in history.calls:
            if self._pattern.search(past_call.name):
                if self._condition is None or self._condition(past_call, history):
                    return True
        return False


class HistoricalCallBuilder:
    """A builder that provides access to a specific historical call's properties."""

    def __init__(
        self, pattern: Pattern[str], condition: Predicate | None, reverse: bool
    ):
        self._pattern = pattern
        self._condition = condition
        self._reverse = reverse

    def _find_matching_call(
        self, call: ToolCall, history: CallHistory
    ) -> ToolCall | None:
        iterator = reversed(history.calls) if self._reverse else history.calls
        for past_call in iterator:
            if self._pattern.search(past_call.name):
                if self._condition is None or self._condition(past_call, history):
                    return past_call
        return None

    @property
    def name(self) -> StringValueBuilder:
        """Get the name of the historical call."""

        def extractor(call: ToolCall, hist: CallHistory) -> str | None:
            match = self._find_matching_call(call, hist)
            return match.name if match else None

        return StringValueBuilder(extractor)

    def arg(self, key: str) -> StringValueBuilder:
        """Get an argument from the historical call."""

        def extractor(call: ToolCall, hist: CallHistory) -> str | None:
            match = self._find_matching_call(call, hist)
            if match:
                return match.arguments.get(key)
            return None

        return StringValueBuilder(extractor)


class CustomPredicate(BasePredicate):
    """A wrapper for a raw Python function to be used as a predicate."""

    def __init__(self, func: Callable[[ToolCall, CallHistory], bool]):
        self._func = func

    def __call__(self, call: ToolCall, history: CallHistory) -> bool:
        return self._func(call, history)


# --- Convenience Function ---


def custom(func: Callable[[ToolCall, CallHistory], bool]) -> Predicate:
    """
    Provides a clean escape hatch to use a raw Python function for complex logic
    that cannot be expressed by the declarative DSL.

    The function must have the signature:
    `my_function(call: ToolCall, history: CallHistory) -> bool`

    Args:
        func: The Python function to wrap in a predicate.

    Returns:
        A Predicate instance that can be used in a .when() clause.
    """
    return CustomPredicate(func)
