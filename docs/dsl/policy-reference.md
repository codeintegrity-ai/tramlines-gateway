# Policy Reference

A **Policy** is the foundational concept in Tramlines - it's a collection of security rules that work together to enforce constraints on AI agent tool calls. Policies are evaluated against each tool call in a session, processing rules in sequence until a decision is made.

## Policy Structure

```python
from tramlines.guardrail.dsl.types import Policy
from tramlines.guardrail.dsl.rules import rule
from tramlines.guardrail.dsl.context import call

# Create a comprehensive security policy
my_security_policy = Policy(
    name="GitHub Security Policy",
    description="Prevents cross-repository operations and dangerous commands",
    rules=[
        rule("Block cross-repository access")
        .when(custom(single_repo_predicate))
        .block("You may only access one repository per session"),
        
        rule("Block destructive operations")
        .when(call.name.contains("delete", "destroy", "remove"))
        .block("Destructive operations are not allowed"),
        
        rule("Allow read-only operations")
        .when(call.name.startswith("get_") | call.name.startswith("list_"))
        .allow()  # Terminates evaluation early
    ]
)
```

## Policy Components

Policies have three main components:

- **Name**: A unique identifier for the policy
- **Description**: Optional human-readable explanation of the policy's purpose  
- **Rules**: An ordered list of security rules that are evaluated sequentially

### Name
The policy name serves as a unique identifier and should be descriptive of the policy's purpose:

```python
Policy(
    name="GitHub: Enforce Single Repository Per Session",
    # ...
)
```

### Description
An optional but recommended field that explains the policy's security purpose:

```python
Policy(
    name="Multi-Stage Security Validation",
    description="Layered security with PII detection, rate limiting, and resource constraints",
    # ...
)
```

### Rules
An ordered list of rules that define the security constraints. Rules are evaluated in sequence:

```python
Policy(
    name="Comprehensive Security Policy",
    rules=[
        # PII detection rules first (highest priority)
        rule("Block PII in arguments").when(...).block(...),
        
        # Rate limiting rules
        rule("Rate limit operations").when(...).block(...),
        
        # Catch-all blocks at the end
        rule("Block dangerous operations").when(...).block(...)
    ]
)
```

## Policy Evaluation Flow

When a tool call is made, the policy evaluation follows this sequence:

1. **Sequential Processing**: Rules are evaluated in the order they appear in the policy
2. **Early Termination**: If a rule triggers an `ALLOW` action, evaluation stops and remaining rules are skipped
3. **Blocking**: If a rule triggers a `BLOCK` action, the tool call is immediately blocked with the rule's message
4. **Default Allow**: If no rules trigger, the tool call is allowed by default

### Evaluation Example

```python
policy = Policy(
    name="Example Policy",
    rules=[
        rule("PII detection check")
        .when(custom(contains_pii_predicate))
        .block("PII detected in tool arguments"),
        
        rule("Allow read operations")  
        .when(call.name.startswith("get_") | call.name.startswith("list_"))
        .allow(),  # Stops here if matched
        
        rule("Block writes")
        .when(call.name.startswith("create_") | call.name.startswith("update_"))
        .block("Write operations not allowed")
    ]
)

# Tool call: "get_user" with no PII
# 1. PII detection check: false (no PII found)
# 2. Allow read operations: true -> ALLOW (evaluation stops)
# 3. Block writes: never evaluated

# Tool call: "create_user" with PII in arguments
# 1. PII detection check: true -> BLOCK (evaluation stops)
# 2. Allow read operations: never evaluated
# 3. Block writes: never evaluated
```

## Best Practices

### Rule Ordering
Order rules by priority and performance considerations:

1. **Critical checks** - Most critical security checks
2. **Rate limiting** - Prevent abuse early  
3. **Early allows** - Skip expensive checks for safe operations
4. **Specific blocks** - Targeted security rules
5. **General blocks** - Catch-all rules

```python
Policy(
    name="Well-Ordered Policy",
    rules=[
        # 1. Critical security first
        rule("Block PII in arguments").when(...).block(...),
        
        # 2. Rate limiting
        rule("Rate limit").when(...).block(...),
        
        # 3. Performance optimization
        rule("Allow safe reads").when(call.name.startswith("get_")).allow(),
        
        # 4. Specific security rules
        rule("Block cross-repo").when(...).block(...),
        
        # 5. General blocks
        rule("Block destructive").when(call.name.contains("delete")).block(...)
    ]
)
```

### Policy Composition
For complex security requirements, consider breaking policies into focused, composable units:

```python
# PII detection policy
pii_policy = Policy(
    name="PII Protection",
    rules=[
        rule("Block PII in arguments").when(...).block(...),
        rule("Block encoding attempts").when(...).block(...)
    ]
)

# Rate limiting policy  
rate_limit_policy = Policy(
    name="Rate Limiting",
    rules=[
        rule("Limit expensive ops").when(...).block(...),
        rule("Limit API calls").when(...).block(...)
    ]
)

# Resource constraints policy
resource_policy = Policy(
    name="Resource Constraints", 
    rules=[
        rule("Single repo per session").when(...).block(...),
        rule("Single user per session").when(...).block(...)
    ]
)
```
