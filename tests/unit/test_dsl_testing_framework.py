from tramlines.guardrail.dsl.context import history
from tramlines.guardrail.dsl.rules import rule
from tramlines.guardrail.dsl.testing import (
    assert_allowed,
    assert_blocked,
    simulate_calls,
)
from tramlines.guardrail.dsl.types import Policy
from tramlines.session import ToolCall


def test_simulation_asserts_allow_and_block_correctly():
    test_policy = Policy(
        name="Test Policy",
        rules=[
            rule("Block Admins")
            .when(history.call.arg("user") == "admin")
            .block("Admin access blocked"),
        ],
    )

    allow_call = ToolCall(name="test", arguments={"user": "guest"})
    result = simulate_calls(test_policy, [allow_call])
    assert_allowed(result)

    block_call = ToolCall(name="test", arguments={"user": "admin"})
    result = simulate_calls(test_policy, [block_call])
    assert_blocked(result, by_rule="Block Admins")


def test_simulation_handles_stateful_rules_like_rate_limits():
    rate_limit_policy = Policy(
        name="Rate Limit Policy",
        rules=[
            rule("Rate Limit on 'api_call'")
            .when(history.select("api_call").count(within="1m") > 2)
            .block("Rate limit exceeded"),
        ],
    )

    api_call = ToolCall(name="api_call", arguments={})

    result = simulate_calls(rate_limit_policy, [api_call, api_call, api_call])
    assert_blocked(result, by_rule="Rate Limit on 'api_call'")


def test_assert_blocked_works_without_specifying_rule_name():
    test_policy = Policy(
        name="Generic Block Policy",
        rules=[
            rule("Generic Block")
            .when(history.call.name == "blocked_tool")
            .block("Tool blocked"),
        ],
    )

    blocked_call = ToolCall(name="blocked_tool", arguments={})
    result = simulate_calls(test_policy, [blocked_call])
    assert_blocked(result)
