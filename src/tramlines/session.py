from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CallStatus(Enum):
    """The final status of a tool call after evaluation."""

    ALLOW = "ALLOW"
    BLOCK = "BLOCK"


@dataclass
class ToolCall:
    """Tool call data for policy evaluation and history tracking."""

    name: str
    arguments: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    status: CallStatus = CallStatus.ALLOW
    execution_duration: float | None = None


# --- Actions ---


class CallHistory:
    """Session call history with automatic size management."""

    def __init__(self, max_calls: int = 100) -> None:
        self.calls: list[ToolCall] = []
        self._max_calls = max_calls

    def add_call(self, call: ToolCall) -> None:
        """Add tool call to history with automatic cleanup."""
        self.calls.append(call)
        if len(self.calls) > self._max_calls:
            self.calls = self.calls[-self._max_calls :]

    def __getitem__(self, index: int) -> ToolCall:
        return self.calls[index]

    def __len__(self) -> int:
        return len(self.calls)

    @property
    def call_count(self) -> int:
        return len(self.calls)
