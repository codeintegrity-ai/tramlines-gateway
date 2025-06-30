"""
Tests for the Generic PII Detection Guardrail.
"""

from tramlines.guardrail.dsl.testing import (
    assert_allowed,
    assert_blocked,
    simulate_calls,
)

# Import the policy to be tested
from tramlines.guardrail.policies.block_pii_in_tool_args import policy as pii_policy
from tramlines.session import ToolCall


def test_safe_string_is_allowed():
    calls = [ToolCall("send_email", {"body": "This is a safe message."})]
    result = simulate_calls(pii_policy, calls)
    assert_allowed(result)


def test_email_in_string_is_blocked():
    calls = [ToolCall("create_user", {"email": "test@example.com"})]
    result = simulate_calls(pii_policy, calls)
    assert_blocked(result, by_rule="Block tool calls containing PII in arguments")


def test_pii_in_nested_dict_is_blocked():
    args = {"data": {"user": {"contact": "Call 555-123-4567"}}}
    calls = [ToolCall("update_record", args)]
    result = simulate_calls(pii_policy, calls)
    assert_blocked(result, by_rule="Block tool calls containing PII in arguments")


def test_pii_in_list_is_blocked():
    args = {"recipients": ["user1@example.com", "user2@gmail.com"]}
    calls = [ToolCall("send_bulk_email", args)]
    result = simulate_calls(pii_policy, calls)
    assert_blocked(result, by_rule="Block tool calls containing PII in arguments")


def test_no_string_args_is_allowed():
    calls = [ToolCall("do_math", {"a": 5, "b": 10})]
    result = simulate_calls(pii_policy, calls)
    assert_allowed(result)
