"""
sentinel/extraction/incident_extractor.py
============================================
Structured incident extraction from raw customer messages.

ADDITIVE MODULE:
    Day 3: IncidentExtractor class
    Day 5+: May add context-aware extraction methods

EXAM CRITICAL — Task Statement 4.3:

    The core pattern:
    1. Define extraction tool with JSON schema
    2. Set tool_choice to FORCE the specific tool
    3. Claude MUST call it — cannot return plain text
    4. Extract result from tool_use block in response
    5. Validate semantically (schema guarantees syntax only)
    6. Retry with error feedback if validation fails

    tool_choice = {"type": "tool", "name": "extract_incident"}
    This is FORCED selection — not "any", not "auto".
    Claude has no choice but to call this exact tool.

EXAM CONCEPT — Few-shot examples (Task Statement 4.2):
    Few-shot examples are the MOST effective technique for
    achieving consistently formatted output when instructions
    alone produce variance.

    We inject DAY_03_FEW_SHOT_EXAMPLES into the extraction
    prompt to demonstrate:
    - Exact output format for each field
    - How to handle missing data (null, not guessed)
    - How to classify edge cases (urgency, sentiment)
    - How to populate key_facts concisely

EXAM CONCEPT — Retry with error feedback (Task Statement 4.4):
    When validation fails, we don't just retry blindly.
    We append the specific validation error to the prompt
    so Claude understands what to fix.

    Blind retry: "Try again"
    Feedback retry: "The amount_mentioned field contains a
    string '$299.99' but must be a number. Extract as 299.99"

    Feedback retries are effective for FORMAT errors.
    They are NOT effective when the information simply
    doesn't exist in the source document.
"""

import json
from sentinel.core.claude_client import create_message
from sentinel.extraction.schemas import INCIDENT_SCHEMA
from sentinel.config.prompts import (
    DAY_03_EXTRACTION_AGENT,
    DAY_03_FEW_SHOT_EXAMPLES,
)


class IncidentExtractor:
    """
    Extracts structured incident data from raw customer messages.

    Usage:
        extractor = IncidentExtractor()
        result = extractor.extract("I'm C001 and I want a refund...")
        print(result.data)        # extracted dict
        print(result.confidence)  # high/medium/low
        print(result.retries)     # how many retries needed
    """

    def __init__(self, use_few_shot: bool = True) -> None:
        """
        Args:
            use_few_shot: Whether to include few-shot examples.
                          Set False to demonstrate variance without them.
                          Default True — always use in production.
        """
        self.use_few_shot = use_few_shot

    def extract(
        self,
        customer_message: str,
        max_retries: int = 2,
    ) -> "ExtractionResult":
        """
        Extract structured incident data from a customer message.

        Args:
            customer_message: Raw text from customer
            max_retries:      Max retry attempts on validation failure

        Returns:
            ExtractionResult with extracted data, confidence,
            and retry count.

        EXAM NOTE — Why max_retries=2 not higher?
            Retries are effective for FORMAT errors (wrong type,
            wrong enum value). They are NOT effective when the
            information is genuinely absent from the source.
            After 2 retries, if still failing, the issue is
            likely absent data — not a format problem.
            Identify the limit of retry effectiveness.
        """
        prompt = self._build_prompt(customer_message)
        last_error = None

        for attempt in range(max_retries + 1):
            # On retry: append the specific error to the prompt
            if attempt > 0 and last_error:
                prompt = self._build_retry_prompt(
                    customer_message,
                    last_error,
                    attempt,
                )

            response = create_message(
                messages=[{"role": "user", "content": prompt}],
                tools=[INCIDENT_SCHEMA],
                system=DAY_03_EXTRACTION_AGENT,
                # FORCED TOOL SELECTION — exam critical
                # Claude MUST call extract_incident
                # Cannot return plain text
                # Cannot call a different tool
                tool_choice={
                    "type": "tool",
                    "name": "extract_incident",
                },
            )

            # Extract data from tool_use block
            extracted = self._parse_tool_response(response)

            if extracted is None:
                last_error = "No tool_use block found in response"
                continue

            # Semantic validation
            validation_error = self._validate(extracted)

            if validation_error is None:
                # Success
                return ExtractionResult(
                    data=extracted,
                    confidence=extracted.get(
                        "extraction_confidence", "medium"
                    ),
                    retries=attempt,
                    success=True,
                )

            last_error = validation_error

        # All retries exhausted
        return ExtractionResult(
            data=extracted if extracted else {},
            confidence="low",
            retries=max_retries,
            success=False,
            error=last_error,
        )

    def _build_prompt(self, message: str) -> str:
        """
        Build the extraction prompt with optional few-shot examples.

        EXAM NOTE — Few-shot placement:
            Examples come BEFORE the target message.
            This is the standard few-shot pattern.
            Claude reads examples first, then applies the
            demonstrated pattern to the new input.
        """
        parts = []

        if self.use_few_shot:
            parts.append(
                "Here are examples of correct extractions:\n"
                + DAY_03_FEW_SHOT_EXAMPLES
            )

        parts.append(
            f"Now extract structured data from this customer message:"
            f"\n\n\"{message}\""
        )

        return "\n\n".join(parts)

    def _build_retry_prompt(
        self,
        message: str,
        error: str,
        attempt: int,
    ) -> str:
        """
        Build retry prompt with specific error feedback.

        EXAM NOTE — Retry with error feedback (Task Statement 4.4):
            We include:
            1. The original message (Claude needs context)
            2. The specific validation error (what to fix)
            3. Instructions to correct that specific issue

            This is MORE effective than just retrying the same prompt.
            Claude knows exactly what went wrong and can correct it.

            Blind retry → same error likely repeats
            Feedback retry → Claude corrects the specific issue
        """
        parts = []

        if self.use_few_shot:
            parts.append(
                "Here are examples of correct extractions:\n"
                + DAY_03_FEW_SHOT_EXAMPLES
            )

        parts.append(
            f"Extract structured data from this customer message:"
            f"\n\n\"{message}\""
            f"\n\nATTEMPT {attempt + 1} — Previous extraction had "
            f"this validation error:\n"
            f"ERROR: {error}\n\n"
            f"Please correct this specific issue in your extraction."
        )

        return "\n\n".join(parts)

    def _parse_tool_response(
        self,
        response
    ) -> dict | None:
        """
        Extract the tool_use block data from Claude's response.

        EXAM NOTE:
            When tool_choice forces a specific tool, the response
            will contain a tool_use block with the schema data
            in the `input` field.

            response.content is a list of blocks.
            We find the tool_use block and return its input.
        """
        for block in response.content:
            if block.type == "tool_use":
                return block.input
        return None

    def _validate(self, data: dict) -> str | None:
        """
        Semantic validation of extracted data.

        Returns None if valid, error string if invalid.

        EXAM NOTE — What tool_use validates vs what we validate:
            tool_use guarantees:  JSON syntax, required fields present,
                                  enum values from allowed list,
                                  correct types (string, number, etc.)

            We must validate:     Semantic correctness
                                  - amount_mentioned is positive
                                  - key_facts is not empty
                                  - issue_type_detail present when
                                    issue_type is "other"
                                  - No contradictory data
        """

        # Validate amount is positive if present
        amount = data.get("amount_mentioned")
        if amount is not None and amount <= 0:
            return (
                f"amount_mentioned must be a positive number. "
                f"Got: {amount}. If no amount was mentioned, "
                f"return null instead."
            )

        # Validate key_facts is not empty
        facts = data.get("key_facts", [])
        if not facts:
            return (
                "key_facts must contain at least 1 fact. "
                "Extract the most important point from the message."
            )

        # Validate issue_type_detail when issue_type is "other"
        if (
            data.get("issue_type") == "other"
            and not data.get("issue_type_detail")
        ):
            return (
                "When issue_type is 'other', issue_type_detail "
                "must be populated with a description of the issue. "
                "Do not leave it null."
            )

        # Validate key_facts are strings, not nested objects
        if not all(isinstance(f, str) for f in facts):
            return (
                "Each item in key_facts must be a plain string. "
                "Found non-string items. Convert all facts to "
                "short descriptive phrases."
            )

        return None  # Valid


class ExtractionResult:
    """
    Result of an extraction attempt.

    Attributes:
        data:       Extracted dict (may be partial on failure)
        confidence: high/medium/low from schema field
        retries:    Number of retry attempts made (0 = first try)
        success:    Whether extraction passed validation
        error:      Last validation error if success=False
    """

    def __init__(
        self,
        data: dict,
        confidence: str,
        retries: int,
        success: bool,
        error: str | None = None,
    ) -> None:
        self.data = data
        self.confidence = confidence
        self.retries = retries
        self.success = success
        self.error = error

    def to_dict(self) -> dict:
        return {
            "data": self.data,
            "confidence": self.confidence,
            "retries": self.retries,
            "success": self.success,
            "error": self.error,
        }

    def __repr__(self) -> str:
        return (
            f"ExtractionResult("
            f"success={self.success}, "
            f"confidence={self.confidence}, "
            f"retries={self.retries})"
        )