from tramlines.guardrail.dsl.evaluator import EvaluationResult, evaluate_call
from tramlines.guardrail.dsl.types import Policy
from tramlines.session import CallHistory, ToolCall


def assert_allowed(result: EvaluationResult):
    """
    Asserts that a tool call was allowed.
    Raises an AssertionError with a descriptive message if blocked.
    """
    if result.is_blocked:
        raise AssertionError(
            f"Expected call to be ALLOWED, but it was BLOCKED by rule "
            f"'{result.violated_rule}': {result.message}"
        )


def assert_blocked(result: EvaluationResult, by_rule: str | None = None) -> None:
    """
    Asserts that a tool call was blocked.

    Args:
        result: The EvaluationResult from a test run.
        by_rule: If provided, also asserts that the block was triggered by the
                 rule with this specific name.

    Raises:
        AssertionError: If the call was allowed or blocked by a different rule.
    """
    if result.is_allowed:
        raise AssertionError("Expected call to be BLOCKED, but it was ALLOWED.")

    if by_rule and result.violated_rule != by_rule:
        raise AssertionError(
            f"Expected block by rule '{by_rule}', but was blocked by "
            f"'{result.violated_rule}' instead."
        )


def simulate_calls(
    policy_under_test: Policy, calls: list[ToolCall]
) -> EvaluationResult:
    """
    Simulates a sequence of tool calls against a policy and returns the final result.

    This function simulates what happens in a real session - each call is evaluated
    as it arrives, with full knowledge of previous calls. If any call is blocked,
    that result is returned immediately.

    Args:
        policy_under_test: The policy to test against.
        calls: List of tool calls to simulate in sequence.

    Returns:
        The final EvaluationResult - either the first blocked call or the last call's result.
    """
    history = CallHistory()

    for call in calls:
        history.add_call(call)
        result = evaluate_call(policy_under_test, history)

        # If this call gets blocked, return immediately
        if result.is_blocked:
            return result

    # If we made it through all calls, return the final result
    return result
