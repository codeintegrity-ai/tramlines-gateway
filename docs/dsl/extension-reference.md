# Extension Reference

Extensions in Tramlines provide reusable detection capabilities that can be integrated into your security policies. They are specialized functions that analyze text content and return boolean results indicating whether specific threats or patterns are detected.

## What are Extensions?

Extensions are Python functions that:

- **Analyze text content** for specific security threats or patterns
- **Return boolean values** (`True` if threat detected, `False` if safe)
- **Can be imported and used** in custom predicates within your rules

## Available Extensions

### 1. PII Detector (`detect_pii`)

Detects Personally Identifiable Information using Microsoft Presidio.

**Detects:**

- Email addresses
- Phone numbers
- Credit card numbers
- Social Security Numbers (SSN)
- Driver's license numbers
- IP addresses
- Names, locations, organizations
- Medical license numbers
- Cryptocurrency addresses

**Usage:**

```python
from tramlines.guardrail.extensions.pii_detector import detect_pii

# Basic usage
has_pii = detect_pii("My email is john@example.com")  # Returns True
```

### 2. Regex Detector (`detect_regex`)

Detects threats using LlamaFirewall's regex pattern matching.

**Detects:**

- Prompt injection attempts
- SQL injection patterns
- Known malicious strings
- Suspicious command patterns

**Usage:**

```python
from tramlines.guardrail.extensions.regex_detector import detect_regex

# Basic usage
has_threat = detect_regex("SELECT * FROM users")  # May return True
```

### 3. Prompt Detector (`detect_prompt`)

Detects prompt injection attacks using LlamaFirewall's PromptGuard.

**Detects:**

- Jailbreak attempts
- Prompt injection attacks
- Social engineering patterns

**Usage:**

```python
from tramlines.guardrail.extensions.prompt_detector import detect_prompt

# Basic usage
is_injection = detect_prompt("Ignore all previous instructions")  # Returns True
```

### 4. Encoding Detector (`detect_encoding`)

Detects suspicious encoding or obfuscation patterns.

**Detects:**

- Base64 encoded content
- Hex encoding sequences
- URL encoding
- Unicode escape sequences
- Excessive non-ASCII characters

**Usage:**

```python
from tramlines.guardrail.extensions.encoding_detector import detect_encoding

# Basic usage
is_encoded = detect_encoding("aGVsbG8gd29ybGQ=")  # Returns True for base64
```
