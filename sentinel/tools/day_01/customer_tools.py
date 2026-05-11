"""
sentinel/tools/day_01/customer_tools.py
=========================================
Day 1 tool implementations — customer lookup and refund operations.

FROZEN: This file is not modified after Day 1 is complete.
        Day 2 creates sentinel/tools/day_02/ with upgraded versions.

CHANGE FROM INITIAL VERSION:
    Date loading now uses MockDataLoader (sentinel/config/data_loader.py)
    instead of raw JSON with absolute dates.
    This ensures all scenarios behave correctly regardless of
    when the code is run.

    This is NOT a breaking change — tool function signatures
    and return shapes are identical. Only the data loading
    mechanism changed internally.
"""

import json
import random
import string
from datetime import date

from sentinel.config.settings import settings
from sentinel.config.data_loader import MockDataLoader


def _get_loader() -> MockDataLoader:
    """
    Return a fresh MockDataLoader instance.
    Fresh instance = today's date recalculated on every call.
    Never cache the loader at module level.
    """
    return MockDataLoader()


def get_customer(customer_id: str) -> dict:
    """
    Look up a customer by their customer ID.
    Returns full profile. Always call this first to verify identity.
    """
    loader = _get_loader()
    customer = loader.get_customer_by_id(customer_id)

    if customer:
        return {"error": False, "customer": customer}

    return {
        "error": True,
        "error_category": "validation",
        "is_retryable": False,
        "message": f"No customer found with ID: {customer_id}",
    }


def lookup_order(order_id: str) -> dict:
    """
    Retrieve full order details by order ID.
    Returns status, items, amounts, dates, and return window.
    """
    loader = _get_loader()
    order = loader.get_order_by_id(order_id)

    if order:
        return {"error": False, "order": order}

    return {
        "error": True,
        "error_category": "validation",
        "is_retryable": False,
        "message": f"No order found with ID: {order_id}",
    }


def get_order_history(customer_id: str) -> dict:
    """
    Retrieve all orders for a customer.
    Returns list sorted newest first.
    Use when customer doesn't provide an order ID.
    """
    loader = _get_loader()
    orders = loader.get_orders_by_customer(customer_id)

    return {
        "error": False,
        "customer_id": customer_id,
        "order_count": len(orders),
        "orders": orders,
        "message": (
            f"Found {len(orders)} orders"
            if orders
            else "No orders found for this customer"
        ),
    }


def check_refund_eligibility(order_id: str) -> dict:
    """
    Check whether an order qualifies for a refund.
    Always call this BEFORE process_refund.
    Returns eligible=true/false with reason and amount.
    """
    loader = _get_loader()
    order = loader.get_order_by_id(order_id)

    if not order:
        return {
            "error": True,
            "error_category": "validation",
            "is_retryable": False,
            "message": f"Order {order_id} not found",
        }

    # Check 1: Must be delivered
    if order["status"] != "delivered":
        return {
            "error": False,
            "eligible": False,
            "order_id": order_id,
            "reason": (
                f"Order status is '{order['status']}'. "
                f"Only delivered orders can be refunded."
            ),
        }

    # Check 2: Return window
    # days_since_delivery is pre-computed by MockDataLoader
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

    # Eligible — compute processing time from policy
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
            f"Refund of ${order['total_amount']:.2f} can be processed."
        ),
    }


def process_refund(order_id: str, amount: float) -> dict:
    """
    Process a refund for an eligible order.
    PREREQUISITES: get_customer and check_refund_eligibility first.
    Refunds above $500 require human escalation.
    """
    if amount > settings.refund_approval_limit:
        return {
            "error": True,
            "error_category": "business",
            "is_retryable": False,
            "message": (
                f"Refund of ${amount:.2f} exceeds the "
                f"${settings.refund_approval_limit:.2f} "
                f"auto-approval limit. Escalate to human agent."
            ),
            "requires_escalation": True,
        }

    loader = _get_loader()
    order = loader.get_order_by_id(order_id)

    if not order:
        return {
            "error": True,
            "error_category": "validation",
            "is_retryable": False,
            "message": f"Order {order_id} not found",
        }

    txn_id = "TXN-" + "".join(
        random.choices(string.ascii_uppercase + string.digits, k=8)
    )

    return {
        "error": False,
        "success": True,
        "transaction_id": txn_id,
        "order_id": order_id,
        "amount_refunded": amount,
        "message": (
            f"Refund of ${amount:.2f} processed. "
            f"Transaction ID: {txn_id}. "
            f"Funds appear within 3-5 business days."
        ),
    }