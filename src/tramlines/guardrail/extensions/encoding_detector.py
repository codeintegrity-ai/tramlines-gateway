"""
Encoding Detection Extension

Detects potentially encoded or obfuscated content that could be used to bypass security checks.
"""

import re


def detect_encoding(text: str) -> bool:
    """
    Detects suspicious encoding or obfuscation in text.

    Args:
        text: String to analyze for encoding patterns

    Returns:
        bool: True if encoding detected, False if safe
    """
    if not text or not text.strip():
        return False

    content = str(text).strip()

    # Check for base64 patterns - but be more specific
    # Must be longer and not contain common words/domains
    base64_pattern = r"[A-Za-z0-9+/]{16,}={0,2}"
    base64_matches = re.findall(base64_pattern, content)
    if base64_matches:
        # Filter out common false positives like domain names, URLs
        for match in base64_matches:
            # Skip if it looks like a domain or URL component
            if any(
                word in match.lower()
                for word in ["com", "org", "net", "example", "api", "http", "www"]
            ):
                continue
            # Skip short matches that might be legitimate tokens
            if len(match) < 20:
                continue
            return True

    # Check for hex encoding - require multiple consecutive hex sequences
    hex_patterns = [
        r"\\x[0-9A-Fa-f]{2}",  # \x hex escapes
        r"%[0-9A-Fa-f]{2}",  # URL-style hex
        r"&#x[0-9A-Fa-f]+;",  # HTML hex entities
    ]
    for pattern in hex_patterns:
        matches = re.findall(pattern, content)
        # Only flag if there are multiple consecutive hex sequences
        if len(matches) >= 3:
            return True

    # Check for excessive URL encoding (more than 8 encoded chars)
    url_encoded = re.findall(r"%[0-9A-Fa-f]{2}", content)
    if len(url_encoded) >= 8:
        return True

    # Check for unicode escape sequences (multiple required)
    unicode_matches = re.findall(r"\\u[0-9A-Fa-f]{4}", content)
    if len(unicode_matches) >= 3:
        return True

    # Check for excessive non-ASCII characters (but allow normal international text)
    non_ascii_count = sum(1 for char in content if ord(char) > 127)
    if len(content) > 20 and non_ascii_count / len(content) > 0.5:
        return True

    return False
