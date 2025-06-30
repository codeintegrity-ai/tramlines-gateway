from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path

from tramlines.guardrail.dsl.types import ActionType, Policy
from tramlines.logger import logger
from tramlines.session import CallHistory


@dataclass
class EvaluationResult:
    """Result of a guardrail policy evaluation for a single tool call."""

    action_type: ActionType
    violated_rule: str | None = None
    message: str | None = None

    @property
    def is_allowed(self) -> bool:
        """Check if the action is allowed."""
        return self.action_type == ActionType.ALLOW

    @property
    def is_blocked(self) -> bool:
        """Check if the action blocks the tool call."""
        return self.action_type == ActionType.BLOCK


def load_policy_from_file(policy_file: str) -> Policy:
    """
    Load a security policy from a Python file.

    The policy file should define a module-level variable named 'policy'
    that contains a Policy instance.

    Args:
        policy_file: Path to the Python policy file

    Returns:
        Policy: The loaded policy object

    Raises:
        FileNotFoundError: If the policy file doesn't exist
        ValueError: If the policy file doesn't contain a valid policy
        ImportError: If the policy file has import errors
    """
    policy_path = Path(policy_file)

    if not policy_path.exists():
        raise FileNotFoundError(f"Policy file not found: {policy_path}")

    if not policy_path.suffix == ".py":
        raise ValueError(f"Policy file must have .py extension: {policy_path}")

    # Generate a unique module name to avoid conflicts
    module_name = f"policy_module_{policy_path.stem}_{id(policy_path)}"

    try:
        # Load the module dynamically
        spec = importlib.util.spec_from_file_location(module_name, policy_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module spec from {policy_path}")

        module = importlib.util.module_from_spec(spec)

        # Add to sys.modules temporarily to support relative imports
        sys.modules[module_name] = module

        try:
            spec.loader.exec_module(module)
        finally:
            # Clean up sys.modules
            if module_name in sys.modules:
                del sys.modules[module_name]

        # Extract the policy object
        if not hasattr(module, "policy"):
            raise ValueError(
                f"Policy file {policy_path} must define a module-level variable named 'policy'"
            )

        policy = getattr(module, "policy")

        # Validate the policy object
        if not isinstance(policy, Policy):
            raise ValueError(
                f"The 'policy' variable in {policy_path} must be an instance of Policy, "
                f"got {type(policy)}"
            )

        logger.info(
            f"POLICY_LOAD | Successfully loaded policy '{policy.name}' "
            f"with {len(policy.rules)} rules from {policy_path}"
        )

        return policy

    except Exception as e:
        logger.error(
            f"POLICY_LOAD_ERROR | Failed to load policy from {policy_path}: {e}"
        )
        raise


def evaluate_call(policy: Policy, history: CallHistory) -> EvaluationResult:
    """Evaluates guardrail rules for a given tool call."""
    if not history:
        raise ValueError("Call history cannot be empty.")

    call = history[-1]

    for rule in policy.rules:
        try:
            if rule.condition(call, history):
                if rule.action_type == ActionType.BLOCK:
                    # Block actions are final
                    return EvaluationResult(
                        action_type=ActionType.BLOCK,
                        violated_rule=rule.name,
                        message=rule.message,
                    )
                elif rule.action_type == ActionType.ALLOW:
                    # Allow actions stop processing for this phase
                    return EvaluationResult(action_type=ActionType.ALLOW)

        except Exception as e:
            logger.error(f"GUARDRAIL_ERROR | Error evaluating rule '{rule.name}': {e}")
            # Decide on a default behavior for errors, e.g., fail-safe (block)
            # For now, we'll log and continue, which is fail-open
            continue

    # If no rule was triggered, default to allow
    return EvaluationResult(action_type=ActionType.ALLOW)
