"""
GitHub Single-Repository-Per-Session Policy

This policy restricts tool access to a single GitHub repository per session.
Once a GitHub tool accesses a specific owner/repo combination, all subsequent
GitHub operations in that session must use the same owner/repo or be blocked.
"""

from tramlines.guardrail.dsl.predicates import custom
from tramlines.guardrail.dsl.rules import rule
from tramlines.guardrail.dsl.types import Policy
from tramlines.session import CallHistory, ToolCall

# List of GitHub tools that operate on a repository context
GITHUB_REPO_TOOLS = [
    "add_issue_comment",
    "add_pull_request_review_comment",
    "create_branch",
    "create_issue",
    "create_or_update_file",
    "create_pull_request",
    "create_pull_request_review",
    "delete_file",
    "fork_repository",
    "get_code_scanning_alert",
    "get_commit",
    "get_file_contents",
    "get_issue",
    "get_issue_comments",
    "get_pull_request",
    "get_pull_request_comments",
    "get_pull_request_files",
    "get_pull_request_reviews",
    "get_pull_request_status",
    "get_secret_scanning_alert",
    "get_tag",
    "list_branches",
    "list_code_scanning_alerts",
    "list_commits",
    "list_issues",
    "list_pull_requests",
    "list_secret_scanning_alerts",
    "list_tags",
    "merge_pull_request",
    "push_files",
    "request_copilot_review",
    "update_issue",
    "update_pull_request",
    "update_pull_request_branch",
]


def _single_repo_per_session_predicate(
    current_call: ToolCall, session_history: CallHistory
) -> bool:
    """
    Checks if the current GitHub tool call targets a different repository
    than what was previously used in the session.
    """
    current_owner = current_call.arguments.get("owner")
    current_repo = current_call.arguments.get("repo")

    # This rule only applies if the tool call specifies an owner and repo
    if not current_owner or not current_repo:
        return False

    # Find the first repository used in the session history
    for prev_call in session_history.calls:
        if prev_call.name in GITHUB_REPO_TOOLS:
            prev_owner = prev_call.arguments.get("owner")
            prev_repo = prev_call.arguments.get("repo")

            # If a different repo was used previously, trigger the block
            if (
                prev_owner
                and prev_repo
                and (prev_owner != current_owner or prev_repo != current_repo)
            ):
                return True

    return False


# The main policy object to be imported
policy = Policy(
    name="GitHub: Enforce Single Repository Per Session",
    description="Restricts tool access to one GitHub repository per session to prevent cross-repo attacks.",
    rules=[
        rule("Block cross-repository GitHub operations")
        .when(custom(_single_repo_per_session_predicate))
        .block(
            "Access denied: You may only interact with one GitHub repository per session."
        ),
    ],
)
