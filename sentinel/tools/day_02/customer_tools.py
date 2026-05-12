"""
sentinel/tools/day_02/customer_tools.py
=========================================
Customer identity tools — Day 2 upgraded version.

FROZEN: Do not modify after Day 2 is complete.

CHANGES FROM DAY 1:
    + search_customers added (find customer without ID)
    + Structured errors via error_schemas (not raw dicts)
    + Explicit WHEN TO USE / WHEN NOT TO USE in all docstrings
    + Boundary between get_customer and search_customers made explicit

EXAM CONCEPT — Tool boundary design (Task Statement 2.1):
    get_customer    → you HAVE the ID, need to verify identity
    search_customers → you DON'T have the ID, need to find them

    Both tools deal with customers.
    Without explicit boundaries, Claude picks arbitrarily.
    With boundaries that reference each other, Claude routes correctly.
"""

from sentinel.config.data_loader import MockDataLoader
from sentinel.tools.day_02.error_schemas import not_found_error


def _get_loader() -> MockDataLoader:
    return MockDataLoader()


def get_customer(customer_id: str) -> dict:
    """
    Retrieve a verified customer record by exact customer ID.

    WHEN TO USE:
        Customer has provided their customer ID (format: C001).
        You need to verify identity before any account action.
        ALWAYS call this first before order or refund operations.

    WHEN NOT TO USE:
        Customer has not provided their ID — use search_customers.
        You need to list customers — use search_customers.

    RETURNS:
        Full profile: name, email, phone, tier (standard/gold),
        account_status (active/suspended), join_date, total_orders.

    ERRORS:
        validation — customer ID does not exist in the system.
                     Do not retry — the ID is genuinely wrong.
    """
    loader = _get_loader()
    customer = loader.get_customer_by_id(customer_id)

    if customer:
        return {"error": False, "customer": customer}

    return not_found_error("customer", customer_id)


def search_customers(
    name: str = "",
    email: str = ""
) -> dict:
    """
    Search for customers by name or email when ID is unknown.

    WHEN TO USE:
        Customer contacts you without providing their customer ID.
        You need to find their account using name or email.
        Provide at least one of: name or email.

    WHEN NOT TO USE:
        Customer has already provided their ID — use get_customer.
        get_customer is faster and more precise when ID is known.

    RETURNS:
        List of matching records. If multiple matches found,
        ask the customer to confirm their customer ID to disambiguate.
        NEVER guess between multiple matches — always ask.

    ERRORS:
        validation — neither name nor email provided.
    """
    if not name and not email:
        return {
            "error": True,
            "error_category": "validation",
            "is_retryable": False,
            "message": (
                "Provide at least one of: name or email to search. "
                "Ask the customer for their name or email address."
            ),
        }

    loader = _get_loader()
    customers = loader.get_customers()
    matches = []

    for customer in customers:
        name_match = (
            name.lower() in customer["name"].lower()
            if name else False
        )
        email_match = (
            email.lower() == customer["email"].lower()
            if email else False
        )
        if name_match or email_match:
            # Return safe subset — not full profile until verified
            matches.append({
                "customer_id": customer["customer_id"],
                "name": customer["name"],
                "email": customer["email"],
                "account_status": customer["account_status"],
            })

    if not matches:
        # EXAM NOTE: empty search result is NOT an error
        # It is a valid outcome — no matching customer exists
        return {
            "error": False,
            "message": "No customers found matching the search criteria.",
            "matches": [],
            "match_count": 0,
        }

    if len(matches) > 1:
        return {
            "error": False,
            "message": (
                f"Found {len(matches)} customers matching your search. "
                f"Ask the customer to confirm their customer ID "
                f"to proceed — do not guess between matches."
            ),
            "matches": matches,
            "match_count": len(matches),
            "action_required": "ask_customer_to_confirm_id",
        }

    return {
        "error": False,
        "message": "Found 1 matching customer.",
        "matches": matches,
        "match_count": 1,
    }