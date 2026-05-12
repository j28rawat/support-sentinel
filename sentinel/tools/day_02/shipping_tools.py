"""
sentinel/tools/day_02/shipping_tools.py
==========================================
Shipment tracking and lost package tools.

FROZEN: Do not modify after Day 2 is complete.

DESIGN NOTE — Why separate from order_tools?

    Order tools answer: what is the order's status?
    Shipping tools answer: where is the physical package?

    These are different questions requiring different backends.
    Keeping them separate:
    - Descriptions stay focused and unambiguous
    - Shipping tools can be scoped to agents that need them
    - Order tools remain clean for agents that don't need tracking

    In Day 4, the coordinator gives different tool subsets
    to each subagent based on their role. This separation
    makes that scoping clean.

EXAM CONCEPT — Scoped tool access (Task Statement 2.3):
    Agents should receive only the tools relevant to their role.
    A synthesis agent should not have shipping tools.
    A resolution agent might need both order and shipping tools.
"""

from sentinel.config.data_loader import MockDataLoader
from sentinel.tools.day_02.error_schemas import not_found_error

# Mock carrier tracking data
# In production: this would call a carrier API
_MOCK_TRACKING = {
    "ORD-10045": {
        "carrier": "FedEx",
        "tracking_number": "794644792798",
        "current_status": "delivered",
        "events": [
            {
                "event": "Package delivered",
                "location": "Austin TX",
                "date_offset": -5,
                "time": "14:32",
            },
            {
                "event": "Out for delivery",
                "location": "Austin TX",
                "date_offset": -5,
                "time": "08:15",
            },
            {
                "event": "Arrived at facility",
                "location": "Austin TX",
                "date_offset": -6,
                "time": "22:10",
            },
        ],
    },
    "ORD-10078": {
        "carrier": "UPS",
        "tracking_number": "1Z999AA10123456784",
        "current_status": "in_transit",
        "events": [
            {
                "event": "In transit to destination",
                "location": "Kansas City MO",
                "date_offset": -1,
                "time": "09:00",
            },
            {
                "event": "Departed origin facility",
                "location": "Denver CO",
                "date_offset": -2,
                "time": "16:45",
            },
            {
                "event": "Shipment picked up",
                "location": "Denver CO",
                "date_offset": -3,
                "time": "20:00",
            },
        ],
    },
}


def _resolve_tracking_dates(tracking: dict) -> dict:
    """Resolve date offsets in tracking events to real dates."""
    from datetime import date, timedelta
    today = date.today()
    resolved = dict(tracking)
    resolved["events"] = []

    for event in tracking["events"]:
        e = dict(event)
        offset = e.pop("date_offset", 0)
        e["date"] = (
            today + timedelta(days=offset)
        ).isoformat()
        resolved["events"].append(e)

    return resolved


def track_shipment(order_id: str) -> dict:
    """
    Get carrier tracking status and event history for an order.

    WHEN TO USE:
        Customer asks 'where is my order?' or 'when will it arrive?'
        Customer reports a delivery issue or missing package.
        Use for orders with status 'in_transit' or 'delivered'.

    WHEN NOT TO USE:
        Customer asks about order status (items, amounts, returns) —
        use lookup_order instead.
        Customer asks about refunds — use refund tools.
        Do not confuse carrier tracking with order management.

    RETURNS:
        carrier, tracking_number, current_status,
        chronological list of tracking events with dates,
        times, and locations. Latest event listed first.

    ERRORS:
        validation — order not found.
        If no tracking available yet (pending order): returns
        tracking_available=false with explanation, not an error.
    """
    tracking_raw = _MOCK_TRACKING.get(order_id)

    if not tracking_raw:
        loader = MockDataLoader()
        order = loader.get_order_by_id(order_id)

        if not order:
            return not_found_error("order", order_id)

        if order["status"] == "pending":
            return {
                "error": False,
                "order_id": order_id,
                "tracking_available": False,
                "message": (
                    "This order has not shipped yet. "
                    "Tracking will be available once it ships."
                ),
            }

        return {
            "error": False,
            "order_id": order_id,
            "tracking_available": False,
            "message": (
                "Tracking information is not yet available "
                "for this order."
            ),
        }

    tracking = _resolve_tracking_dates(tracking_raw)

    return {
        "error": False,
        "order_id": order_id,
        "tracking_available": True,
        "carrier": tracking["carrier"],
        "tracking_number": tracking["tracking_number"],
        "current_status": tracking["current_status"],
        "latest_event": (
            tracking["events"][0]
            if tracking["events"] else None
        ),
        "all_events": tracking["events"],
    }


def report_lost_package(
    order_id: str,
    customer_id: str
) -> dict:
    """
    File a lost package claim for an undelivered order.

    WHEN TO USE:
        Customer reports package not received AND it has been
        more than 7 days past the expected delivery date.
        Always call track_shipment first to verify the package
        is genuinely lost (not delivered to a neighbour).
        Always verify identity via get_customer first.

    WHEN NOT TO USE:
        Tracking shows the package as delivered — cannot file
        a lost claim for a delivered package.
        Less than 7 days past expected delivery — too early.

    RETURNS:
        claim_reference number and next steps for the customer.

    ERRORS:
        business — package shows as delivered in carrier system.
                   Customer should check with neighbours.
    """
    # Check carrier status first
    tracking_raw = _MOCK_TRACKING.get(order_id, {})
    if tracking_raw.get("current_status") == "delivered":
        return {
            "error": False,
            "claim_filed": False,
            "reason": (
                "Our carrier records show this package was delivered. "
                "Please check with neighbours or building reception. "
                "If still not found after 24 hours, contact us again "
                "and we will open a formal investigation."
            ),
        }

    loader = MockDataLoader()
    order = loader.get_order_by_id(order_id)
    if not order:
        return not_found_error("order", order_id)

    import random
    claim_ref = f"CLAIM-{random.randint(100000, 999999)}"

    return {
        "error": False,
        "claim_filed": True,
        "claim_reference": claim_ref,
        "order_id": order_id,
        "customer_id": customer_id,
        "message": (
            f"Lost package claim filed successfully. "
            f"Reference: {claim_ref}. "
            f"Our team will investigate within 2 business days "
            f"and contact you at your registered email."
        ),
        "next_steps": [
            "Confirmation email sent within 1 hour",
            "Investigation takes 2-3 business days",
            "Replacement or refund issued upon confirmation",
        ],
    }