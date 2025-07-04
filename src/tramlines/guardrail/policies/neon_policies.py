"""
Neon Database Policy

This policy blocks the run_sql tool if it is called twice in any session.
"""

from tramlines.guardrail.dsl.predicates import custom
from tramlines.guardrail.dsl.rules import rule
from tramlines.guardrail.dsl.types import Policy
from tramlines.session import CallHistory, ToolCall

NEON_DATABASE_TOOLS = [
    "mcp_tramlines-proxy_run_sql",
]

def _sql_contains_delete_command(
    current_call: ToolCall, session_history: CallHistory
) -> bool:
    """
    Check if the current run_sql call contains a DELETE command in the SQL statement.
    """
    # Only check run_sql calls
    if current_call.name != "mcp_tramlines-proxy_run_sql":
        return False
    
    # Get the SQL parameter from the call
    sql_statement = current_call.arguments.get("params", {}).get("sql", "")
    
    # Check if SQL contains DELETE command (case insensitive)
    return "DELETE" in sql_statement.upper()

def _run_sql_called_twice(
    current_call: ToolCall, session_history: CallHistory
) -> bool:
    """
    Check if the run_sql tool has been called twice in the session.
    Note: The current call is already in the history when this is evaluated.
    """
    # Count how many times run_sql has been called
    run_sql_count = sum(
        1 for call in session_history.calls 
        if call.name == "mcp_tramlines-proxy_run_sql"
    )
    
    # Block if this is the second call
    return run_sql_count >= 2

# The main policy object to be imported
policy = Policy(
    name="Neon Database Policy",
    description="Manages access to Neon database tools and prevents excessive SQL execution.",
    rules=[
        rule("Block run_sql tool after second call")
        .when(custom(_run_sql_called_twice))
        .block(
            "Tool call blocked: The run_sql tool has already been called twice in this session. Please use alternative approaches"
        ),
    ],
)
