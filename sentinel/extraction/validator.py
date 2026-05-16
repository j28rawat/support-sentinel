"""
sentinel/extraction/validator.py
==================================
Standalone validation utilities for structured outputs.

ADDITIVE MODULE:
    Day 3: Basic semantic validators
    Day 5+: Multi-field cross-validation added

EXAM CONCEPT — Syntax vs Semantic errors (Task Statement 4.4):

    Syntax errors   → eliminated by tool_use + JSON schema
                      Claude cannot return malformed JSON.
                      Cannot omit required fields.
                      Cannot use invalid enum values.

    Semantic errors → require code validation
                      Values in wrong fields.
                      Amounts that don't match context.
                      Contradictory data.
                      These require your validators.

EXAM CONCEPT — When retries work vs when they don't:

    Retries ARE effective for:
        Format errors: amount as "$299" instead of 299.0
        Structural errors: key_facts as string not array
        Enum errors: "URGENT" instead of "urgent"

    Retries are NOT effective for:
        Missing information: source document doesn't contain
        the data — retrying won't make it appear.
        Fundamental ambiguity: message has no clear issue type.

    Identifying this limit is tested in Task Statement 4.4.
"""


def validate_incident(data: dict) -> list[str]:
    """
    Validate extracted incident data semantically.

    Returns list of error strings. Empty list = valid.

    Use this for standalone validation outside IncidentExtractor.
    IncidentExtractor.validate() calls this internally.
    """
    errors = []

    # Amount must be positive
    amount = data.get("amount_mentioned")
    if amount is not None:
        if not isinstance(amount, (int, float)):
            errors.append(
                f"amount_mentioned must be a number, got "
                f"{type(amount).__name__}: {amount}"
            )
        elif amount <= 0:
            errors.append(
                f"amount_mentioned must be positive, got {amount}"
            )

    # key_facts must be non-empty list of strings
    facts = data.get("key_facts")
    if facts is not None:
        if not isinstance(facts, list):
            errors.append(
                f"key_facts must be a list, got "
                f"{type(facts).__name__}"
            )
        elif len(facts) == 0:
            errors.append("key_facts must not be empty")
        elif not all(isinstance(f, str) for f in facts):
            errors.append(
                "All items in key_facts must be strings"
            )

    # issue_type_detail required when issue_type is "other"
    if data.get("issue_type") == "other":
        if not data.get("issue_type_detail"):
            errors.append(
                "issue_type_detail required when "
                "issue_type is 'other'"
            )

    # urgency must be a known value
    urgency = data.get("urgency")
    valid_urgencies = {"urgent", "high", "normal", "low"}
    if urgency and urgency not in valid_urgencies:
        errors.append(
            f"urgency '{urgency}' is not valid. "
            f"Must be one of: {valid_urgencies}"
        )

    return errors


def is_retry_worthwhile(errors: list[str]) -> bool:
    """
    Determine whether retrying will likely fix the errors.

    Returns True if errors are format/structural issues
    that a retry with feedback can fix.

    Returns False if errors suggest missing data that
    no amount of retrying will resolve.

    EXAM NOTE:
        This function embodies Task Statement 4.4:
        "Retries are ineffective when the required information
        is simply absent from the source document."
    """
    # These error patterns suggest format issues — retryable
    retryable_patterns = [
        "must be a number",
        "must be positive",
        "must be a list",
        "must not be empty",
        "is not valid",
        "required when",
    ]

    # These patterns suggest missing data — not retryable
    non_retryable_patterns = [
        "not found in message",
        "not mentioned",
        "absent from source",
    ]

    for error in errors:
        error_lower = error.lower()
        for pattern in non_retryable_patterns:
            if pattern in error_lower:
                return False

    for error in errors:
        error_lower = error.lower()
        for pattern in retryable_patterns:
            if pattern in error_lower:
                return True

    # Default: attempt retry for unknown error types
    return True


def format_validation_report(
    data: dict,
    errors: list[str]
) -> str:
    """
    Format a validation report for logging and debugging.
    """
    if not errors:
        return f"✓ Validation passed — {len(data)} fields extracted"

    report = [
        f"✗ Validation failed — {len(errors)} error(s):",
    ]
    for i, error in enumerate(errors, 1):
        report.append(f"  {i}. {error}")

    return "\n".join(report)