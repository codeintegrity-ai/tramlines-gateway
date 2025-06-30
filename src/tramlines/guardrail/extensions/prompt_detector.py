"""
Prompt Injection Detection Extension

Uses LlamaFirewall's PromptGuard for detecting jailbreak attempts and prompt injections.
"""

# Global imports and instance creation for performance
try:
    from llamafirewall import LlamaFirewall, Role, ScannerType, UserMessage
    from llamafirewall.llamafirewall_data_types import ScanDecision as LlamaDecision

    # Create global firewall instance to avoid reloading models
    _firewall: LlamaFirewall | None = LlamaFirewall(
        scanners={
            Role.USER: [ScannerType.PROMPT_GUARD],
        }
    )
except ImportError:
    # Handle missing llamafirewall dependencies gracefully
    _firewall = None
except Exception:
    # Handle any other initialization errors (e.g., model loading issues)
    _firewall = None


def detect_prompt(text: str) -> bool:
    """
    Detects prompt injection attacks in text.

    Args:
        text: String to analyze for prompt injection

    Returns:
        bool: True if prompt injection detected, False if safe
    """
    if not text or not text.strip():
        return False

    # Return False if firewall couldn't be initialized
    if _firewall is None:
        return False

    try:
        message = UserMessage(content=text)
        result = _firewall.scan(message)

        return result.decision == LlamaDecision.BLOCK  # type: ignore[no-any-return]

    except Exception:
        return False
