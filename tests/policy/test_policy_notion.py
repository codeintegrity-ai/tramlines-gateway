"""
Tests for the Notion Single-Page-Per-Session Policy.

USAGE: pytest tests/policy/test_policy_notion.py -v
"""

from tramlines.guardrail.dsl.testing import (
    assert_allowed,
    assert_blocked,
    simulate_calls,
)

# Import the policy to be tested
from tramlines.guardrail.policies.notion_enforce_single_page import (
    policy as notion_single_page_policy,
)
from tramlines.session import ToolCall


def test_first_notion_call_is_allowed():
    calls = [ToolCall("get_page_content", {"page_id": "page-A"})]
    result = simulate_calls(notion_single_page_policy, calls)
    assert_allowed(result)


def test_same_page_calls_are_allowed():
    calls = [
        ToolCall("get_page_content", {"page_id": "page-A"}),
        ToolCall("create_comment", {"page_id": "page-A", "text": "Comment"}),
    ]
    result = simulate_calls(notion_single_page_policy, calls)
    assert_allowed(result)


def test_different_page_is_blocked():
    calls = [
        ToolCall("get_page_content", {"page_id": "page-A"}),
        ToolCall(
            "update_page_content", {"page_id": "page-B", "content": "New content"}
        ),
    ]
    result = simulate_calls(notion_single_page_policy, calls)
    assert_blocked(result, by_rule="Block cross-page Notion operations")


def test_calls_without_page_id_are_allowed():
    calls = [
        ToolCall("get_page_content", {"page_id": "page-A"}),
        ToolCall("search", {"query": "My notes"}),
    ]
    result = simulate_calls(notion_single_page_policy, calls)
    assert_allowed(result)


def test_different_page_after_no_page_id_is_blocked():
    calls = [
        ToolCall("get_page_content", {"page_id": "page-A"}),
        ToolCall("search", {"query": "My notes"}),
        ToolCall("archive_page", {"page_id": "page-B"}),
    ]
    result = simulate_calls(notion_single_page_policy, calls)
    assert_blocked(result, by_rule="Block cross-page Notion operations")
