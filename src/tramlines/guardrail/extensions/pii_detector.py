"""
PII Detection Extension

Uses Microsoft Presidio for detecting personally identifiable information (PII).
Provides comprehensive detection of emails, phone numbers, credit cards, SSNs, and more.
"""

# Global imports and instance creation for performance
try:
    from presidio_analyzer import AnalyzerEngine

    # Create global analyzer instance to avoid reloading models
    _analyzer: AnalyzerEngine | None = AnalyzerEngine()
except ImportError:
    # Handle missing presidio dependencies gracefully
    _analyzer = None
except Exception:
    # Handle any other initialization errors (e.g., missing spacy models)
    _analyzer = None


def detect_pii(text: str) -> bool:
    """
    Detects personally identifiable information in text.

    Args:
        text: String to analyze for PII

    Returns:
        bool: True if PII detected, False if safe
    """
    if not text or not text.strip():
        return False

    # Return False if analyzer couldn't be initialized
    if _analyzer is None:
        return False

    try:
        results = _analyzer.analyze(
            text=text,
            entities=[
                "PHONE_NUMBER",
                "EMAIL_ADDRESS",
                "CREDIT_CARD",
                "IBAN_CODE",
                "IP_ADDRESS",
                "PERSON",
                "LOCATION",
                "ORGANIZATION",
                "US_SSN",
                "US_DRIVER_LICENSE",
                "US_PASSPORT",
                "US_BANK_NUMBER",
                "DATE_TIME",
                "MEDICAL_LICENSE",
                "URL",
                "CRYPTO",
            ],
            language="en",
        )

        return len(results) > 0
    except Exception:
        return False
