"""
sentinel/extraction/__init__.py
=================================
Structured output extraction pipeline.

Built Day 3. Additive — new extractors appended.

Usage:
    from sentinel.extraction import IncidentExtractor

    extractor = IncidentExtractor()
    result = extractor.extract("I'm C001 and want a refund...")
    print(result.data)
"""

from sentinel.extraction.incident_extractor import (
    IncidentExtractor,
    ExtractionResult,
)
from sentinel.extraction.validator import (
    validate_incident,
    is_retry_worthwhile,
    format_validation_report,
)

__all__ = [
    "IncidentExtractor",
    "ExtractionResult",
    "validate_incident",
    "is_retry_worthwhile",
    "format_validation_report",
]