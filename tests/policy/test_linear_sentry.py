"""
Tests for the Linear & Sentry Context Separation Policy.

USAGE: pytest tests/policy/test_linear_sentry.py -v
"""

from tramlines.guardrail.dsl.testing import (
    assert_allowed,
    assert_blocked,
    simulate_calls,
)

# Import the policy to be tested
from tramlines.guardrail.policies.linear_sentry_rules import (
    policy as linear_sentry_policy,
)
from tramlines.session import ToolCall


def test_first_linear_call_is_allowed():
    calls = [ToolCall("get_issue", {"issue_id": "PROJ-123"})]
    result = simulate_calls(linear_sentry_policy, calls)
    assert_allowed(result)


def test_first_sentry_call_is_allowed():
    calls = [
        ToolCall(
            "get_issue_details", {"organization_slug": "my-org", "issue_id": "BUG-456"}
        )
    ]
    result = simulate_calls(linear_sentry_policy, calls)
    assert_allowed(result)


def test_sequential_linear_calls_are_allowed():
    calls = [
        ToolCall("get_issue", {"issue_id": "PROJ-123"}),
        ToolCall("list_comments", {"issue_id": "PROJ-123"}),
    ]
    result = simulate_calls(linear_sentry_policy, calls)
    assert_allowed(result)


def test_sequential_sentry_calls_are_allowed():
    calls = [
        ToolCall(
            "get_issue_details", {"organization_slug": "my-org", "issue_id": "BUG-456"}
        ),
        ToolCall(
            "get_issue_details", {"organization_slug": "my-org", "issue_id": "BUG-789"}
        ),
    ]
    result = simulate_calls(linear_sentry_policy, calls)
    assert_allowed(result)


def test_linear_after_sentry_is_blocked():
    calls = [
        ToolCall(
            "get_issue_details", {"organization_slug": "my-org", "issue_id": "BUG-456"}
        ),
        ToolCall("get_issue", {"issue_id": "PROJ-123"}),
    ]
    result = simulate_calls(linear_sentry_policy, calls)
    assert_blocked(result, by_rule="Block Linear calls after Sentry calls")


def test_sentry_after_linear_is_blocked():
    calls = [
        ToolCall("list_issues", {"query": "bug reports"}),
        ToolCall(
            "get_issue_details", {"organization_slug": "my-org", "issue_id": "BUG-456"}
        ),
    ]
    result = simulate_calls(linear_sentry_policy, calls)
    assert_blocked(result, by_rule="Block Sentry calls after Linear calls")


def test_non_linear_sentry_tools_are_ignored():
    calls = [
        ToolCall("some_other_tool", {"param": "value"}),
        ToolCall("get_issue", {"issue_id": "PROJ-123"}),
    ]
    result = simulate_calls(linear_sentry_policy, calls)
    assert_allowed(result)


def test_other_tools_between_linear_sentry_allows_context_reset():
    calls = [
        ToolCall(
            "get_issue_details", {"organization_slug": "my-org", "issue_id": "BUG-456"}
        ),
        ToolCall("some_other_tool", {"param": "value"}),
        ToolCall("list_documents", {"query": "requirements"}),
    ]
    result = simulate_calls(linear_sentry_policy, calls)
    assert_allowed(result)


def test_multiple_context_switches_are_blocked():
    calls = [
        ToolCall("get_issue", {"issue_id": "PROJ-123"}),
        ToolCall(
            "get_issue_details", {"organization_slug": "my-org", "issue_id": "BUG-456"}
        ),
    ]
    result = simulate_calls(linear_sentry_policy, calls)
    assert_blocked(result, by_rule="Block Sentry calls after Linear calls")
