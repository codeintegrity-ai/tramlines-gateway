"""
Tests for the Heroku Single-App-Per-Session Policy.

USAGE: pytest tests/policy/test_policy_heroku.py -v
"""

from tramlines.guardrail.dsl.testing import (
    assert_allowed,
    assert_blocked,
    simulate_calls,
)

# Import the policy to be tested
from tramlines.guardrail.policies.heroku_enforce_single_app import (
    policy as heroku_single_app_policy,
)
from tramlines.session import ToolCall


def test_first_heroku_call_is_allowed():
    calls = [ToolCall("get_app_logs", {"app": "my-app-1"})]
    result = simulate_calls(heroku_single_app_policy, calls)
    assert_allowed(result)


def test_same_app_calls_are_allowed():
    calls = [
        ToolCall("get_app_logs", {"app": "my-app-1"}),
        ToolCall("rename_app", {"app": "my-app-1"}),
    ]
    result = simulate_calls(heroku_single_app_policy, calls)
    assert_allowed(result)


def test_different_app_is_blocked():
    calls = [
        ToolCall("get_app_logs", {"app": "my-app-1"}),
        ToolCall("rename_app", {"app": "my-app-2"}),
    ]
    result = simulate_calls(heroku_single_app_policy, calls)
    assert_blocked(result, by_rule="Block cross-app Heroku operations")


def test_calls_without_app_id_are_allowed():
    calls = [
        ToolCall("get_app_info", {"app": "my-app-1"}),
        ToolCall("list_apps", {}),
    ]
    result = simulate_calls(heroku_single_app_policy, calls)
    assert_allowed(result)


def test_different_app_after_no_app_id_is_blocked():
    calls = [
        ToolCall("get_app_logs", {"app": "my-app-1"}),
        ToolCall("list_apps", {}),
        ToolCall("get_app_logs", {"app": "my-app-2"}),
    ]
    result = simulate_calls(heroku_single_app_policy, calls)
    assert_blocked(result, by_rule="Block cross-app Heroku operations")
