# Rule Reference

A **Rule** is a single security constraint within a policy that defines:
- **A condition** (when to trigger the rule)
- **An action** (what to do when the condition is met)
- **A message** (optional explanation for blocks)

Rules are immutable and use a fluent builder pattern for construction.

## Basic Rule Structure

```python
from tramlines.guardrail.dsl.rules import rule
from tramlines.guardrail.dsl.context import call

# Basic rule structure
my_rule = (rule("Descriptive rule name")
    .when(call.name == "dangerous_tool")
    .block("This tool is not allowed"))
```

## Rule Builder Pattern

Rules use a fluent builder pattern that enforces proper construction:

```python
rule("Rule name")        # 1. Start with a descriptive name
.when(condition)         # 2. Define the triggering condition  
.block("message")        # 3. Specify the action (block or allow)

# Alternative action
rule("Rule name")
.when(condition)
.allow()                 # Allow action (no message needed)
```

## Building Conditions with Predicates

### Basic Call Properties

Access properties of the current tool call using the `call` context:

```python
from tramlines.guardrail.dsl.context import call

# Match tool names
call.name == "get_user_data"

# Check arguments
call.arg("user_id") == "admin"
call.arg("query").contains("DROP", "DELETE")
```

### String Operations

The DSL provides rich string operations for building conditions:

```python
# Equality and comparison
call.name == "delete_user"
call.arg("priority") != "low"

# Pattern matching with regex
call.name.matches(r"^(create|update)_.*")
call.arg("email").matches(r".*@company\.com$")

# String content checks
call.arg("query").contains("DROP", "DELETE", "TRUNCATE")
call.name.startswith("admin_")
call.arg("filename").endswith(".sql", ".exe")
```

### Logical Operators

Combine conditions using Python's logical operators:

```python
# AND operations
(call.name == "transfer_money") & (call.arg("amount") > 10000)

# OR operations  
(call.name == "delete_user") | (call.name == "deactivate_user")

```

### History-Based Conditions

Query session history for complex patterns:

```python
from tramlines.guardrail.dsl.context import history

# Check if any calls occurred
history.select(r"github_.*").exists()

# Count tool calls within time window
history.select("send_email").count(within="1h") > 5

# Access historical call properties
history.select("create_.*").last().arg("user_id") == call.arg("user_id")

# Complex history queries
history.select("create_user").where(call.arg("role") == "admin").count() > 0
```

#### Time Windows

History queries support time-based filtering:

```python
# Count calls in different time windows
history.select("api_call").count(within="1m")   # Last minute
history.select("api_call").count(within="1h")   # Last hour  
history.select("api_call").count(within="1d")   # Last day
history.select("api_call").count(within="30s")  # Last 30 seconds

# Time window formats
"10s"  # 10 seconds
"5m"   # 5 minutes
"2h"   # 2 hours
"1d"   # 1 day
```

## Rule Actions

Rules can take two types of actions:

### Block Actions

Block actions prevent the tool call from executing and return an error message:

```python
rule("Block dangerous operations")
.when(call.name.contains("delete", "destroy"))
.block("Destructive operations are not permitted")

rule("Rate limit API calls")
.when(history.select("api_call").count(within="1h") > 100)
.block("API rate limit exceeded - maximum 100 calls per hour")
```

### Allow Actions

Allow actions immediately permit the tool call and skip evaluation of remaining rules:

```python
rule("Allow read-only operations")
.when(call.name.startswith("get_") | call.name.startswith("list_"))
.allow()  # No message needed, skips remaining rules

rule("Allow low-risk operations")
.when(call.name.startswith("get_") & call.arg("sensitive") != "true")
.allow()
```

## Custom Predicates

For complex logic that can't be expressed with built-in predicates, use custom functions.
Custom predicates must return boolean values and should handle edge cases gracefully:

```python
from tramlines.guardrail.dsl.predicates import custom
from tramlines.session import CallHistory, ToolCall

def single_user_predicate(current_call: ToolCall, session_history: CallHistory) -> bool:
    """Ensure operations are limited to a single user."""
    current_user = current_call.arguments.get("user_id")
    if not current_user:
        return False
    
    # Check if a different user was accessed previously
    for call in session_history.calls:
        previous_user = call.arguments.get("user_id")
        if previous_user and previous_user != current_user:
            return True  # Different user detected
    
    return False

# Use in a rule
rule("Enforce single user per session")
.when(custom(single_user_predicate))
.block("You may only operate on one user account per session")
```
