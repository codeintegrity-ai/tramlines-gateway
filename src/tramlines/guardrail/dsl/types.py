from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Protocol

# --- Import shared types from session module ---
from tramlines.session import CallHistory, ToolCall

# --- DSL-specific Types ---


class ActionType(Enum):
    """The type of action a rule can take."""

    ALLOW = "ALLOW"
    BLOCK = "BLOCK"


# --- Rule and Policy Structure ---


class Predicate(Protocol):
    """
    A protocol defining the structure of a predicate.
    It's a callable that evaluates a condition against a tool call and its history.
    """

    def __call__(self, call: ToolCall, history: CallHistory) -> bool: ...

    def __and__(self, other: Predicate) -> Predicate: ...

    def __or__(self, other: Predicate) -> Predicate: ...

    def __invert__(self) -> Predicate: ...


@dataclass(frozen=True)
class Rule:
    """
    A single, immutable security rule.
    It consists of a name, a condition (predicate), and the action to take.
    """

    name: str
    condition: Predicate
    action_type: ActionType
    message: str | None = None


@dataclass
class Policy:
    """A collection of rules that are evaluated in order."""

    name: str
    rules: List[Rule] = field(default_factory=list)
    description: str | None = None
