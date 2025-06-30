"""
Generic PII Detection Guardrail

This policy scans all string arguments in every tool call for Personally
Identifiable Information (PII) and blocks the call if any is found.
"""

from typing import Any

from tramlines.guardrail.dsl.predicates import custom
from tramlines.guardrail.dsl.rules import rule
from tramlines.guardrail.dsl.types import Policy
from tramlines.guardrail.extensions.pii_detector import detect_pii
from tramlines.session import CallHistory, ToolCall


def _contains_pii_in_args(current_call: ToolCall, session_history: CallHistory) -> bool:
    """
    Recursively scans arguments of a tool call for PII in string values.
    """

    def scan_value(value: Any) -> bool:
        if isinstance(value, str):
            if detect_pii(value):
                return True
        elif isinstance(value, dict):
            for v in value.values():
                if scan_value(v):
                    return True
        elif isinstance(value, list):
            for item in value:
                if scan_value(item):
                    return True
        return False

    return scan_value(current_call.arguments)


# The main policy object to be imported
policy = Policy(
    name="Block PII in Tool Arguments",
    description="Scans all string-based tool inputs to detect and block Personally Identifiable Information (PII).",
    rules=[
        rule("Block tool calls containing PII in arguments")
        .when(custom(_contains_pii_in_args))
        .block(
            "Tool call blocked: Personally Identifiable Information (PII) was detected in the tool arguments."
        ),
    ],
)
