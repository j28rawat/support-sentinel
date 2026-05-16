"""
tests/test_day_03.py
======================
Tests for Day 3 components.

Run: pytest tests/test_day_03.py -v

All tests run without API calls except TestIncidentExtractorIntegration
which is marked with a comment — skip if you want zero API usage.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
))

from sentinel.extraction.schemas import INCIDENT_SCHEMA
from sentinel.extraction.validator import (
    validate_incident,
    is_retry_worthwhile,
    format_validation_report,
)
from sentinel.extraction.incident_extractor import ExtractionResult


class TestIncidentSchema:
    """Verify schema structure is correct before any API calls."""

    def test_schema_has_required_name(self):
        assert INCIDENT_SCHEMA["name"] == "extract_incident"

    def test_schema_has_input_schema(self):
        assert "input_schema" in INCIDENT_SCHEMA

    def test_required_fields_present(self):
        required = INCIDENT_SCHEMA["input_schema"]["required"]
        assert "issue_type" in required
        assert "urgency" in required
        assert "sentiment" in required
        assert "key_facts" in required
        assert "extraction_confidence" in required

    def test_nullable_fields_allow_null(self):
        props = INCIDENT_SCHEMA["input_schema"]["properties"]
        nullable_fields = [
            "customer_id", "order_id",
            "customer_name", "amount_mentioned",
        ]
        for field in nullable_fields:
            field_type = props[field]["type"]
            assert "null" in field_type, (
                f"Field '{field}' should allow null "
                f"to prevent hallucination"
            )

    def test_issue_type_enum_values(self):
        props = INCIDENT_SCHEMA["input_schema"]["properties"]
        enum = props["issue_type"]["enum"]
        assert "refund_request" in enum
        assert "return_request" in enum
        assert "missing_package" in enum
        assert "other" in enum

    def test_urgency_enum_values(self):
        props = INCIDENT_SCHEMA["input_schema"]["properties"]
        enum = props["urgency"]["enum"]
        assert set(enum) == {"urgent", "high", "normal", "low"}


class TestValidator:
    """Unit tests for semantic validation — no API calls."""

    def test_valid_data_passes(self):
        data = {
            "customer_id": "C001",
            "order_id": "ORD-10045",
            "issue_type": "refund_request",
            "urgency": "normal",
            "sentiment": "negative",
            "key_facts": ["wants refund", "order delivered"],
            "extraction_confidence": "high",
            "amount_mentioned": 299.99,
        }
        errors = validate_incident(data)
        assert errors == []

    def test_negative_amount_fails(self):
        data = {
            "issue_type": "refund_request",
            "urgency": "normal",
            "sentiment": "negative",
            "key_facts": ["test"],
            "extraction_confidence": "high",
            "amount_mentioned": -50.0,
        }
        errors = validate_incident(data)
        assert any("positive" in e for e in errors)

    def test_empty_key_facts_fails(self):
        data = {
            "issue_type": "refund_request",
            "urgency": "normal",
            "sentiment": "negative",
            "key_facts": [],
            "extraction_confidence": "high",
        }
        errors = validate_incident(data)
        assert any("key_facts" in e for e in errors)

    def test_other_issue_type_requires_detail(self):
        data = {
            "issue_type": "other",
            "issue_type_detail": None,
            "urgency": "normal",
            "sentiment": "neutral",
            "key_facts": ["unusual request"],
            "extraction_confidence": "medium",
        }
        errors = validate_incident(data)
        assert any("issue_type_detail" in e for e in errors)

    def test_other_issue_type_with_detail_passes(self):
        data = {
            "issue_type": "other",
            "issue_type_detail": "Customer requesting gift wrapping",
            "urgency": "low",
            "sentiment": "positive",
            "key_facts": ["gift wrapping request"],
            "extraction_confidence": "high",
        }
        errors = validate_incident(data)
        assert errors == []

    def test_null_amount_is_valid(self):
        """Null amount is valid — field is optional."""
        data = {
            "issue_type": "return_request",
            "urgency": "normal",
            "sentiment": "neutral",
            "key_facts": ["wants to return"],
            "extraction_confidence": "high",
            "amount_mentioned": None,
        }
        errors = validate_incident(data)
        assert errors == []

    def test_non_string_in_key_facts_fails(self):
        data = {
            "issue_type": "refund_request",
            "urgency": "normal",
            "sentiment": "negative",
            "key_facts": ["valid fact", 42, None],
            "extraction_confidence": "medium",
        }
        errors = validate_incident(data)
        assert any("string" in e for e in errors)


class TestRetryWorthwhile:
    """Test retry decision logic."""

    def test_format_error_is_retryable(self):
        errors = ["amount_mentioned must be a number, got str: $299"]
        assert is_retry_worthwhile(errors) is True

    def test_empty_list_error_is_retryable(self):
        errors = ["key_facts must not be empty"]
        assert is_retry_worthwhile(errors) is True

    def test_missing_data_is_not_retryable(self):
        errors = ["customer_id not found in message"]
        assert is_retry_worthwhile(errors) is False

    def test_empty_error_list_defaults_to_retryable(self):
        assert is_retry_worthwhile([]) is True


class TestExtractionResult:
    """Test ExtractionResult dataclass."""

    def test_successful_result(self):
        result = ExtractionResult(
            data={"issue_type": "refund_request"},
            confidence="high",
            retries=0,
            success=True,
        )
        assert result.success is True
        assert result.retries == 0
        assert result.error is None

    def test_failed_result_has_error(self):
        result = ExtractionResult(
            data={},
            confidence="low",
            retries=2,
            success=False,
            error="Validation failed after 2 retries",
        )
        assert result.success is False
        assert result.error is not None

    def test_to_dict_includes_all_fields(self):
        result = ExtractionResult(
            data={"issue_type": "refund_request"},
            confidence="high",
            retries=0,
            success=True,
        )
        d = result.to_dict()
        assert "data" in d
        assert "confidence" in d
        assert "retries" in d
        assert "success" in d
        assert "error" in d


class TestFormatValidationReport:
    def test_valid_data_shows_passed(self):
        report = format_validation_report(
            {"a": 1, "b": 2}, []
        )
        assert "passed" in report.lower()

    def test_errors_shown_in_report(self):
        report = format_validation_report(
            {}, ["Error one", "Error two"]
        )
        assert "Error one" in report
        assert "Error two" in report
        assert "2" in report


class TestDay01Day02StillWork:
    """Versioning contract — prior days unaffected."""

    def test_day_01_tools_still_importable(self):
        from sentinel.tools.day_01 import (
            ALL_TOOL_DEFINITIONS,
            execute_tool,
        )
        assert len(ALL_TOOL_DEFINITIONS) == 5

    def test_day_02_tools_still_importable(self):
        from sentinel.tools.day_02 import (
            ALL_TOOL_DEFINITIONS,
            execute_tool,
        )
        assert len(ALL_TOOL_DEFINITIONS) == 9

    def test_day_03_tools_have_more_than_day_02(self):
        from sentinel.tools.day_03 import ALL_TOOL_DEFINITIONS
        assert len(ALL_TOOL_DEFINITIONS) == 10