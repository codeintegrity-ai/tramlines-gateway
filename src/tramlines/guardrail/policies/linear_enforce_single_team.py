"""
Linear Single-Team-Per-Session Policy

This policy restricts tool access to a single Linear team per session.
Once a Linear tool accesses a specific team ID, all subsequent Linear
operations in that session must use the same team ID or be blocked.
"""

from tramlines.guardrail.dsl.predicates import custom
from tramlines.guardrail.dsl.rules import rule
from tramlines.guardrail.dsl.types import Policy
from tramlines.session import CallHistory, ToolCall

# List of Linear tools that operate on a team context
LINEAR_TEAM_TOOLS = [
    "create_comment",
    "create_issue",
    "create_project",
    "create_project_update",
    "get_issue",
    "get_project",
    "get_team_issues",
    "get_team_projects",
    "list_comments",
    "list_issues",
    "list_projects",
    "update_issue",
    "update_project",
]


def _single_team_per_session_predicate(
    current_call: ToolCall, session_history: CallHistory
) -> bool:
    """
    Checks if the current Linear tool call targets a different team
    than what was previously used in the session.
    """
    current_team_id = current_call.arguments.get("team_id")
    if not current_team_id:
        return False

    for prev_call in session_history.calls:
        if prev_call.name in LINEAR_TEAM_TOOLS:
            prev_team_id = prev_call.arguments.get("team_id")
            if prev_team_id and prev_team_id != current_team_id:
                return True

    return False


# The main policy object to be imported
policy = Policy(
    name="Linear: Enforce Single Team Per Session",
    description="Restricts tool access to one Linear team per session to prevent cross-team data leakage.",
    rules=[
        rule("Block cross-team Linear operations")
        .when(custom(_single_team_per_session_predicate))
        .block(
            "Access denied: You may only interact with one Linear team per session."
        ),
    ],
)
