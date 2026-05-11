"""
sentinel/config/data_loader.py
================================
MockDataLoader — resolves date offsets to real dates at runtime.

DESIGN DECISION — Why offsets instead of absolute dates:

    Absolute dates (2024-11-25) become stale.
    Scenario 1 expects a successful refund (within 30-day window).
    With absolute dates, Scenario 1 silently breaks after 30 days.

    Offsets (-5 means "5 days ago") are always correct.
    "Delivered 5 days ago" is true every time the code runs.

OFFSET FIELDS:
    delivery_offset_days:          Days since delivery (negative = past)
                                   None for undelivered orders
    order_offset_days:             Days since order was placed
    estimated_delivery_offset_days: Days until estimated delivery
                                   (positive = future)
    join_offset_days:              Days since customer joined

SCENARIO INTENT:
    Each order carries a `scenario_intent` field explaining
    what the order is designed to demonstrate. This makes
    the mock data self-documenting.

ADDITIVE MODULE:
    New resolver methods appended as new days need them.
    Existing methods never modified.
"""

import json
from datetime import date, timedelta
from pathlib import Path

from sentinel.config.settings import settings


class MockDataLoader:
    """
    Loads mock data and resolves date offsets to real dates.

    Usage:
        loader = MockDataLoader()
        customers = loader.get_customers()
        orders = loader.get_orders()
        order = loader.get_order_by_id("ORD-10045")

    All returned dicts contain real ISO date strings
    (e.g., "2026-05-05") computed relative to today.
    Tools can use these directly — no offset arithmetic needed.
    """

    def __init__(self) -> None:
        self._data_path = Path(settings.mock_data_path)
        self._today = date.today()

    def _resolve_offset(self, offset_days: int | None) -> str | None:
        """
        Convert an integer offset to an ISO date string.

        Args:
            offset_days: Days relative to today.
                         Negative = past (e.g., -5 = 5 days ago)
                         Positive = future (e.g., 2 = in 2 days)
                         None = not applicable (e.g., undelivered order)

        Returns:
            ISO date string "YYYY-MM-DD" or None
        """
        if offset_days is None:
            return None
        return (self._today + timedelta(days=offset_days)).isoformat()

    def _load_raw(self, filename: str) -> list | dict:
        """Load raw JSON without offset resolution."""
        path = self._data_path / filename
        return json.loads(path.read_text())

    def get_customers(self) -> list[dict]:
        """
        Load all customers with resolved join dates.

        join_offset_days → join_date (ISO string)
        """
        raw = self._load_raw("customers.json")
        resolved = []

        for customer in raw:
            c = dict(customer)
            c["join_date"] = self._resolve_offset(
                c.pop("join_offset_days", None)
            )
            resolved.append(c)

        return resolved

    def get_orders(self) -> list[dict]:
        """
        Load all orders with resolved dates.

        delivery_offset_days          → delivery_date
        order_offset_days             → order_date
        estimated_delivery_offset_days → estimated_delivery

        Also computes derived fields:
            days_since_delivery: int (for eligibility checks)
            within_return_window: bool
        """
        raw = self._load_raw("orders.json")
        resolved = []

        for order in raw:
            o = dict(order)

            # Resolve date offsets → real dates
            delivery_offset = o.pop("delivery_offset_days", None)
            order_offset = o.pop("order_offset_days", None)
            estimated_offset = o.pop(
                "estimated_delivery_offset_days", None
            )

            o["order_date"] = self._resolve_offset(order_offset)
            o["delivery_date"] = self._resolve_offset(delivery_offset)
            o["estimated_delivery"] = self._resolve_offset(
                estimated_offset
            )

            # Compute derived fields for delivered orders
            if delivery_offset is not None:
                days_since = abs(delivery_offset)
                o["days_since_delivery"] = days_since
                o["within_return_window"] = (
                    days_since <= o["return_window_days"]
                )
            else:
                o["days_since_delivery"] = None
                o["within_return_window"] = False

            # Remove internal scenario_intent from tool responses
            # (useful for developers reading JSON, not for Claude)
            o.pop("scenario_intent", None)

            resolved.append(o)

        return resolved

    def get_policies(self) -> dict:
        """Load policies — no date fields to resolve."""
        return self._load_raw("policies.json")

    def get_customer_by_id(self, customer_id: str) -> dict | None:
        """Find a single customer by ID. Returns None if not found."""
        return next(
            (c for c in self.get_customers()
             if c["customer_id"] == customer_id),
            None
        )

    def get_order_by_id(self, order_id: str) -> dict | None:
        """Find a single order by ID. Returns None if not found."""
        return next(
            (o for o in self.get_orders()
             if o["order_id"] == order_id),
            None
        )

    def get_orders_by_customer(
        self,
        customer_id: str,
        limit: int = 5
    ) -> list[dict]:
        """
        Get all orders for a customer, newest first.
        Returns up to `limit` orders.
        """
        orders = [
            o for o in self.get_orders()
            if o["customer_id"] == customer_id
        ]
        orders.sort(key=lambda x: x["order_date"], reverse=True)
        return orders[:limit]

    def debug_scenario_dates(self) -> None:
        """
        Print all order dates as resolved today.
        Run this to verify scenarios will behave as expected.

        Usage:
            from sentinel.config.data_loader import MockDataLoader
            MockDataLoader().debug_scenario_dates()
        """
        print(f"\n{'─'*60}")
        print(f"MockDataLoader — Scenario Date Debug")
        print(f"Today: {self._today.isoformat()}")
        print(f"{'─'*60}")

        raw_orders = self._load_raw("orders.json")
        for raw in raw_orders:
            d_offset = raw.get("delivery_offset_days")
            o_offset = raw.get("order_offset_days")
            window = raw.get("return_window_days", 30)
            amount = raw.get("total_amount", 0)

            delivery_date = self._resolve_offset(d_offset)
            order_date = self._resolve_offset(o_offset)
            days_since = abs(d_offset) if d_offset is not None else None
            within_window = (
                days_since <= window
                if days_since is not None
                else False
            )

            status_icon = "✓" if within_window else "✗"
            escalation = " ⚠ ESCALATION" if amount > 500 else ""

            print(
                f"\n{raw['order_id']} ({raw['status']})"
                f"\n  Intent:      {raw.get('scenario_intent', 'N/A')}"
                f"\n  Order date:  {order_date}"
                f"\n  Delivered:   {delivery_date}"
                f"\n  Days since:  {days_since}"
                f"\n  Window:      {window} days"
                f"\n  Eligible:    {status_icon} {within_window}"
                f"\n  Amount:      ${amount:.2f}{escalation}"
            )
        print(f"\n{'─'*60}\n")


# Module-level convenience instance
# Usage: from sentinel.config.data_loader import loader
loader = MockDataLoader()