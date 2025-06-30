"""
Notion Single-Page-Per-Session Policy

This policy restricts tool access to a single Notion page per session.
Once a Notion tool accesses a specific page ID, all subsequent Notion
operations in that session must use the same page ID or be blocked.
"""

from tramlines.guardrail.dsl.predicates import custom
from tramlines.guardrail.dsl.rules import rule
from tramlines.guardrail.dsl.types import Policy
from tramlines.session import CallHistory, ToolCall

# List of Notion tools that operate on a page context
NOTION_PAGE_TOOLS = [
    "create_comment",
    "get_page_content",
    "update_page_content",
    "add_page_to_favorites",
    "remove_page_from_favorites",
    "archive_page",
]


def _single_page_per_session_predicate(
    current_call: ToolCall, session_history: CallHistory
) -> bool:
    """
    Checks if the current Notion tool call targets a different page
    than what was previously used in the session.
    """
    current_page_id = current_call.arguments.get("page_id")
    if not current_page_id:
        return False

    for prev_call in session_history.calls:
        if prev_call.name in NOTION_PAGE_TOOLS:
            prev_page_id = prev_call.arguments.get("page_id")
            if prev_page_id and prev_page_id != current_page_id:
                return True

    return False


# The main policy object to be imported
policy = Policy(
    name="Notion: Enforce Single Page Per Session",
    description="Restricts tool access to one Notion page per session to prevent cross-page data leakage.",
    rules=[
        rule("Block cross-page Notion operations")
        .when(custom(_single_page_per_session_predicate))
        .block(
            "Access denied: You may only interact with one Notion page per session."
        ),
    ],
)
