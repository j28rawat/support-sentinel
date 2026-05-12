"""
sentinel/tools/day_02/error_schemas.py
========================================
Structured error system for all Day 2+ tools.

FROZEN: Do not modify after Day 2 is complete.

EXAM CRITICAL — Task Statement 2.2:
    When a tool fails, Claude needs to make a decision:
      - Should I retry?           → transient error
      - Should I fix the input?   → validation error
      - Should I explain policy?  → business error
      - Should I escalate?        → permission error

    Generic errors ("Operation failed") give Claude ZERO
    information. It will retry forever, hallucinate, or
    give up — all bad outcomes.

    Structured errors with errorCategory + isRetryable
    give Claude exactly what it needs to recover.

THE FOUR ERROR CATEGORIES:

    transient   Service temporarily unavailable, timeout.
                Claude SHOULD retry after a brief wait.
                is_retryable: True

    validation  Invalid input, resource not found.
                Claude should NOT retry — fix the input.
                is_retryable: False

    business    Policy violation, limit exceeded.
                Claude should NOT retry — explain to customer.
                is_retryable: False

    permission  Insufficient access rights.
                Claude should NOT retry — escalate to human.
                is_retryable: False
                requires_escalation: True

EXAM TRAP — Empty result vs access failure:
    No orders found → error: False, orders: []
    Database timeout → error: True, category: transient
    These are DIFFERENT. The first is a valid empty result.
    The second is a failure needing retry.
    Marking empty results as errors causes unnecessary retries.
"""

from dataclasses import dataclass
from typing import Literal

ErrorCategory = Literal[
    "transient",
    "validation",
    "business",
    "permission",
]


@dataclass
class StructuredError:
    """
    Standardised error returned by all SupportSentinel tools.

    Claude reads this and makes intelligent recovery decisions
    based on error_category and is_retryable.
    """
    error: bool
    error_category: ErrorCategory
    is_retryable: bool
    message: str
    technical_detail: str = ""
    requires_escalation: bool = False

    def to_dict(self) -> dict:
        return {
            "error": self.error,
            "error_category": self.error_category,
            "is_retryable": self.is_retryable,
            "message": self.message,
            "technical_detail": self.technical_detail,
            "requires_escalation": self.requires_escalation,
        }


# ── Pre-built constructors ────────────────────────────────────────────────────
# Use these in every tool function for consistency.
# Never return raw {"error": True, "message": "..."} dicts.

def not_found_error(resource: str, identifier: str) -> dict:
    """
    Resource genuinely does not exist.

    EXAM NOTE: This is VALIDATION — not transient.
    The record will not appear on retry.
    Do NOT mark this is_retryable=True.

    Contrast with service_unavailable_error where the record
    MAY exist but the service is down.
    """
    return StructuredError(
        error=True,
        error_category="validation",
        is_retryable=False,
        message=f"No {resource} found with identifier: {identifier}",
        technical_detail=(
            f"DB lookup returned 0 results for {identifier}"
        ),
    ).to_dict()


def service_unavailable_error(
    service: str,
    operation: str
) -> dict:
    """
    Downstream service is temporarily unreachable.

    EXAM NOTE: This IS retryable — the service may recover.
    Claude should wait briefly and try the same call again.
    """
    return StructuredError(
        error=True,
        error_category="transient",
        is_retryable=True,
        message=(
            f"The {service} service is temporarily unavailable. "
            f"Please try again in a moment."
        ),
        technical_detail=(
            f"Service {service} failed during {operation}"
        ),
    ).to_dict()


def business_rule_error(
    rule: str,
    explanation: str,
    requires_escalation: bool = False,
) -> dict:
    """
    A business policy prevents the operation.

    EXAM NOTE: NOT retryable — the policy will not change
    between retries. Claude should explain to the customer,
    not retry.

    If requires_escalation=True, Claude should call
    escalate_to_human as the next step.
    """
    return StructuredError(
        error=True,
        error_category="business",
        is_retryable=False,
        message=explanation,
        technical_detail=f"Business rule violated: {rule}",
        requires_escalation=requires_escalation,
    ).to_dict()


def permission_error(action: str, reason: str) -> dict:
    """
    The agent lacks permission to perform this action.

    EXAM NOTE: NOT retryable. Always requires escalation.
    Permission won't change between retries.
    """
    return StructuredError(
        error=True,
        error_category="permission",
        is_retryable=False,
        message=(
            "This action requires additional authorisation. "
            "A team member will assist you shortly."
        ),
        technical_detail=f"Permission denied for {action}: {reason}",
        requires_escalation=True,
    ).to_dict()