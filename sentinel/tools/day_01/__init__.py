"""
sentinel/tools/day_01/__init__.py
===================================
Tool registry — Day 1 snapshot.

FROZEN: Do not modify after Day 1 is complete.

Contains: 5 tools covering the core support workflow.
    get_customer, lookup_order, get_order_history,
    check_refund_eligibility, process_refund

Day 2 adds: search_customers, order history improvements,
    shipping tools, escalation tools, structured errors.

VERSIONING NOTE:
    days/day_01_agentic_loop/exercise.py imports from HERE.
    It will always run correctly regardless of what Day 2+
    adds to the codebase.
"""

import json
from sentinel.tools.day_01.customer_tools import (
    get_customer,
    lookup_order,
    get_order_history,
    check_refund_eligibility,
    process_refund,
)

# ── Tool definitions (what Claude sees) ──────────────────────────────────────

ALL_TOOL_DEFINITIONS = [
    {
        "name": "get_customer",
        "description": (
            "Retrieve a customer record by customer ID (format: C001). "
            "Returns full profile including name, email, tier, status. "
            "ALWAYS call this first to verify identity before any "
            "account action. Required before lookup_order or process_refund."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer ID — format C001, C002, C003"
                }
            },
            "required": ["customer_id"]
        }
    },
    {
        "name": "lookup_order",
        "description": (
            "Retrieve details for a specific order by order ID "
            "(format: ORD-#####). Returns status, items, total, "
            "delivery date, and return window. "
            "Use when customer provides an order ID. "
            "Use get_order_history instead when no order ID is given."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID — format ORD-10045"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "get_order_history",
        "description": (
            "Retrieve all orders for a customer. "
            "Use when a customer refers to 'my order' without giving "
            "an order ID, or when you need to find which order they mean. "
            "Do not use when customer has already provided an order ID "
            "— use lookup_order instead."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer ID to fetch order history for"
                }
            },
            "required": ["customer_id"]
        }
    },
    {
        "name": "check_refund_eligibility",
        "description": (
            "Check whether an order qualifies for a refund. "
            "Returns eligible=true/false, reason, and refund amount. "
            "ALWAYS call this BEFORE process_refund — never skip. "
            "Use to explain eligibility to customer before acting."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID to check for refund eligibility"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "process_refund",
        "description": (
            "Process a refund for a confirmed-eligible order. "
            "PREREQUISITES: Must call get_customer AND "
            "check_refund_eligibility first. "
            "Refunds above $500 are blocked — escalate to human instead. "
            "Returns transaction ID and processing timeline."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID to refund"
                },
                "amount": {
                    "type": "number",
                    "description": "Refund amount in USD"
                }
            },
            "required": ["order_id", "amount"]
        }
    },
]


# ── Tool executor ─────────────────────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict) -> str:
    """
    Route Claude's tool call to the correct Python function.
    Returns JSON string (Anthropic API requires string content).

    DESIGN PATTERN — Dispatch map:
        A dict mapping tool names to lambda functions.
        Clean, readable, easy to extend.
        Adding a new tool = one new dict entry.
    """
    dispatch = {
        "get_customer": lambda i: get_customer(
            i["customer_id"]
        ),
        "lookup_order": lambda i: lookup_order(
            i["order_id"]
        ),
        "get_order_history": lambda i: get_order_history(
            i["customer_id"]
        ),
        "check_refund_eligibility": lambda i: check_refund_eligibility(
            i["order_id"]
        ),
        "process_refund": lambda i: process_refund(
            i["order_id"], i["amount"]
        ),
    }

    if tool_name not in dispatch:
        return json.dumps({
            "error": True,
            "error_category": "validation",
            "is_retryable": False,
            "message": f"Unknown tool: {tool_name}",
        })

    result = dispatch[tool_name](tool_input)
    return json.dumps(result, default=str)