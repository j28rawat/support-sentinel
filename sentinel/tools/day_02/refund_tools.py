"""
sentinel/tools/day_02/refund_tools.py
========================================
Refund eligibility and processing tools.

FROZEN: Do not modify after Day 2 is complete.

PREREQUISITE CHAIN — enforced today via descriptions,
                     enforced Day 7 via programmatic hooks:

    get_customer              ← must run first (identity)
         ↓
    check_refund_eligibility  ← must run second (policy check)
         ↓
    process_refund            ← only if eligible + verified

TODAY (Day 2): Description-based enforcement (probabilistic)
    The descriptions say PREREQUISITES clearly.
    Claude usually follows this. Not guaranteed.

DAY 7: Programmatic enforcement (deterministic)
    A hook blocks process_refund if prerequisites not met.
    100% reliable. No exceptions.

EXAM CONCEPT — Task Statement 1.4:
    For financial operations, prompt instructions have a
    non-zero failure rate. Programmatic enforcement is required
    for deterministic compliance. We experience the probabilistic
    version today so Day 7's fix is meaningful.
"""

import random
import string

from sentinel.config.settings import settings
from sentinel.config.data_loader import MockDataLoader
from sentinel.tools.day_02.error_schemas import (
    not_found_error,
    business_rule_error,
)


def _get_loader() -> MockDataLoader:
    return MockDataLoader()


def _generate_txn_id() -> str:
    suffix = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=8)
    )
    return f"TXN-{suffix}"


def check_refund_eligibility(order_id: str) -> dict:
    """
    Determine whether an order qualifies for a refund.

    WHEN TO USE:
        Before processing any refund request — without exception.
        Use this to understand eligibility AND explain it to the
        customer before taking action.

    WHEN NOT TO USE:
        After already confirming eligibility in this conversation.
        Do not call this twice for the same order in one session.

    RETURNS:
        eligible=true:  refund_amount, payment_method,
                        processing_days, return_window_remaining_days
        eligible=false: reason explaining why not eligible

    COMMON INELIGIBILITY REASONS:
        Order not yet delivered (status is not 'delivered')
        Return window has expired (typically 30 days)

    ERRORS:
        validation — order ID not found. Do not retry.
    """
    loader = _get_loader()
    order = loader.get_order_by_id(order_id)

    if not order:
        return not_found_error("order", order_id)

    # Check 1: Must be delivered
    if order["status"] != "delivered":
        return {
            "error": False,
            "eligible": False,
            "order_id": order_id,
            "reason": (
                f"Order cannot be refunded — current status is "
                f"'{order['status']}'. Refunds are only available "
                f"for delivered orders."
            ),
        }

    # Check 2: Return window
    # days_since_delivery pre-computed by MockDataLoader
    days_since = order["days_since_delivery"]
    window = order["return_window_days"]
    within_window = order["within_return_window"]

    if not within_window:
        return {
            "error": False,
            "eligible": False,
            "order_id": order_id,
            "reason": (
                f"Return window of {window} days has expired. "
                f"Order was delivered {days_since} days ago."
            ),
        }

    # Eligible — compute refund details
    policies = loader.get_policies()
    payment = order["payment_method"]
    processing_days = (
        policies["refund_policy"]["processing_days_credit_card"]
        if payment == "credit_card"
        else policies["refund_policy"]["processing_days_paypal"]
    )

    return {
        "error": False,
        "eligible": True,
        "order_id": order_id,
        "refund_amount": order["total_amount"],
        "payment_method": payment,
        "processing_days": processing_days,
        "days_since_delivery": days_since,
        "return_window_remaining_days": window - days_since,
        "reason": (
            f"Order is within the {window}-day return window "
            f"({days_since} days since delivery). "
            f"Refund of ${order['total_amount']:.2f} is available."
        ),
    }


def process_refund(order_id: str, amount: float) -> dict:
    """
    Execute a refund for a confirmed-eligible order.

    PREREQUISITES — MUST complete both before calling this:
        1. get_customer — verified customer identity this session
        2. check_refund_eligibility — returned eligible=true

    WHEN TO USE:
        Only after both prerequisites are confirmed in this session.

    WHEN NOT TO USE:
        Amount exceeds $500 — use escalate_to_human instead.
        Eligibility not yet confirmed — run check_refund_eligibility.

    RETURNS:
        transaction_id, amount_refunded, processing timeline.

    ERRORS:
        business — amount exceeds $500 auto-approval limit.
                   requires_escalation=true — hand off to human.
        validation — order not found.
    """
    # Business rule: hard limit
    if amount > settings.refund_approval_limit:
        return business_rule_error(
            rule=f"refund_auto_approval_limit_"
                 f"{settings.refund_approval_limit}",
            explanation=(
                f"Refunds over ${settings.refund_approval_limit:.2f} "
                f"require manager approval. I'll connect you with "
                f"a team member who can authorise this refund "
                f"of ${amount:.2f}."
            ),
            requires_escalation=True,
        )

    loader = _get_loader()
    order = loader.get_order_by_id(order_id)

    if not order:
        return not_found_error("order", order_id)

    txn_id = _generate_txn_id()

    return {
        "error": False,
        "success": True,
        "transaction_id": txn_id,
        "order_id": order_id,
        "amount_refunded": amount,
        "payment_method": order["payment_method"],
        "message": (
            f"Refund of ${amount:.2f} successfully processed. "
            f"Transaction ID: {txn_id}. "
            f"Funds will appear within 3-5 business days."
        ),
    }