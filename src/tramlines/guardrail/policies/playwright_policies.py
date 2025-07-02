"""
Playwright Browser Automation Policy

This policy blocks a tool if it is called 5 times in a row and 
blocks a sequence of n tool calls (where n >= 3 and n <= 6) repeats >= 3 times contiguously.
"""

from tramlines.guardrail.dsl.predicates import custom
from tramlines.guardrail.dsl.rules import rule
from tramlines.guardrail.dsl.types import Policy
from tramlines.session import CallHistory, ToolCall

PLAYWRIGHT_BROWSER_TOOLS = [
    "browser_close",
    "browser_resize",
    "browser_console_messages",
    "browser_handle_dialog",
    "browser_file_upload",
    "browser_install",
    "browser_press_key",
    "browser_navigate",
    "browser_navigate_back",
    "browser_navigate_forward",
    "browser_network_requests",
    "browser_pdf_save",
    "browser_take_screenshot",
    "browser_snapshot",
    "browser_click",
    "browser_drag",
    "browser_hover",
    "browser_type",
    "browser_select_option",
    "browser_tab_list",
    "browser_tab_new",
    "browser_tab_select",
    "browser_tab_close",
    "browser_generate_playwright_test",
    "browser_wait_for",
]

def _tool_called_five_times_contiguously(current_call: ToolCall, session_history: CallHistory) -> bool:
    """
    Check if the current tool has been called 5 times in a contiguous sequence.
    Note: The current call is already in the history when this is evaluated.
    """
    # We need at least 5 calls to have 5 consecutive calls
    if len(session_history.calls) < 5:
        return False
    
    # Get the last 5 calls from history (including the current call)
    last_five_calls = session_history.calls[-5:]
    
    # Check if all 5 calls are the same tool
    first_tool_name = last_five_calls[0].name
    return all(call.name == first_tool_name for call in last_five_calls)


def _sequence_repeats_more_than_three_times(current_call: ToolCall, session_history: CallHistory) -> bool:
    """
    Check if a sequence of n tool calls (where n >= 3 and n <= 6) repeats >= 3 times contiguously.
    """
    calls = session_history.calls
    
    # Need at least 9 calls for a 3-tool pattern repeated 3 times
    if len(calls) < 9:
        return False
    
    # Check for patterns of different lengths (3 to 6 tools)
    for pattern_length in range(3, min(7, len(calls) // 3 + 1)):
        # Check if we have enough calls for 3 repetitions of this pattern
        if len(calls) < pattern_length * 3:
            continue
            
        # Get the most recent calls that could form 3+ repetitions
        recent_calls = calls[-(pattern_length * 3):]
        
        # Extract the pattern (first occurrence)
        pattern = [call.name for call in recent_calls[:pattern_length]]
        
        # Check if this pattern repeats 3 times
        is_repeating = True
        for i in range(3):
            start_idx = i * pattern_length
            end_idx = start_idx + pattern_length
            current_segment = [call.name for call in recent_calls[start_idx:end_idx]]
            if current_segment != pattern:
                is_repeating = False
                break
        
        if is_repeating:
            return True
    
    return False

# The main policy object to be imported
policy = Policy(
    name="Playwright Browser Automation Policy",
    description="Manages access to Playwright browser automation tools and prevents excessive contiguous tool usage.",
    rules=[
        rule("Block tools called 5 times contiguously")
        .when(custom(_tool_called_five_times_contiguously))
        .block(
            "Tool call blocked: The same tool has been called 5 times in a row. Please vary your approach"
        ),
        rule("Block repeating tool sequences")
        .when(custom(_sequence_repeats_more_than_three_times))
        .block(
            "Tool call blocked: A repeating sequence of tools has been detected more than 3 times. Please vary your workflow"
        ),
    ],
)
