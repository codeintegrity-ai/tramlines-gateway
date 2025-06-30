"""
Tests for the GitHub Single-Repository-Per-Session Policy.

USAGE: pytest tests/policy/test_policy_github.py -v
"""

from tramlines.guardrail.dsl.testing import (
    assert_allowed,
    assert_blocked,
    simulate_calls,
)

# Import the policy to be tested
from tramlines.guardrail.policies.github_enforce_single_repo import (
    policy as github_single_repo_policy,
)
from tramlines.session import ToolCall


def test_first_github_call_is_allowed():
    calls = [ToolCall("create_issue", {"owner": "octocat", "repo": "hello-world"})]
    result = simulate_calls(github_single_repo_policy, calls)
    assert_allowed(result)


def test_same_repo_calls_are_allowed():
    calls = [
        ToolCall("create_issue", {"owner": "octocat", "repo": "hello-world"}),
        ToolCall("add_issue_comment", {"owner": "octocat", "repo": "hello-world"}),
    ]
    result = simulate_calls(github_single_repo_policy, calls)
    assert_allowed(result)


def test_non_github_tools_are_allowed():
    calls = [
        ToolCall("create_issue", {"owner": "octocat", "repo": "hello-world"}),
        ToolCall("send_email", {"to": "user@example.com"}),
    ]
    result = simulate_calls(github_single_repo_policy, calls)
    assert_allowed(result)


def test_github_tools_without_repo_are_allowed():
    calls = [
        ToolCall("create_issue", {"owner": "octocat", "repo": "hello-world"}),
        ToolCall("create_issue", {"title": "Bug report"}),
    ]
    result = simulate_calls(github_single_repo_policy, calls)
    assert_allowed(result)


def test_different_repo_is_blocked():
    calls = [
        ToolCall("create_issue", {"owner": "octocat", "repo": "hello-world"}),
        ToolCall("create_issue", {"owner": "microsoft", "repo": "vscode"}),
    ]
    result = simulate_calls(github_single_repo_policy, calls)
    assert_blocked(result, by_rule="Block cross-repository GitHub operations")


def test_different_owner_is_blocked():
    calls = [
        ToolCall("create_issue", {"owner": "octocat", "repo": "hello-world"}),
        ToolCall("get_issue", {"owner": "github", "repo": "hello-world"}),
    ]
    result = simulate_calls(github_single_repo_policy, calls)
    assert_blocked(result, by_rule="Block cross-repository GitHub operations")


def test_different_repo_same_owner_is_blocked():
    calls = [
        ToolCall("create_issue", {"owner": "octocat", "repo": "hello-world"}),
        ToolCall("list_issues", {"owner": "octocat", "repo": "goodbye-world"}),
    ]
    result = simulate_calls(github_single_repo_policy, calls)
    assert_blocked(result, by_rule="Block cross-repository GitHub operations")
