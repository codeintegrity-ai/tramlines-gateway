# Tramlines Language Reference

Tramlines provides a declarative Domain-Specific Language (DSL) embedded within Python for creating flexible and powerful security policies that govern tool call behavior in AI agent sessions. The declarative approach allows developers to focus on defining what security conditions should be enforced rather than how to implement the enforcement logic, making policies more readable, maintainable, and expressive. This reference guide is organized into focused sections to help developers understand and implement effective security policies.

## Overview

The Tramlines DSL consists of four main components:

1. **[Policies](policy-reference.md)** - Collections of security rules that work together
2. **[Rules](rule-reference.md)** - Individual security constraints within policies
3. **[Extensions](extension-reference.md)** - Reusable functionality for complex security logic
4. **[Testing](testing-reference.md)** - Framework for validating policy behavior

## Quick Start Example

Here's a simple example showing how the components work together:

```python
from tramlines.guardrail.dsl.types import Policy
from tramlines.guardrail.dsl.rules import rule
from tramlines.guardrail.dsl.context import call

# Create a simple security policy
basic_security_policy = Policy(
    name="Basic Security Policy",
    description="Prevents dangerous operations and enforces resource constraints",
    rules=[
        # Rule 1: Block destructive operations
        rule("Block dangerous operations")
        .when(call.name.contains("delete", "destroy", "remove"))
        .block("Destructive operations are not allowed"),

        # Rule 2: Allow safe read operations
        rule("Allow safe operations")
        .when(call.name.startswith("get_") | call.name.startswith("list_"))
        .allow()
    ]
)
```
