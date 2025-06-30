"""
Known Pattern Detection Guardrail

This policy scans all string arguments in every tool call for known malicious
or sensitive patterns using a regex scanner and blocks the call if any are found.
"""

from typing import Any

from tramlines.guardrail.dsl.predicates import custom
from tramlines.guardrail.dsl.rules import rule
from tramlines.guardrail.dsl.types import Policy
from tramlines.guardrail.extensions.regex_detector import detect_regex
from tramlines.session import CallHistory, ToolCall


def _contains_known_patterns_in_args(
    current_call: ToolCall, session_history: CallHistory
) -> bool:
    """
    Recursively scans arguments of a tool call for malicious/sensitive patterns
    in string values using regex.
    """

    def scan_value(value: Any) -> bool:
        if isinstance(value, str):
            if detect_regex(value):
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
    name="Block Known Malicious/Sensitive Patterns",
    description="Scans all string-based tool inputs to detect and block known patterns like prompt injections, credit card numbers, etc., using regex.",
    rules=[
        rule(
            "Block tool calls containing known malicious/sensitive patterns in arguments"
        )
        .when(custom(_contains_known_patterns_in_args))
        .block(
            "Tool call blocked: A known malicious or sensitive pattern was detected in the tool arguments."
        ),
    ],
)
