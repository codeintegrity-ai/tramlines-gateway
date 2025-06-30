import re
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from tramlines.guardrail.dsl.predicates import (
    AndPredicate,
    BasePredicate,
    ComparisonPredicate,
    CustomPredicate,
    HistoricalCallBuilder,
    HistoryExistsPredicate,
    HistoryQueryBuilder,
    NotPredicate,
    OrPredicate,
    StringValueBuilder,
    ValueBuilder,
    _parse_time_window,
    custom,
)
from tramlines.session import CallHistory, ToolCall


class MockPredicate(BasePredicate):
    def __init__(self, result: bool):
        self.result = result

    def __call__(self, call: ToolCall, history: CallHistory) -> bool:
        return self.result


@pytest.fixture
def mock_call():
    return ToolCall(
        name="test_tool",
        arguments={"user": "admin", "action": "delete"},
        timestamp=datetime.now(),
    )


@pytest.fixture
def mock_history():
    history = Mock(spec=CallHistory)
    history.states = {"active", "verified"}

    now = datetime.now()
    call1 = ToolCall(
        name="read_file",
        arguments={"user": "alice", "path": "/test"},
        timestamp=now,
    )
    call2 = ToolCall(
        name="write_file",
        arguments={"user": "bob", "path": "/test2"},
        timestamp=now,
    )

    history.calls = [call1, call2]
    return history


class TestLogicalOperators:
    def test_and_predicate_returns_true_when_both_operands_are_true(
        self, mock_call, mock_history
    ):
        left = MockPredicate(True)
        right = MockPredicate(True)
        predicate = AndPredicate(left, right)
        assert predicate(mock_call, mock_history) is True

    def test_and_predicate_returns_false_when_one_operand_is_false(
        self, mock_call, mock_history
    ):
        left = MockPredicate(True)
        right = MockPredicate(False)
        predicate = AndPredicate(left, right)
        assert predicate(mock_call, mock_history) is False

    def test_or_predicate_returns_true_when_one_operand_is_true(
        self, mock_call, mock_history
    ):
        left = MockPredicate(False)
        right = MockPredicate(True)
        predicate = OrPredicate(left, right)
        assert predicate(mock_call, mock_history) is True

    def test_or_predicate_returns_false_when_both_operands_are_false(
        self, mock_call, mock_history
    ):
        left = MockPredicate(False)
        right = MockPredicate(False)
        predicate = OrPredicate(left, right)
        assert predicate(mock_call, mock_history) is False

    def test_not_predicate_inverts_true_to_false(self, mock_call, mock_history):
        predicate = NotPredicate(MockPredicate(True))
        assert predicate(mock_call, mock_history) is False

    def test_not_predicate_inverts_false_to_true(self, mock_call, mock_history):
        predicate = NotPredicate(MockPredicate(False))
        assert predicate(mock_call, mock_history) is True

    def test_base_predicate_supports_logical_operators(self, mock_call, mock_history):
        left = MockPredicate(True)
        right = MockPredicate(False)

        and_result = left & right
        assert isinstance(and_result, AndPredicate)
        assert and_result(mock_call, mock_history) is False

        or_result = left | right
        assert isinstance(or_result, OrPredicate)
        assert or_result(mock_call, mock_history) is True

        not_result = ~left
        assert isinstance(not_result, NotPredicate)
        assert not_result(mock_call, mock_history) is False


class TestValueBuilder:
    def test_value_builder_equality_check_returns_true_on_match(
        self, mock_call, mock_history
    ):
        builder = ValueBuilder(lambda c, h: c.name)
        predicate = builder == "test_tool"
        assert predicate(mock_call, mock_history) is True

    def test_value_builder_inequality_check_returns_true_on_mismatch(
        self, mock_call, mock_history
    ):
        builder = ValueBuilder(lambda c, h: c.name)
        predicate = builder != "other_tool"
        assert predicate(mock_call, mock_history) is True

    def test_value_builder_greater_than_check_is_correct(self, mock_call, mock_history):
        builder = ValueBuilder(lambda c, h: 10)
        predicate = builder > 5
        assert predicate(mock_call, mock_history) is True

    def test_value_builder_less_than_check_is_correct(self, mock_call, mock_history):
        builder = ValueBuilder(lambda c, h: 3)
        predicate = builder < 5
        assert predicate(mock_call, mock_history) is True

    def test_value_builder_greater_or_equal_check_is_correct(
        self, mock_call, mock_history
    ):
        builder = ValueBuilder(lambda c, h: 5)
        predicate = builder >= 5
        assert predicate(mock_call, mock_history) is True

    def test_value_builder_less_or_equal_check_is_correct(
        self, mock_call, mock_history
    ):
        builder = ValueBuilder(lambda c, h: 5)
        predicate = builder <= 5
        assert predicate(mock_call, mock_history) is True


class TestStringValueBuilder:
    def test_matches_returns_true_for_matching_string_pattern(
        self, mock_call, mock_history
    ):
        builder = StringValueBuilder(lambda c, h: c.name)
        predicate = builder.matches(r"test_.*")
        assert predicate(mock_call, mock_history) is True

    def test_matches_returns_true_for_matching_compiled_pattern(
        self, mock_call, mock_history
    ):
        pattern = re.compile(r"test_.*")
        builder = StringValueBuilder(lambda c, h: c.name)
        predicate = builder.matches(pattern)
        assert predicate(mock_call, mock_history) is True

    def test_is_in_returns_true_when_value_in_list(self, mock_call, mock_history):
        builder = StringValueBuilder(lambda c, h: c.name)
        predicate = builder.is_in(["test_tool", "other_tool"])
        assert predicate(mock_call, mock_history) is True

    def test_contains_returns_true_for_contained_string(self, mock_call, mock_history):
        builder = StringValueBuilder(lambda c, h: c.name)
        predicate = builder.contains("test")
        assert predicate(mock_call, mock_history) is True

    def test_startswith_returns_true_for_correct_prefix(self, mock_call, mock_history):
        builder = StringValueBuilder(lambda c, h: c.name)
        predicate = builder.startswith("test")
        assert predicate(mock_call, mock_history) is True

    def test_endswith_returns_true_for_correct_suffix(self, mock_call, mock_history):
        builder = StringValueBuilder(lambda c, h: c.name)
        predicate = builder.endswith("tool")
        assert predicate(mock_call, mock_history) is True

    def test_string_methods_return_false_when_value_is_none(
        self, mock_call, mock_history
    ):
        builder = StringValueBuilder(lambda c, h: None)
        assert builder.matches(".*")(mock_call, mock_history) is False
        assert builder.is_in(["test"])(mock_call, mock_history) is False
        assert builder.contains("test")(mock_call, mock_history) is False
        assert builder.startswith("test")(mock_call, mock_history) is False
        assert builder.endswith("test")(mock_call, mock_history) is False

    def test_string_methods_return_false_for_non_string_values(
        self, mock_call, mock_history
    ):
        int_builder = StringValueBuilder(lambda c, h: 8080)
        bool_builder = StringValueBuilder(lambda c, h: True)
        list_builder = StringValueBuilder(lambda c, h: [1, 2, 3])

        assert int_builder.matches(r"\d+")(mock_call, mock_history) is False
        assert int_builder.contains("80")(mock_call, mock_history) is False
        assert int_builder.startswith("808")(mock_call, mock_history) is False
        assert int_builder.endswith("80")(mock_call, mock_history) is False
        assert int_builder.is_in(["8080"])(mock_call, mock_history) is False

        assert bool_builder.contains("True")(mock_call, mock_history) is False
        assert list_builder.contains("1")(mock_call, mock_history) is False


class TestComparisonPredicate:
    def test_comparison_predicate_returns_true_on_successful_comparison(
        self, mock_call, mock_history
    ):
        predicate = ComparisonPredicate(
            lambda c, h: c.name, lambda a, b: a == b, "test_tool"
        )
        assert predicate(mock_call, mock_history) is True

    def test_comparison_predicate_returns_false_when_value_is_none(
        self, mock_call, mock_history
    ):
        predicate = ComparisonPredicate(lambda c, h: None, lambda a, b: a == b, "test")
        assert predicate(mock_call, mock_history) is False

    def test_comparison_predicate_returns_false_on_type_error(
        self, mock_call, mock_history
    ):
        predicate = ComparisonPredicate(lambda c, h: "string", lambda a, b: a > b, 5)
        assert predicate(mock_call, mock_history) is False

    def test_comparison_predicate_returns_false_on_value_error(
        self, mock_call, mock_history
    ):
        def bad_comparison(a, b):
            raise ValueError("Bad comparison")

        predicate = ComparisonPredicate(lambda c, h: "test", bad_comparison, "test")
        assert predicate(mock_call, mock_history) is False


class TestHistoryQueryBuilder:
    def test_exists_returns_true_when_calls_match_pattern(
        self, mock_call, mock_history
    ):
        builder = HistoryQueryBuilder(".*_file")
        predicate = builder.exists()
        assert predicate(mock_call, mock_history) is True

    def test_exists_returns_false_when_no_calls_match_pattern(
        self, mock_call, mock_history
    ):
        builder = HistoryQueryBuilder("no_match")
        predicate = builder.exists()
        assert predicate(mock_call, mock_history) is False

    def test_exists_with_where_clause_filters_calls(self, mock_call, mock_history):
        condition = MockPredicate(True)
        builder = HistoryQueryBuilder(".*_file").where(condition)
        predicate = builder.exists()
        assert predicate(mock_call, mock_history) is True

    def test_count_returns_total_matching_calls(self, mock_call, mock_history):
        builder = HistoryQueryBuilder(".*_file")
        counter = builder.count()
        result = counter._extractor(mock_call, mock_history)
        assert result == 2

    def test_count_within_time_window_filters_by_timestamp(
        self, mock_call, mock_history
    ):
        builder = HistoryQueryBuilder(".*_file")
        counter = builder.count(within="1h")
        result = counter._extractor(mock_call, mock_history)
        assert result == 2

    def test_count_with_condition_filters_calls(self, mock_call, mock_history):
        condition = MockPredicate(True)
        builder = HistoryQueryBuilder(".*_file").where(condition)
        counter = builder.count()
        result = counter._extractor(mock_call, mock_history)
        assert result == 2

    def test_count_with_condition_and_time_window(self, mock_call, mock_history):
        condition = MockPredicate(True)
        builder = HistoryQueryBuilder(".*_file").where(condition)
        counter = builder.count(within="1h")
        result = counter._extractor(mock_call, mock_history)
        assert result == 2

    def test_last_returns_builder_for_last_matching_call(self, mock_call, mock_history):
        builder = HistoryQueryBuilder(".*_file").last()
        assert isinstance(builder, HistoricalCallBuilder)
        assert builder._reverse is True

    def test_first_returns_builder_for_first_matching_call(
        self, mock_call, mock_history
    ):
        builder = HistoryQueryBuilder(".*_file").first()
        assert isinstance(builder, HistoricalCallBuilder)
        assert builder._reverse is False

    def test_history_query_builder_handles_string_pattern(
        self, mock_call, mock_history
    ):
        builder = HistoryQueryBuilder("read_file")
        assert builder.exists()(mock_call, mock_history) is True

    def test_history_query_builder_handles_compiled_regex_pattern(
        self, mock_call, mock_history
    ):
        pattern = re.compile("read_file")
        builder = HistoryQueryBuilder(pattern)
        assert builder.exists()(mock_call, mock_history) is True


class TestHistoryExistsPredicate:
    def test_history_exists_predicate_true_without_condition(
        self, mock_call, mock_history
    ):
        predicate = HistoryExistsPredicate(re.compile(".*_file"), None)
        assert predicate(mock_call, mock_history) is True

    def test_history_exists_predicate_true_with_matching_condition(
        self, mock_call, mock_history
    ):
        predicate = HistoryExistsPredicate(re.compile(".*_file"), MockPredicate(True))
        assert predicate(mock_call, mock_history) is True

    def test_history_exists_predicate_false_with_non_matching_condition(
        self, mock_call, mock_history
    ):
        predicate = HistoryExistsPredicate(re.compile(".*_file"), MockPredicate(False))
        assert predicate(mock_call, mock_history) is False

    def test_history_exists_predicate_false_with_no_matching_pattern(
        self, mock_call, mock_history
    ):
        predicate = HistoryExistsPredicate(re.compile("no_match"), None)
        assert predicate(mock_call, mock_history) is False


class TestHistoricalCallBuilder:
    def test_historical_call_builder_finds_last_matching_call(
        self, mock_call, mock_history
    ):
        builder = HistoryQueryBuilder(".*_file").last()
        call = builder._find_matching_call(mock_call, mock_history)
        assert call is not None
        assert call.name == "write_file"

    def test_historical_call_builder_finds_first_matching_call(
        self, mock_call, mock_history
    ):
        builder = HistoryQueryBuilder(".*_file").first()
        call = builder._find_matching_call(mock_call, mock_history)
        assert call is not None
        assert call.name == "read_file"

    def test_historical_call_builder_applies_where_condition(
        self, mock_call, mock_history
    ):
        def condition(call, history):
            return call.name == "read_file"

        builder = HistoryQueryBuilder(".*_file").where(condition).last()
        call = builder._find_matching_call(mock_call, mock_history)
        assert call is not None
        assert call.name == "read_file"

    def test_historical_call_builder_returns_none_for_no_match(
        self, mock_call, mock_history
    ):
        builder = HistoryQueryBuilder("no_match").last()
        call = builder._find_matching_call(mock_call, mock_history)
        assert call is None

    def test_name_property_returns_call_name_for_match(self, mock_call, mock_history):
        builder = HistoryQueryBuilder(".*_file").last()
        value = builder.name._extractor(mock_call, mock_history)
        assert value == "write_file"

    def test_name_property_returns_none_for_no_match(self, mock_call, mock_history):
        builder = HistoryQueryBuilder("no_match").last()
        value = builder.name._extractor(mock_call, mock_history)
        assert value is None

    def test_arg_property_returns_argument_value_for_match(
        self, mock_call, mock_history
    ):
        builder = HistoryQueryBuilder(".*_file").last()
        value = builder.arg("user")._extractor(mock_call, mock_history)
        assert value == "bob"

    def test_arg_property_returns_none_for_no_match(self, mock_call, mock_history):
        builder = HistoryQueryBuilder("no_match").last()
        value = builder.arg("user")._extractor(mock_call, mock_history)
        assert value is None


class TestCustomPredicate:
    def test_custom_predicate_executes_provided_function(self, mock_call, mock_history):
        def custom_func(call, history):
            return call.name == "test_tool"

        predicate = CustomPredicate(custom_func)
        assert predicate(mock_call, mock_history) is True

    def test_custom_predicate_passes_history_to_function(self, mock_call, mock_history):
        def custom_func(call, history):
            return "active" in history.states

        predicate = CustomPredicate(custom_func)
        assert predicate(mock_call, mock_history) is True

    def test_custom_decorator_creates_custom_predicate(self, mock_call, mock_history):
        @custom
        def my_predicate(call, history):
            return call.name == "test_tool"

        assert isinstance(my_predicate, CustomPredicate)
        assert my_predicate(mock_call, mock_history) is True


class TestTimeWindowParsing:
    def test_time_window_parser_handles_seconds(self):
        td = _parse_time_window("30s")
        assert td == timedelta(seconds=30)

    def test_time_window_parser_handles_minutes(self):
        td = _parse_time_window("10m")
        assert td == timedelta(minutes=10)

    def test_time_window_parser_handles_hours(self):
        td = _parse_time_window("2h")
        assert td == timedelta(hours=2)

    def test_time_window_parser_handles_days(self):
        td = _parse_time_window("7d")
        assert td == timedelta(days=7)

    def test_time_window_parser_is_case_insensitive(self):
        td = _parse_time_window("5H")
        assert td == timedelta(hours=5)

    def test_time_window_parser_raises_error_for_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid time window format"):
            _parse_time_window("10")

    def test_time_window_parser_raises_error_for_invalid_unit(self):
        with pytest.raises(ValueError, match="Invalid time window format"):
            _parse_time_window("10y")


class TestEdgeCases:
    def test_history_queries_handle_empty_call_history(self, mock_call):
        history = Mock(spec=CallHistory)
        history.calls = []

        builder = HistoryQueryBuilder(".*")
        assert builder.exists()(mock_call, history) is False
        assert builder.count()._extractor(mock_call, history) == 0
        assert builder.last().name._extractor(mock_call, history) is None

    def test_time_window_filter_handles_none_timestamp(self, mock_call, mock_history):
        mock_history.calls.append(ToolCall("none_ts", {}, None))
        builder = HistoryQueryBuilder("none_ts")
        count = builder.count(within="1h")._extractor(mock_call, mock_history)
        assert count == 0

    def test_time_window_filter_excludes_old_timestamps(self, mock_call, mock_history):
        old_call = ToolCall("old_call", {}, datetime.now() - timedelta(hours=2))
        mock_history.calls.append(old_call)

        builder = HistoryQueryBuilder(".*")
        count = builder.count(within="1h")._extractor(mock_call, mock_history)
        assert count == 2

    def test_count_returns_zero_for_no_matching_pattern(self, mock_call, mock_history):
        builder = HistoryQueryBuilder("non_existent_pattern")
        count = builder.count()._extractor(mock_call, mock_history)
        assert count == 0
