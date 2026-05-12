"""
sentinel/tools/day_02/order_tools.py
=======================================
Order lookup tools — separated from customer_tools in Day 2.

FROZEN: Do not modify after Day 2 is complete.

DESIGN DECISION — Why two tools instead of one?

    lookup_order       → ONE specific order by ID (fast, precise)
    get_order_history  → ALL orders for a customer (broader)

    Merging them into one tool degrades description quality.
    A merged tool's description becomes ambiguous:
    "Gets order information" — for one order or all orders?

    Separate tools with explicit boundaries eliminate ambiguity.
    This is the core lesson of Day 2.

EXAM CONCEPT — Task Statement 2.3:
    Giving an agent too many tools (18+) degrades reliability.
    Separate tools per concern keeps each tool's purpose clear
    and reduces the decision complexity Claude faces.

EXAM CONCEPT — Empty result vs access failure:
    get_order_history returning [] is NOT an error.
    A database timeout returning nothing IS an error.
    These must be distinguished in the response structure.
"""

from sentinel.config.data_loader import MockDataLoader
from sentinel.tools.day_02.error_schemas import not_found_error


def _get_loader() -> MockDataLoader:
    return MockDataLoader()


def lookup_order(order_id: str) -> dict:
    """
    Retrieve complete details for ONE specific order by its ID.

    WHEN TO USE:
        Customer provides an order ID (format: ORD-#####).
        You need full details: status, items, amounts, dates,
        return window, and delivery information.

    WHEN NOT TO USE:
        Customer says 'my order' without an ID —
        use get_order_history to find which order they mean.
        Never call this without a valid order ID.

    RETURNS:
        Complete order record including:
        status (pending/in_transit/delivered/returned/cancelled),
        line items with prices, total amount, order_date,
        delivery_date (null if not yet delivered),
        days_since_delivery, within_return_window (bool).

    ERRORS:
        validation — order ID does not exist. Do not retry.
    """
    loader = _get_loader()
    order = loader.get_order_by_id(order_id)

    if order:
        return {"error": False, "order": order}

    return not_found_error("order", order_id)


def get_order_history(
    customer_id: str,
    limit: int = 5
) -> dict:
    """
    Retrieve all recent orders for a customer by customer ID.

    WHEN TO USE:
        Customer refers to 'my order' or 'my recent order'
        without providing an order ID.
        You need to find which order they are asking about.
        You need an overview of their purchase history.

    WHEN NOT TO USE:
        Customer has already provided an order ID —
        use lookup_order instead (faster and more specific).

    RETURNS:
        List of up to `limit` orders sorted newest-first.
        Each order includes: order_id, status, order_date,
        delivery_date, total_amount, item names.
        Returns empty list (NOT an error) if no orders exist.

    ERRORS:
        None — empty list is a valid result meaning the
        customer has no orders. This is NOT an error.
        Do not retry or escalate on an empty result.
    """
    loader = _get_loader()
    orders = loader.get_orders_by_customer(customer_id, limit)

    # Summarise each order for readability
    summarised = []
    for order in orders:
        summarised.append({
            "order_id": order["order_id"],
            "status": order["status"],
            "order_date": order["order_date"],
            "delivery_date": order.get("delivery_date"),
            "estimated_delivery": order.get("estimated_delivery"),
            "total_amount": order["total_amount"],
            "item_count": len(order["items"]),
            "item_names": [i["name"] for i in order["items"]],
            "within_return_window": order.get(
                "within_return_window", False
            ),
        })

    return {
        "error": False,
        "customer_id": customer_id,
        "order_count": len(summarised),
        "orders": summarised,
        # EXAM NOTE: empty result is NOT an error
        "message": (
            f"Found {len(summarised)} recent order(s)."
            if summarised
            else "This customer has no orders on record."
        ),
    }