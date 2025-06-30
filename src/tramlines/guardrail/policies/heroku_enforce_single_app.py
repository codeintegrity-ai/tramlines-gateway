"""
Heroku Single-App-Per-Session Policy

This policy restricts tool access to a single Heroku app per session.
Once a Heroku tool accesses a specific app ID or name, all subsequent
Heroku operations in that session must use the same app or be blocked.
"""

from tramlines.guardrail.dsl.predicates import custom
from tramlines.guardrail.dsl.rules import rule
from tramlines.guardrail.dsl.types import Policy
from tramlines.session import CallHistory, ToolCall

# List of Heroku tools that operate on an app context
HEROKU_APP_TOOLS = [
    "get_app_info",
    "list_app_config_vars",
    "set_app_config_vars",
    "restart_app",
    "get_app_addons",
    "add_app_addon",
    "delete_app_addon",
    "get_app_logs",
]


def _single_app_per_session_predicate(
    current_call: ToolCall, session_history: CallHistory
) -> bool:
    """
    Checks if the current Heroku tool call targets a different app
    than what was previously used in the session.
    """
    current_app_id = current_call.arguments.get("app")
    if not current_app_id:
        return False

    for prev_call in session_history.calls:
        if prev_call.name in HEROKU_APP_TOOLS:
            prev_app_id = prev_call.arguments.get("app")
            if prev_app_id and prev_app_id != current_app_id:
                return True

    return False


# The main policy object to be imported
policy = Policy(
    name="Heroku: Enforce Single App Per Session",
    description="Restricts tool access to one Heroku app per session to prevent cross-app data leakage or misconfiguration.",
    rules=[
        rule("Block cross-app Heroku operations")
        .when(custom(_single_app_per_session_predicate))
        .block("Access denied: You may only interact with one Heroku app per session."),
    ],
)
