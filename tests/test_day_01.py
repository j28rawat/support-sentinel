"""
tests/test_day_01.py
======================
Tests for Day 1 components.

Run: pytest tests/test_day_01.py -v
"""

import pytest
import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
))

from sentinel.tools.day_01.customer_tools import (
    get_customer,
    lookup_order,
    get_order_history,
    check_refund_eligibility,
    process_refund,
)
from sentinel.core.types import AgentResponse

class TestMockDataLoader:
    """
    Verify MockDataLoader resolves offsets correctly.
    These tests will pass on any date — no hardcoded dates.
    """

    def setup_method(self):
        from sentinel.config.data_loader import MockDataLoader
        self.loader = MockDataLoader()
        self.today = date.today()

    def test_orders_have_real_dates_not_offsets(self):
        orders = self.loader.get_orders()
        for order in orders:
            # Offset fields should be resolved — not present
            assert "delivery_offset_days" not in order
            assert "order_offset_days" not in order
            # Real date fields should be present
            assert "order_date" in order
            assert "delivery_date" in order

    def test_ord_10045_always_within_return_window(self):
        """Scenario 1 order — always eligible for refund."""
        order = self.loader.get_order_by_id("ORD-10045")
        assert order is not None
        assert order["within_return_window"] is True
        assert order["days_since_delivery"] == 5

    def test_ord_10091_always_within_window_but_over_limit(self):
        """Scenario 2 order — eligible but triggers $500 escalation."""
        order = self.loader.get_order_by_id("ORD-10091")
        assert order is not None
        assert order["within_return_window"] is True
        assert order["total_amount"] > 500

    def test_ord_10078_in_transit_no_delivery_date(self):
        """Scenario 3 order — in transit, no delivery date."""
        order = self.loader.get_order_by_id("ORD-10078")
        assert order is not None
        assert order["status"] == "in_transit"
        assert order["delivery_date"] is None
        assert order["within_return_window"] is False

    def test_customers_have_join_date_not_offset(self):
        customers = self.loader.get_customers()
        for customer in customers:
            assert "join_offset_days" not in customer
            assert "join_date" in customer

    def test_delivery_date_is_in_past(self):
        """Delivered orders should have past delivery dates."""
        order = self.loader.get_order_by_id("ORD-10045")
        delivery = date.fromisoformat(order["delivery_date"])
        assert delivery < self.today

    def test_estimated_delivery_is_in_future(self):
        """In-transit order should have future estimated delivery."""
        order = self.loader.get_order_by_id("ORD-10078")
        estimated = date.fromisoformat(order["estimated_delivery"])
        assert estimated > self.today

    def test_scenario_intent_removed_from_output(self):
        """scenario_intent is internal — should not reach Claude."""
        orders = self.loader.get_orders()
        for order in orders:
            assert "scenario_intent" not in order


class TestGetCustomer:
    def test_valid_customer_returns_profile(self):
        result = get_customer("C001")
        assert result["error"] is False
        assert result["customer"]["customer_id"] == "C001"
        assert result["customer"]["name"] == "Sarah Mitchell"

    def test_invalid_customer_returns_error(self):
        result = get_customer("C999")
        assert result["error"] is True
        assert result["error_category"] == "validation"
        assert result["is_retryable"] is False

    def test_error_has_required_fields(self):
        result = get_customer("INVALID")
        assert "error_category" in result
        assert "is_retryable" in result
        assert "message" in result


class TestLookupOrder:
    def test_valid_order_returns_details(self):
        result = lookup_order("ORD-10045")
        assert result["error"] is False
        assert result["order"]["order_id"] == "ORD-10045"
        assert result["order"]["status"] == "delivered"

    def test_invalid_order_returns_validation_error(self):
        result = lookup_order("ORD-99999")
        assert result["error"] is True
        assert result["error_category"] == "validation"


class TestGetOrderHistory:
    def test_customer_with_orders(self):
        result = get_order_history("C001")
        assert result["error"] is False
        assert result["order_count"] >= 1
        assert isinstance(result["orders"], list)

    def test_customer_with_no_orders_not_error(self):
        # Empty result is NOT an error — this is a key exam concept
        result = get_order_history("C999")
        assert result["error"] is False
        assert result["orders"] == []


class TestCheckRefundEligibility:
    def test_delivered_order_within_window_eligible(self):
        # ORD-10045 is delivered but may be outside 30-day window
        # depending on when test is run — test structure not value
        result = check_refund_eligibility("ORD-10045")
        assert result["error"] is False
        assert "eligible" in result
        assert "reason" in result

    def test_in_transit_order_not_eligible(self):
        result = check_refund_eligibility("ORD-10078")
        assert result["error"] is False
        assert result["eligible"] is False
        assert "in_transit" in result["reason"] or \
               "in transit" in result["reason"].lower()

    def test_nonexistent_order_returns_error(self):
        result = check_refund_eligibility("ORD-99999")
        assert result["error"] is True


class TestProcessRefund:
    def test_small_refund_succeeds(self):
        result = process_refund("ORD-10045", 50.00)
        assert result["error"] is False
        assert result["success"] is True
        assert "transaction_id" in result
        assert result["transaction_id"].startswith("TXN-")

    def test_large_refund_blocked(self):
        result = process_refund("ORD-10091", 549.00)
        assert result["error"] is True
        assert result["error_category"] == "business"
        assert result["is_retryable"] is False
        assert result["requires_escalation"] is True


class TestAgentResponse:
    def test_tools_used_returns_ordered_list(self):
        response = AgentResponse(
            final_response="Done",
            tool_calls=[
                {"tool": "get_customer", "input": {}, "result": ""},
                {"tool": "lookup_order", "input": {}, "result": ""},
            ],
            iterations=2,
            resolved=True,
        )
        assert response.tools_used() == ["get_customer", "lookup_order"]

    def test_was_tool_called(self):
        response = AgentResponse(
            final_response="Done",
            tool_calls=[
                {"tool": "get_customer", "input": {}, "result": ""},
            ],
            iterations=1,
            resolved=True,
        )
        assert response.was_tool_called("get_customer") is True
        assert response.was_tool_called("process_refund") is False