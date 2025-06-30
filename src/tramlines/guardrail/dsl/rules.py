from __future__ import annotations

from .types import ActionType, Predicate, Rule


class RuleBuilder:
    """
    A builder for creating a Rule object in a fluent, step-by-step manner.
    """

    def __init__(self, name: str):
        self._name = name
        self._condition: Predicate | None = None

    def when(self, condition: Predicate) -> RuleBuilder:
        """
        Sets the condition (a Predicate) for this rule to trigger.

        Args:
            condition: The predicate that defines the logic of the rule.

        Returns:
            The RuleBuilder instance for chaining.
        """
        self._condition = condition
        return self

    def _ensure_condition(self) -> Predicate:
        if self._condition is None:
            raise ValueError(
                "A rule must have a `.when()` condition before an action is set."
            )
        return self._condition

    def block(self, message: str) -> Rule:
        """
        Finalizes the rule with a BLOCK action.
        If the condition is met, the tool call will be blocked.
        """
        return Rule(
            name=self._name,
            condition=self._ensure_condition(),
            action_type=ActionType.BLOCK,
            message=message,
        )

    def allow(self) -> Rule:
        """
        Finalizes the rule with an ALLOW action.
        If the condition is met, evaluation of other rules in the same phase stops.
        """
        return Rule(
            name=self._name,
            condition=self._ensure_condition(),
            action_type=ActionType.ALLOW,
        )


def rule(name: str) -> RuleBuilder:
    """
    The entry point for creating a new security rule.

    Args:
        name: A descriptive name for the rule, used for logging.

    Returns:
        A RuleBuilder instance to define the rule's condition and action.
    """
    return RuleBuilder(name)
