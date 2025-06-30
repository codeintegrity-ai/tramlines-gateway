"""
Linear & Sentry Prompt Injection Protection Policy

This policy scans all parameters of Linear and Sentry tool calls for
prompt injection attempts and blocks any calls containing harmful input.
Uses LlamaFirewall's PromptGuard to detect jailbreak attempts and malicious prompts.
"""

from tramlines.guardrail.dsl.predicates import custom
from tramlines.guardrail.dsl.rules import rule
from tramlines.guardrail.dsl.types import Policy
from tramlines.guardrail.extensions.prompt_detector import detect_prompt
from tramlines.session import CallHistory, ToolCall

# List of Linear tools that operate on a team context
LINEAR_TOOLS = [
    "get_issue",
    "get_team_issues",
    "list_comments",
    "list_issues",
    "get_document",
    "list_documents",
]
SENTRY_TOOLS = ["get_issue_details"]


def _contains_harmful_input_predicate(
    current_call: ToolCall, session_history: CallHistory
) -> bool:
    """
    Checks if any parameter in Linear or Sentry tool calls contains
    prompt injection attempts or other harmful input.

    Scans all string parameters using the prompt detection extension
    to identify jailbreak attempts and malicious prompts.
    """
    # Only check Linear and Sentry tools
    if current_call.name not in LINEAR_TOOLS + SENTRY_TOOLS:
        return False

    # Check all parameter values for harmful content
    for param_value in current_call.arguments.values():
        if isinstance(param_value, str) and detect_prompt(param_value):
            return True
        # Also check nested structures like lists of strings
        elif isinstance(param_value, list):
            for item in param_value:
                if isinstance(item, str) and detect_prompt(item):
                    return True

    return False


def _linear_after_sentry_predicate(
    current_call: ToolCall, session_history: CallHistory
) -> bool:
    """
    Checks if a Linear tool call is being made immediately after a Sentry tool call.

    This prevents context switching from Sentry error tracking to Linear project
    management within the same session to avoid potential data leakage.
    """
    # Only apply to Linear tool calls
    if current_call.name not in LINEAR_TOOLS:
        return False

    # Check if the previous call was a Sentry tool
    # Note: session_history includes the current call at the end, so we need to check [-2]
    if len(session_history.calls) >= 1:
        previous_call = session_history.calls[-2]
        return previous_call.name in SENTRY_TOOLS

    return False


def _sentry_after_linear_predicate(
    current_call: ToolCall, session_history: CallHistory
) -> bool:
    """
    Checks if a Sentry tool call is being made immediately after a Linear tool call.

    This prevents context switching from Linear project management to Sentry error
    tracking within the same session to avoid potential data leakage.
    """
    # Only apply to Sentry tool calls
    if current_call.name not in SENTRY_TOOLS:
        return False

    # Check if the previous call was a Linear tool
    # Note: session_history includes the current call at the end, so we need to check [-2]
    if len(session_history.calls) >= 2:
        previous_call = session_history.calls[-2]
        return previous_call.name in LINEAR_TOOLS

    return False


# The main policy object to be imported
policy = Policy(
    name="Linear & Sentry: Context Separation & Security",
    description="Prevents context switching between Linear and Sentry tools and blocks harmful input to maintain security boundaries.",
    rules=[
        rule("Block harmful input in Linear/Sentry calls")
        .when(custom(_contains_harmful_input_predicate))
        .block(
            "Access denied: Harmful or malicious input detected in tool parameters. Please ensure your input does not contain prompt injection attempts."
        ),
        rule("Block Linear calls after Sentry calls")
        .when(custom(_linear_after_sentry_predicate))
        .block(
            "Access denied: Cannot switch from Sentry tools to Linear tools within the same session to prevent data leakage."
        ),
        rule("Block Sentry calls after Linear calls")
        .when(custom(_sentry_after_linear_predicate))
        .block(
            "Access denied: Cannot switch from Linear tools to Sentry tools within the same session to prevent data leakage."
        ),
    ],
)
