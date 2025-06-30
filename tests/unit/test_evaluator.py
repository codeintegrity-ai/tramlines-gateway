from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from tramlines.guardrail.dsl.evaluator import EvaluationResult, evaluate_call
from tramlines.guardrail.dsl.types import ActionType, Policy, Rule
from tramlines.session import CallHistory, ToolCall


@pytest.fixture
def mock_tool_call():
    return ToolCall(
        name="test_tool",
        arguments={"user": "admin", "action": "delete"},
        timestamp=datetime.now(),
    )


@pytest.fixture
def mock_history(mock_tool_call):
    history = CallHistory(max_calls=10)
    history.add_call(mock_tool_call)
    return history


@pytest.fixture
def mock_predicate_true():
    predicate = Mock()
    predicate.return_value = True
    return predicate


@pytest.fixture
def mock_predicate_false():
    predicate = Mock()
    predicate.return_value = False
    return predicate


@pytest.fixture
def allow_rule(mock_predicate_true):
    return Rule(
        name="allow_rule",
        condition=mock_predicate_true,
        action_type=ActionType.ALLOW,
        message="Allow message",
    )


@pytest.fixture
def block_rule(mock_predicate_true):
    return Rule(
        name="block_rule",
        condition=mock_predicate_true,
        action_type=ActionType.BLOCK,
        message="Block message",
    )


@pytest.fixture
def policy_with_allow_rule(allow_rule):
    return Policy(name="test_policy", rules=[allow_rule])


@pytest.fixture
def policy_with_block_rule(block_rule):
    return Policy(name="test_policy", rules=[block_rule])


class TestEvaluationResult:
    def test_evaluation_result_initializes_correctly_for_allow_action(self):
        result = EvaluationResult(action_type=ActionType.ALLOW)
        assert result.action_type == ActionType.ALLOW
        assert result.violated_rule is None
        assert result.message is None

    def test_evaluation_result_initializes_correctly_for_block_action(self):
        result = EvaluationResult(
            action_type=ActionType.BLOCK,
            violated_rule="test_rule",
            message="Test message",
        )
        assert result.action_type == ActionType.BLOCK
        assert result.violated_rule == "test_rule"
        assert result.message == "Test message"

    def test_is_allowed_property_is_true_for_allow_action(self):
        result = EvaluationResult(action_type=ActionType.ALLOW)
        assert result.is_allowed is True

    def test_is_allowed_property_is_false_for_block_action(self):
        result = EvaluationResult(action_type=ActionType.BLOCK)
        assert result.is_allowed is False

    def test_is_blocked_property_is_true_for_block_action(self):
        result = EvaluationResult(action_type=ActionType.BLOCK)
        assert result.is_blocked is True

    def test_is_blocked_property_is_false_for_allow_action(self):
        result = EvaluationResult(action_type=ActionType.ALLOW)
        assert result.is_blocked is False


class TestEvaluateCall:
    def test_evaluate_call_raises_value_error_for_empty_history(self):
        empty_history = CallHistory()
        policy = Policy(name="test", rules=[])

        with pytest.raises(ValueError, match="Call history cannot be empty"):
            evaluate_call(policy, empty_history)

    def test_evaluate_call_returns_allow_when_policy_has_no_rules(self, mock_history):
        policy = Policy(name="test", rules=[])
        result = evaluate_call(policy, mock_history)

        assert result.is_allowed
        assert result.violated_rule is None
        assert result.message is None

    def test_evaluate_call_returns_allow_when_allow_rule_is_triggered(
        self, policy_with_allow_rule, mock_history
    ):
        result = evaluate_call(policy_with_allow_rule, mock_history)

        assert result.is_allowed

    def test_evaluate_call_returns_block_when_block_rule_is_triggered(
        self, policy_with_block_rule, mock_history
    ):
        result = evaluate_call(policy_with_block_rule, mock_history)

        assert result.is_blocked
        assert result.violated_rule == "block_rule"
        assert result.message == "Block message"

    def test_evaluate_call_returns_allow_when_no_rule_condition_is_met(
        self, mock_history, mock_predicate_false
    ):
        rule = Rule(
            name="test_rule",
            condition=mock_predicate_false,
            action_type=ActionType.BLOCK,
            message="Should not trigger",
        )
        policy = Policy(name="test", rules=[rule])

        result = evaluate_call(policy, mock_history)

        assert result.is_allowed

    def test_evaluate_call_stops_processing_after_first_matching_allow_rule(
        self, mock_history
    ):
        allow_predicate = Mock(return_value=True)
        block_predicate = Mock(return_value=True)

        allow_rule = Rule(
            name="allow_rule", condition=allow_predicate, action_type=ActionType.ALLOW
        )
        block_rule = Rule(
            name="block_rule",
            condition=block_predicate,
            action_type=ActionType.BLOCK,
            message="Should not reach here",
        )
        policy = Policy(name="test", rules=[allow_rule, block_rule])

        result = evaluate_call(policy, mock_history)

        assert result.is_allowed
        allow_predicate.assert_called_once()
        block_predicate.assert_not_called()

    def test_evaluate_call_stops_processing_after_first_matching_block_rule(
        self, mock_history
    ):
        block_predicate = Mock(return_value=True)
        second_predicate = Mock(return_value=True)

        block_rule = Rule(
            name="block_rule",
            condition=block_predicate,
            action_type=ActionType.BLOCK,
            message="First block rule",
        )
        second_rule = Rule(
            name="second_rule", condition=second_predicate, action_type=ActionType.ALLOW
        )
        policy = Policy(name="test", rules=[block_rule, second_rule])

        result = evaluate_call(policy, mock_history)

        assert result.is_blocked
        assert result.violated_rule == "block_rule"
        block_predicate.assert_called_once()
        second_predicate.assert_not_called()

    def test_evaluate_call_passes_correct_parameters_to_rule_condition(
        self, mock_history, mock_tool_call
    ):
        predicate = Mock(return_value=True)
        rule = Rule(name="test_rule", condition=predicate, action_type=ActionType.ALLOW)
        policy = Policy(name="test", rules=[rule])

        evaluate_call(policy, mock_history)

        predicate.assert_called_once_with(mock_tool_call, mock_history)

    @patch("tramlines.guardrail.dsl.evaluator.logger")
    def test_evaluate_call_logs_exception_and_continues_on_rule_error(
        self, mock_logger, mock_history
    ):
        failing_predicate = Mock(side_effect=Exception("Test error"))
        working_predicate = Mock(return_value=True)

        failing_rule = Rule(
            name="failing_rule",
            condition=failing_predicate,
            action_type=ActionType.BLOCK,
        )
        working_rule = Rule(
            name="working_rule",
            condition=working_predicate,
            action_type=ActionType.ALLOW,
        )
        policy = Policy(name="test", rules=[failing_rule, working_rule])

        result = evaluate_call(policy, mock_history)

        assert result.is_allowed
        mock_logger.error.assert_called_once()
        assert (
            "Error evaluating rule 'failing_rule'" in mock_logger.error.call_args[0][0]
        )

    @patch("tramlines.guardrail.dsl.evaluator.logger")
    def test_evaluate_call_returns_allow_if_all_rules_fail_with_exceptions(
        self, mock_logger, mock_history
    ):
        failing_predicate_1 = Mock(side_effect=Exception("Error 1"))
        failing_predicate_2 = Mock(side_effect=Exception("Error 2"))

        rule_1 = Rule(
            name="rule_1", condition=failing_predicate_1, action_type=ActionType.BLOCK
        )
        rule_2 = Rule(
            name="rule_2", condition=failing_predicate_2, action_type=ActionType.BLOCK
        )
        policy = Policy(name="test", rules=[rule_1, rule_2])

        result = evaluate_call(policy, mock_history)

        assert result.is_allowed
        assert mock_logger.error.call_count == 2

    def test_evaluate_call_handles_block_rule_with_none_message(
        self, mock_history, mock_predicate_true
    ):
        rule = Rule(
            name="block_rule_none_msg",
            condition=mock_predicate_true,
            action_type=ActionType.BLOCK,
            message=None,
        )
        policy = Policy(name="test", rules=[rule])

        result = evaluate_call(policy, mock_history)

        assert result.is_blocked
        assert result.violated_rule == "block_rule_none_msg"
        assert result.message is None

    def test_evaluate_call_uses_latest_call_from_history(self, mock_tool_call):
        history = CallHistory()
        first_call = ToolCall("first", {}, datetime.now())
        history.add_call(first_call)
        history.add_call(mock_tool_call)

        predicate = Mock(return_value=True)
        rule = Rule(name="test", condition=predicate, action_type=ActionType.ALLOW)
        policy = Policy(name="test", rules=[rule])

        evaluate_call(policy, history)

        predicate.assert_called_once_with(mock_tool_call, history)

    def test_evaluate_call_respects_rule_order_in_policy(self, mock_history):
        block_first_policy = Policy(
            "Block First",
            rules=[
                Rule("Block", Mock(return_value=True), ActionType.BLOCK),
                Rule("Allow", Mock(return_value=True), ActionType.ALLOW),
            ],
        )

        allow_first_policy = Policy(
            "Allow First",
            rules=[
                Rule("Allow", Mock(return_value=True), ActionType.ALLOW),
                Rule("Block", Mock(return_value=True), ActionType.BLOCK),
            ],
        )

        block_result = evaluate_call(block_first_policy, mock_history)
        assert block_result.is_blocked

        allow_result = evaluate_call(allow_first_policy, mock_history)
        assert allow_result.is_allowed

    def test_evaluate_call_allows_if_non_matching_block_is_followed_by_matching_allow(
        self, mock_history
    ):
        policy = Policy(
            "Mixed Rules",
            rules=[
                Rule("Block", Mock(return_value=False), ActionType.BLOCK),
                Rule("Allow", Mock(return_value=True), ActionType.ALLOW),
            ],
        )

        result = evaluate_call(policy, mock_history)
        assert result.is_allowed

    def test_evaluation_result_equality_check_works_as_expected(self):
        allow1 = EvaluationResult(action_type=ActionType.ALLOW)
        allow2 = EvaluationResult(action_type=ActionType.ALLOW)
        block1 = EvaluationResult(ActionType.BLOCK, "rule1", "msg1")
        block2 = EvaluationResult(ActionType.BLOCK, "rule1", "msg1")
        block3 = EvaluationResult(ActionType.BLOCK, "rule2", "msg2")

        assert allow1 == allow2
        assert block1 == block2
        assert allow1 != block1
        assert block1 != block3
