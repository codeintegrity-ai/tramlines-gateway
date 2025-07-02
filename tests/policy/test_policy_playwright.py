"""
Tests for the Playwright Browser Automation Policy.

USAGE: pytest tests/policy/test_policy_playwright.py -v
"""

from tramlines.guardrail.dsl.testing import (
    assert_allowed,
    assert_blocked,
    simulate_calls,
)

# Import the policy to be tested
from tramlines.guardrail.policies.playwright_policies import (
    policy as playwright_policy,
)
from tramlines.session import ToolCall


def test_four_consecutive_calls_are_allowed():
    calls = [
        ToolCall("browser_click", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_click", {}),
    ]
    result = simulate_calls(playwright_policy, calls)
    assert_allowed(result)


def test_five_consecutive_calls_are_blocked():
    calls = [
        ToolCall("browser_click", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_click", {}),
    ]
    result = simulate_calls(playwright_policy, calls)
    assert_blocked(result, by_rule="Block tools called 5 times contiguously")


def test_non_consecutive_calls_are_allowed():
    calls = [
        ToolCall("browser_click", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_click", {}),
    ]
    result = simulate_calls(playwright_policy, calls)
    assert_allowed(result)


def test_different_tools_mixed_are_allowed():
    calls = [
        ToolCall("browser_navigate", {}),
        ToolCall("browser_take_screenshot", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
    ]
    result = simulate_calls(playwright_policy, calls)
    assert_allowed(result)


def test_three_pattern_repeated_twice_is_allowed():
    # Pattern: [navigate, click, type] repeated 2 times (6 calls total) - should be allowed
    calls = [
        # First repetition
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
        # Second repetition
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
    ]
    result = simulate_calls(playwright_policy, calls)
    assert_allowed(result)


def test_three_pattern_repeated_three_times_is_blocked():
    # Pattern: [navigate, click, type] repeated 3 times (9 calls total) - should be blocked
    calls = [
        # First repetition
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
        # Second repetition
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
        # Third repetition
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
    ]
    result = simulate_calls(playwright_policy, calls)
    assert_blocked(result, by_rule="Block repeating tool sequences")


def test_four_pattern_repeated_three_times_is_blocked():
    # Pattern: [navigate, click, type, screenshot] repeated 3 times (12 calls total)
    calls = [
        # First repetition
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
        ToolCall("browser_take_screenshot", {}),
        # Second repetition
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
        ToolCall("browser_take_screenshot", {}),
        # Third repetition
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
        ToolCall("browser_take_screenshot", {}),
    ]
    result = simulate_calls(playwright_policy, calls)
    assert_blocked(result, by_rule="Block repeating tool sequences")


def test_five_pattern_repeated_three_times_is_blocked():
    # Pattern: [navigate, click, type, screenshot, hover] repeated 3 times (15 calls total)
    calls = [
        # First repetition
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
        ToolCall("browser_take_screenshot", {}),
        ToolCall("browser_hover", {}),
        # Second repetition
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
        ToolCall("browser_take_screenshot", {}),
        ToolCall("browser_hover", {}),
        # Third repetition
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
        ToolCall("browser_take_screenshot", {}),
        ToolCall("browser_hover", {}),
    ]
    result = simulate_calls(playwright_policy, calls)
    assert_blocked(result, by_rule="Block repeating tool sequences")


def test_interrupted_pattern_is_allowed():
    # Pattern starts to repeat but gets interrupted - should be allowed
    calls = [
        # First partial pattern
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
        # Second partial pattern
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
        # Interruption with different tool
        ToolCall("browser_resize", {}),
        # Third pattern attempt
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
    ]
    result = simulate_calls(playwright_policy, calls)
    assert_allowed(result)


def test_six_pattern_repeated_twice_is_allowed():
    # Longest pattern (6 tools) repeated only twice - should be allowed
    calls = [
        # First repetition
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
        ToolCall("browser_take_screenshot", {}),
        ToolCall("browser_hover", {}),
        ToolCall("browser_press_key", {}),
        # Second repetition
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
        ToolCall("browser_take_screenshot", {}),
        ToolCall("browser_hover", {}),
        ToolCall("browser_press_key", {}),
    ]
    result = simulate_calls(playwright_policy, calls)
    assert_allowed(result)


def test_six_pattern_repeated_three_times_is_blocked():
    # Longest pattern (6 tools) repeated three times - should be blocked
    calls = [
        # First repetition
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
        ToolCall("browser_take_screenshot", {}),
        ToolCall("browser_hover", {}),
        ToolCall("browser_press_key", {}),
        # Second repetition
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
        ToolCall("browser_take_screenshot", {}),
        ToolCall("browser_hover", {}),
        ToolCall("browser_press_key", {}),
        # Third repetition
        ToolCall("browser_navigate", {}),
        ToolCall("browser_click", {}),
        ToolCall("browser_type", {}),
        ToolCall("browser_take_screenshot", {}),
        ToolCall("browser_hover", {}),
        ToolCall("browser_press_key", {}),
    ]
    result = simulate_calls(playwright_policy, calls)
    assert_blocked(result, by_rule="Block repeating tool sequences")
