"""
Tests for the Linear Single-Team-Per-Session Policy.

USAGE: pytest tests/policy/test_policy_linear.py -v
"""

from tramlines.guardrail.dsl.testing import (
    assert_allowed,
    assert_blocked,
    simulate_calls,
)

# Import the policy to be tested
from tramlines.guardrail.policies.linear_enforce_single_team import (
    policy as linear_single_team_policy,
)
from tramlines.session import ToolCall


def test_first_linear_call_is_allowed():
    calls = [ToolCall("create_issue", {"team_id": "team-A", "title": "New Bug"})]
    result = simulate_calls(linear_single_team_policy, calls)
    assert_allowed(result)


def test_same_team_calls_are_allowed():
    calls = [
        ToolCall("create_issue", {"team_id": "team-A", "title": "Bug"}),
        ToolCall("list_issues", {"team_id": "team-A"}),
    ]
    result = simulate_calls(linear_single_team_policy, calls)
    assert_allowed(result)


def test_different_team_is_blocked():
    calls = [
        ToolCall("create_issue", {"team_id": "team-A", "title": "Bug"}),
        ToolCall("list_issues", {"team_id": "team-B"}),
    ]
    result = simulate_calls(linear_single_team_policy, calls)
    assert_blocked(result, by_rule="Block cross-team Linear operations")


def test_calls_without_team_id_are_allowed():
    calls = [
        ToolCall("create_issue", {"team_id": "team-A"}),
        ToolCall("get_viewer", {}),
    ]
    result = simulate_calls(linear_single_team_policy, calls)
    assert_allowed(result)


def test_session_with_no_team_id_is_allowed():
    calls = [ToolCall("get_viewer", {}), ToolCall("get_user", {"user_id": "user-123"})]
    result = simulate_calls(linear_single_team_policy, calls)
    assert_allowed(result)


def test_different_team_after_no_team_id_is_blocked():
    calls = [
        ToolCall("get_team_issues", {"team_id": "team-A"}),
        ToolCall("get_user", {}),
        ToolCall("get_team_projects", {"team_id": "team-B"}),
    ]
    result = simulate_calls(linear_single_team_policy, calls)
    assert_blocked(result, by_rule="Block cross-team Linear operations")
