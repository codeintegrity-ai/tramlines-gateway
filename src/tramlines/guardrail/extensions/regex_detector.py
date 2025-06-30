"""
Regex Threat Detection Extension

Uses LlamaFirewall's RegexScanner for pattern-based threat detection.
"""

import asyncio

# Global imports and instance creation for performance
try:
    from llamafirewall.llamafirewall_data_types import ScanDecision as LlamaDecision
    from llamafirewall.llamafirewall_data_types import UserMessage
    from llamafirewall.scanners.regex_scanner import RegexScanner

    # Create global scanner instance to avoid reloading models
    _scanner: RegexScanner | None = RegexScanner()
except ImportError:
    # Handle missing llamafirewall dependencies gracefully
    _scanner = None
except Exception:
    # Handle any other initialization errors (e.g., model loading issues)
    _scanner = None


def detect_regex(text: str) -> bool:
    """
    Detect potential regex-based threats in text using LlamaFirewall's RegexScanner.

    Args:
        text: The text to analyze

    Returns:
        True if potential threats are detected, False otherwise
    """
    if not text or not text.strip():
        return False

    if _scanner is None:
        # Gracefully handle missing dependencies
        return False

    try:
        # Create a user message and scan it using asyncio.run() as in official example
        message = UserMessage(text)
        result = asyncio.run(_scanner.scan(message))

        # Return True if scanner decided to block
        return bool(result.decision == LlamaDecision.BLOCK)
    except Exception:
        # Return False on any scanning errors to avoid blocking valid content
        return False
