"""
sentinel/tools/day_02/__init__.py
====================================
Tool registry — Day 2 frozen snapshot.

FROZEN: Do not modify after Day 2 is complete.

TOOLS IN THIS SNAPSHOT (9 total):
    get_customer              Identity verification by ID
    search_customers          Discovery when ID is unknown  ← NEW
    lookup_order              Single order by ID
    get_order_history         All orders for a customer
    check_refund_eligibility  Validate before processing
    process_refund            Execute the refund
    track_shipment            Carrier tracking events       ← NEW
    report_lost_package       File lost package claim       ← NEW
    escalate_to_human         Structured human handoff      ← NEW

CHANGES FROM DAY 1 (sentinel/tools/day_01/):
    + 4 new tools added (search_customers, track_shipment,
      report_lost_package, escalate_to_human)
    + Structured error schema (errorCategory, isRetryable)
    + All tools separated into dedicated modules
    + All descriptions include WHEN TO USE / WHEN NOT TO USE
    + Boundaries explicitly reference alternative tools

KEY EXAM CONCEPT — Description quality:
    Compare the description for lookup_order here vs day_01.
    Day 1: "Retrieve details for a specific order by order ID."
    Day 2: Includes WHEN TO USE, WHEN NOT TO USE referencing
           get_order_history, specific input format, all return
           fields listed, error types documented.
    Same tool. Vastly different routing reliability.

VERSIONING NOTE:
    days/day_02_tool_design/exercise.py imports from HERE.
    days/day_01_agentic_loop/exercise.py still imports from
    sentinel.tools.day_01 and is completely unaffected.
"""

import json
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

# ── Tool definitions — what Claude sees ──────────────────────────────────────

ALL_TOOL_DEFINITIONS = [
    {
        "name": "get_customer",
        "description": (
            "Retrieve a verified customer record by exact customer ID "
            "(format: C001, C002, C003). Returns full profile: name, "
            "email, tier (standard/gold), account_status, join_date, "
            "total_orders. "
            "WHEN TO USE: Customer has provided their customer ID. "
            "ALWAYS call this first before any order or refund action. "
            "WHEN NOT TO USE: Customer has not provided an ID — "
            "use search_customers to find them by name or email."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer ID — format C001, C002, C003",
                }
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "search_customers",
        "description": (
            "Search for a customer by name or email when their customer "
            "ID is unknown. Returns list of potential matches. "
            "WHEN TO USE: Customer contacts you without providing their "
            "customer ID. Provide at least one of: name or email. "
            "If multiple matches found, ask the customer to confirm "
            "their customer ID — never guess between matches. "
            "WHEN NOT TO USE: Customer has already given their ID — "
            "use get_customer instead (faster and more precise)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Customer full or partial name",
                },
                "email": {
                    "type": "string",
                    "description": "Customer email address",
                },
            },
            "required": [],
        },
    },
    {
        "name": "lookup_order",
        "description": (
            "Retrieve complete details for ONE specific order by its ID "
            "(format: ORD-#####). Returns status, line items, total "
            "amount, order_date, delivery_date, days_since_delivery, "
            "within_return_window. "
            "WHEN TO USE: Customer provides a specific order ID. "
            "WHEN NOT TO USE: Customer says 'my order' without an ID — "
            "use get_order_history to find which order they mean. "
            "Do not call this without a valid order ID."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID — format ORD-10045",
                }
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "get_order_history",
        "description": (
            "Retrieve all recent orders for a customer by customer ID. "
            "Returns up to 5 orders sorted newest-first. Each includes "
            "order_id, status, dates, total amount, item names. "
            "WHEN TO USE: Customer refers to 'my order' without an ID. "
            "You need to find which order they are asking about. "
            "Returns empty list (not an error) if no orders exist. "
            "WHEN NOT TO USE: Customer has provided an order ID — "
            "use lookup_order instead (faster and more specific)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer ID to fetch order history for",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum orders to return (default 5)",
                    "default": 5,
                },
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "check_refund_eligibility",
        "description": (
            "Check whether an order qualifies for a refund based on "
            "return policy. Returns eligible=true/false with reason "
            "and refund amount if eligible. "
            "WHEN TO USE: Before processing any refund — without exception. "
            "ALWAYS call this BEFORE process_refund — never skip. "
            "Use the result to explain eligibility to the customer. "
            "WHEN NOT TO USE: Eligibility already confirmed this session."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID to check eligibility for",
                }
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "process_refund",
        "description": (
            "Execute a refund for a confirmed-eligible order. "
            "Returns transaction_id and processing timeline. "
            "PREREQUISITES — MUST complete both first: "
            "1) get_customer must have verified identity this session. "
            "2) check_refund_eligibility must have returned eligible=true. "
            "WHEN NOT TO USE: Amount exceeds $500 — use escalate_to_human. "
            "Eligibility not yet confirmed — run check_refund_eligibility."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID to process refund for",
                },
                "amount": {
                    "type": "number",
                    "description": "Refund amount in USD",
                },
            },
            "required": ["order_id", "amount"],
        },
    },
    {
        "name": "track_shipment",
        "description": (
            "Get carrier tracking status and event history for an order. "
            "Returns carrier, tracking number, current status, and "
            "chronological events with dates, times, locations. "
            "WHEN TO USE: Customer asks 'where is my order?' or "
            "'when will it arrive?' or reports a delivery issue. "
            "WHEN NOT TO USE: Order status questions about items or "
            "amounts — use lookup_order. Refund questions — use refund tools. "
            "Tracking and order status are different concepts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID to track",
                }
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "report_lost_package",
        "description": (
            "File a lost package claim for an order not received "
            "7+ days past expected delivery. "
            "WHEN TO USE: Customer reports package not received AND "
            "it is 7+ days past expected delivery. "
            "Always call track_shipment first to verify genuinely lost. "
            "Always verify identity via get_customer first. "
            "WHEN NOT TO USE: Tracking shows package as delivered — "
            "cannot file lost claim. Fewer than 7 days past delivery."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID for the lost package",
                },
                "customer_id": {
                    "type": "string",
                    "description": "Verified customer ID",
                },
            },
            "required": ["order_id", "customer_id"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": (
            "Transfer case to a human agent with complete structured handoff. "
            "WHEN TO USE: Customer explicitly requests a human. "
            "Refund exceeds $500. Policy is ambiguous or silent. "
            "Cannot resolve after thorough investigation. "
            "Any tool returns requires_escalation=true. "
            "WHEN NOT TO USE: Customer is frustrated but issue is solvable — "
            "offer to resolve first, escalate only if they insist. "
            "Always provide full investigation_summary so human agent "
            "does not ask customer to repeat themselves."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer ID for the human to pull up",
                },
                "issue_summary": {
                    "type": "string",
                    "description": "What the customer wants (1-2 sentences)",
                },
                "investigation_summary": {
                    "type": "string",
                    "description": "What was already checked and tried",
                },
                "recommended_action": {
                    "type": "string",
                    "description": "What the human agent should do next",
                },
                "escalation_reason": {
                    "type": "string",
                    "description": "Specific reason WHY escalating",
                },
            },
            "required": [
                "customer_id",
                "issue_summary",
                "investigation_summary",
                "recommended_action",
                "escalation_reason",
            ],
        },
    },
]

# ── Vague definitions — used in exercise Part 1 to demonstrate misrouting ────
# These are intentionally bad descriptions showing what NOT to do.
# Keep them here so the lesson is visible alongside the correct versions.

VAGUE_TOOL_DEFINITIONS = [
    {
        "name": "get_customer",
        "description": "Gets customer information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"}
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "lookup_order",
        "description": "Gets order information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"}
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "get_order_history",
        "description": "Gets order information for a customer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"}
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "check_refund_eligibility",
        "description": "Checks if an order can be refunded.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"}
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "process_refund",
        "description": "Processes a refund.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "amount": {"type": "number"},
            },
            "required": ["order_id", "amount"],
        },
    },
]


# ── Tool executor ─────────────────────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict) -> str:
    """
    Route Claude's tool call to the correct Python function.
    Returns JSON string — Anthropic API requires string content.

    Works for both ALL_TOOL_DEFINITIONS and VAGUE_TOOL_DEFINITIONS
    since the underlying Python functions are the same.
    Only the descriptions change — not the implementations.
    """
    dispatch = {
        "get_customer": lambda i: get_customer(
            i["customer_id"]
        ),
        "search_customers": lambda i: search_customers(
            i.get("name", ""),
            i.get("email", ""),
        ),
        "lookup_order": lambda i: lookup_order(
            i["order_id"]
        ),
        "get_order_history": lambda i: get_order_history(
            i["customer_id"],
            i.get("limit", 5),
        ),
        "check_refund_eligibility": lambda i: check_refund_eligibility(
            i["order_id"]
        ),
        "process_refund": lambda i: process_refund(
            i["order_id"],
            i["amount"],
        ),
        "track_shipment": lambda i: track_shipment(
            i["order_id"]
        ),
        "report_lost_package": lambda i: report_lost_package(
            i["order_id"],
            i["customer_id"],
        ),
        "escalate_to_human": lambda i: escalate_to_human(
            i["customer_id"],
            i["issue_summary"],
            i["investigation_summary"],
            i["recommended_action"],
            i["escalation_reason"],
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