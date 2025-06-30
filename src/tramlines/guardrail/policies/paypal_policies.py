"""
PayPal Mutation Prevention Policy

This policy blocks all PayPal tools that cause mutations (create, send, cancel operations)
and allows only read-only operations like listing and getting invoices.
"""

from tramlines.guardrail.dsl.predicates import custom
from tramlines.guardrail.dsl.rules import rule
from tramlines.guardrail.dsl.types import Policy
from tramlines.session import CallHistory, ToolCall

# List of PayPal tools that operate on invoice context
PAYPAL_INVOICE_TOOLS = [
    "create_invoice",
    "send_invoice",
    "list_invoices",
    "send_invoice_reminder",
    "generate_invoice_qr_code",
    "get_invoice",
    "cancel_sent_invoice",
]

# List of PayPal tools that are read-only (don't cause mutations)
PAYPAL_READ_ONLY_TOOLS = [
    "list_invoices",
    "get_invoice",
]

# List of PayPal tools that cause mutations
PAYPAL_MUTATION_TOOLS = [
    tool for tool in PAYPAL_INVOICE_TOOLS if tool not in PAYPAL_READ_ONLY_TOOLS
]


def _is_mutation_tool_predicate(
    current_call: ToolCall, session_history: CallHistory
) -> bool:
    """
    Checks if the current tool call is a PayPal mutation tool.

    Mutation tools are those that create, modify, or delete data,
    as opposed to read-only tools that only retrieve information.
    """
    return current_call.name in PAYPAL_MUTATION_TOOLS


def _create_invoice_too_frequent_predicate(
    current_call: ToolCall, session_history: CallHistory
) -> bool:
    """
    Checks if the current create_invoice call is being made within 5 minutes
    of any previous create_invoice call.

    This prevents rapid-fire invoice creation which could be abusive or
    indicate automated spam behavior.
    """
    # Only apply to create_invoice calls
    if current_call.name != "create_invoice":
        return False

    # Get current timestamp
    current_time = current_call.timestamp

    # Check all previous calls in session history
    for previous_call in session_history.calls[:-1]:  # Exclude current call
        if previous_call.name == "create_invoice":
            # Calculate time difference
            time_diff = abs((current_time - previous_call.timestamp).total_seconds())

            # Block if difference is less than 5 minutes (300 seconds)
            if time_diff < 300:
                return True

    return False


def _create_invoice_after_read_predicate(
    current_call: ToolCall, session_history: CallHistory
) -> bool:
    """
    Checks if the current create_invoice call is being made immediately after
    a list_invoices or get_invoice call.

    This prevents creating invoices immediately after reading invoice data,
    which could indicate automated invoice creation based on existing data.
    """
    # Only apply to create_invoice calls
    if current_call.name != "create_invoice":
        return False

    # Check if there's at least one previous call
    if len(session_history.calls) < 2:  # Need at least previous call + current call
        return False

    # Get the immediately previous call (second to last, since current call is last)
    previous_call = session_history.calls[-2]

    # Block if previous call was list_invoices or get_invoice
    return previous_call.name in ["list_invoices", "get_invoice"]


# Rule for blocking create_policy tool
create_policy_block_rule = (
    rule("Block create_policy tool")
    .when(
        custom(
            lambda current_call, session_history: current_call.name == "create_policy"
        )
    )
    .block("The create_policy tool is disabled and cannot be used.")
)

# The main policy object to be imported
policy = Policy(
    name="PayPal: Block Mutation Tools",
    description="Blocks all PayPal tools that cause mutations, allowing only read-only operations like listing and getting invoices.",
    rules=[
        rule("Block PayPal mutation tools")
        .when(custom(_is_mutation_tool_predicate))
        .block(
            "Access denied: PayPal mutation operations are not allowed. Only read-only operations (list_invoices, get_invoice) are permitted."
        ),
    ],
)
