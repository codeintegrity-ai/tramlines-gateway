"""
Tests for the Neon Database Policy.

USAGE: pytest tests/policy/test_policy_neon.py -v
"""

from tramlines.guardrail.dsl.testing import (
    assert_allowed,
    assert_blocked,
    simulate_calls,
)

# Import the policy to be tested
from tramlines.guardrail.policies.neon_policies import (
    policy as neon_policy,
)
from tramlines.session import ToolCall


def test_single_run_sql_call_is_allowed():
    calls = [
        ToolCall("mcp_tramlines-proxy_run_sql", {}),
    ]
    result = simulate_calls(neon_policy, calls)
    assert_allowed(result)


def test_second_run_sql_call_is_blocked():
    calls = [
        ToolCall("mcp_tramlines-proxy_run_sql", {}),
        ToolCall("mcp_tramlines-proxy_run_sql", {}),
    ]
    result = simulate_calls(neon_policy, calls)
    assert_blocked(result, by_rule="Block run_sql tool after second call")


def test_other_tools_with_single_run_sql_are_allowed():
    calls = [
        ToolCall("mcp_tramlines-proxy_list_projects", {}),
        ToolCall("mcp_tramlines-proxy_run_sql", {}),
        ToolCall("mcp_tramlines-proxy_create_project", {}),
        ToolCall("mcp_tramlines-proxy_describe_project", {}),
    ]
    result = simulate_calls(neon_policy, calls)
    assert_allowed(result)


def test_other_tools_with_two_run_sql_calls_blocks_second():
    calls = [
        ToolCall("mcp_tramlines-proxy_list_projects", {}),
        ToolCall("mcp_tramlines-proxy_run_sql", {}),
        ToolCall("mcp_tramlines-proxy_create_project", {}),
        ToolCall("mcp_tramlines-proxy_run_sql", {}),
    ]
    result = simulate_calls(neon_policy, calls)
    assert_blocked(result, by_rule="Block run_sql tool after second call")


def test_non_neon_tools_are_not_affected():
    calls = [
        ToolCall("some_other_tool", {}),
        ToolCall("another_tool", {}),
        ToolCall("third_tool", {}),
    ]
    result = simulate_calls(neon_policy, calls)
    assert_allowed(result)


def test_run_sql_sandwiched_between_other_tools_blocks_second():
    calls = [
        ToolCall("mcp_tramlines-proxy_list_projects", {}),
        ToolCall("mcp_tramlines-proxy_run_sql", {}),
        ToolCall("mcp_tramlines-proxy_create_branch", {}),
        ToolCall("mcp_tramlines-proxy_describe_project", {}),
        ToolCall("mcp_tramlines-proxy_run_sql", {}),
        ToolCall("mcp_tramlines-proxy_delete_project", {}),
    ]
    result = simulate_calls(neon_policy, calls)
    assert_blocked(result, by_rule="Block run_sql tool after second call")
