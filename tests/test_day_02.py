"""
tests/test_day_02.py
======================
Tests for Day 2 components.

Run: pytest tests/test_day_02.py -v

All tests run without API calls.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
))

from sentinel.tools.day_02.error_schemas import (
    not_found_error,
    service_unavailable_error,
    business_rule_error,
    permission_error,
)
from sentinel.tools.day_02.customer_tools import (
    get_customer,
    search_customers,
)
from sentinel.tools.day_02.order_tools import (
    lookup_order,
    get_order_history,
)
from sentinel.tools.day_02.refund_tools import (
    check_refund_eligibility,
    process_refund,
)
from sentinel.tools.day_02.shipping_tools import (
    track_shipment,
    report_lost_package,
)
from sentinel.tools.day_02.escalation_tools import (
    escalate_to_human,
)


class TestErrorSchemas:
    """Verify structured error constructors produce correct fields."""

    def test_not_found_is_validation_not_retryable(self):
        err = not_found_error("customer", "C999")
        assert err["error"] is True
        assert err["error_category"] == "validation"
        assert err["is_retryable"] is False

    def test_service_unavailable_is_transient_retryable(self):
        err = service_unavailable_error("payments", "refund")
        assert err["error"] is True
        assert err["error_category"] == "transient"
        assert err["is_retryable"] is True

    def test_business_rule_not_retryable(self):
        err = business_rule_error("test_rule", "Policy prevents this.")
        assert err["error"] is True
        assert err["error_category"] == "business"
        assert err["is_retryable"] is False

    def test_business_rule_escalation_flag(self):
        err = business_rule_error(
            "limit", "Exceeds limit.", requires_escalation=True
        )
        assert err["requires_escalation"] is True

    def test_permission_error_always_escalates(self):
        err = permission_error("delete_account", "agent not authorised")
        assert err["error"] is True
        assert err["error_category"] == "permission"
        assert err["is_retryable"] is False
        assert err["requires_escalation"] is True

    def test_all_errors_have_required_fields(self):
        required = {
            "error", "error_category",
            "is_retryable", "message"
        }
        errors = [
            not_found_error("x", "y"),
            service_unavailable_error("x", "y"),
            business_rule_error("x", "y"),
            permission_error("x", "y"),
        ]
        for err in errors:
            for field in required:
                assert field in err, (
                    f"Field '{field}' missing from error: {err}"
                )


class TestCustomerToolsDay02:
    def test_valid_customer_returns_profile(self):
        result = get_customer("C001")
        assert result["error"] is False
        assert result["customer"]["name"] == "Sarah Mitchell"

    def test_invalid_customer_structured_error(self):
        result = get_customer("C999")
        assert result["error"] is True
        assert result["error_category"] == "validation"
        assert result["is_retryable"] is False

    def test_search_by_name_finds_match(self):
        result = search_customers(name="Sarah")
        assert result["error"] is False
        assert result["match_count"] >= 1

    def test_search_by_email_finds_match(self):
        result = search_customers(
            email="james.okonkwo@email.com"
        )
        assert result["error"] is False
        assert result["match_count"] == 1

    def test_search_empty_params_returns_error(self):
        result = search_customers()
        assert result["error"] is True
        assert result["error_category"] == "validation"

    def test_search_no_match_is_not_error(self):
        """Empty search result is NOT an error — key exam concept."""
        result = search_customers(name="ZZZNobodyNamedThis")
        assert result["error"] is False
        assert result["match_count"] == 0
        assert result["matches"] == []


class TestOrderToolsDay02:
    def test_lookup_valid_order(self):
        result = lookup_order("ORD-10045")
        assert result["error"] is False
        assert result["order"]["order_id"] == "ORD-10045"

    def test_lookup_invalid_order_structured_error(self):
        result = lookup_order("ORD-99999")
        assert result["error"] is True
        assert result["error_category"] == "validation"
        assert result["is_retryable"] is False

    def test_order_history_returns_orders(self):
        result = get_order_history("C001")
        assert result["error"] is False
        assert result["order_count"] >= 1

    def test_order_history_empty_is_not_error(self):
        """Empty order history is NOT an error — key exam concept."""
        result = get_order_history("C999")
        assert result["error"] is False
        assert result["orders"] == []
        assert result["order_count"] == 0


class TestRefundToolsDay02:
    def test_eligible_order_returns_amount(self):
        result = check_refund_eligibility("ORD-10045")
        assert result["error"] is False
        assert "eligible" in result
        if result["eligible"]:
            assert "refund_amount" in result

    def test_in_transit_order_not_eligible(self):
        result = check_refund_eligibility("ORD-10078")
        assert result["error"] is False
        assert result["eligible"] is False

    def test_small_refund_succeeds(self):
        result = process_refund("ORD-10045", 50.00)
        assert result["error"] is False
        assert result["success"] is True
        assert result["transaction_id"].startswith("TXN-")

    def test_large_refund_business_error(self):
        result = process_refund("ORD-10091", 549.00)
        assert result["error"] is True
        assert result["error_category"] == "business"
        assert result["is_retryable"] is False
        assert result["requires_escalation"] is True

    def test_large_refund_not_retryable(self):
        """Business rule violations must not be retried."""
        result = process_refund("ORD-10091", 549.00)
        assert result["is_retryable"] is False


class TestShippingToolsDay02:
    def test_track_delivered_order(self):
        result = track_shipment("ORD-10045")
        assert result["error"] is False
        assert result["tracking_available"] is True
        assert result["current_status"] == "delivered"

    def test_track_in_transit_order(self):
        result = track_shipment("ORD-10078")
        assert result["error"] is False
        assert result["tracking_available"] is True
        assert result["current_status"] == "in_transit"

    def test_track_unknown_order_error(self):
        result = track_shipment("ORD-99999")
        assert result["error"] is True
        assert result["error_category"] == "validation"

    def test_tracking_events_have_real_dates(self):
        """Tracking events should have resolved dates, not offsets."""
        result = track_shipment("ORD-10045")
        assert result["tracking_available"] is True
        for event in result["all_events"]:
            assert "date" in event
            assert "date_offset" not in event


class TestEscalationToolsDay02:
    def test_escalation_returns_ticket_id(self):
        result = escalate_to_human(
            customer_id="C001",
            issue_summary="Customer wants refund for Smart Watch",
            investigation_summary="Order ORD-10091 checked, "
                                  "refund amount $549 exceeds limit",
            recommended_action="Approve high-value refund manually",
            escalation_reason="Refund exceeds $500 auto-approval limit",
        )
        assert result["error"] is False
        assert result["escalated"] is True
        assert result["ticket_id"].startswith("TKT-")

    def test_escalation_has_wait_time(self):
        result = escalate_to_human(
            customer_id="C001",
            issue_summary="Test",
            investigation_summary="Test",
            recommended_action="Test",
            escalation_reason="Test",
        )
        assert "estimated_wait_minutes" in result

    def test_refund_reason_gets_high_priority(self):
        result = escalate_to_human(
            customer_id="C001",
            issue_summary="Refund issue",
            investigation_summary="Checked order",
            recommended_action="Process manually",
            escalation_reason="Refund exceeds approval limit",
        )
        assert result["priority"] == "high"


class TestDay01StillWorks:
    """
    Verify Day 1 tools are completely unaffected by Day 2.
    This is the versioning contract in action.
    """

    def test_day_01_get_customer_still_works(self):
        from sentinel.tools.day_01.customer_tools import get_customer
        result = get_customer("C001")
        assert result["error"] is False
        assert result["customer"]["name"] == "Sarah Mitchell"

    def test_day_01_lookup_order_still_works(self):
        from sentinel.tools.day_01.customer_tools import lookup_order
        result = lookup_order("ORD-10045")
        assert result["error"] is False

    def test_day_01_imports_unchanged(self):
        from sentinel.tools.day_01 import (
            ALL_TOOL_DEFINITIONS,
            execute_tool,
        )
        assert len(ALL_TOOL_DEFINITIONS) == 5