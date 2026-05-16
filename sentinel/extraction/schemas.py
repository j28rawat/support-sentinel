"""
sentinel/extraction/schemas.py
================================
JSON schemas for all structured outputs in SupportSentinel.

ADDITIVE MODULE:
    Day 3: INCIDENT_SCHEMA — extract structured data from
           raw customer messages
    Day 4+: Additional schemas appended as needed

EXAM CRITICAL — Task Statement 4.3:

    tool_use with JSON schema is the MOST RELIABLE approach
    for guaranteed schema-compliant output. It eliminates
    JSON syntax errors entirely.

    But it does NOT prevent semantic errors:
    - Values placed in wrong fields
    - Amounts that don't match the order
    - Contradictory data (eligible=true but status=in_transit)

    Semantic validation requires code — see validator.py.

SCHEMA DESIGN PRINCIPLES:

    Required fields:  Fields that must always be present.
                      Claude will always populate these.
                      Use for fields with reliable default values.

    Optional (nullable) fields: Fields that may not exist in
                      the source. Marked with type: [X, null].
                      Claude returns null when data is absent.
                      NEVER make a field required if source
                      documents may not contain it — this forces
                      Claude to hallucinate a value.

    Enum fields:      Constrain to known values.
                      Add "other" + detail string pattern for
                      extensible categorisation without losing
                      unknown values.
"""

# ── Incident extraction schema ────────────────────────────────────────────────
# Extracts structured data from raw customer support messages.
# Used by IncidentExtractor in incident_extractor.py.

INCIDENT_SCHEMA = {
    "name": "extract_incident",
    "description": (
        "Extract structured incident data from a raw customer "
        "support message. Return null for any field not explicitly "
        "present in the message — never guess or infer missing data."
    ),
    "input_schema": {
        "type": "object",
        "properties": {

            # ── Identity fields ───────────────────────────────────
            "customer_id": {
                "type": ["string", "null"],
                "description": (
                    "Customer ID if explicitly stated "
                    "(format: C001, C002). Null if not provided."
                ),
            },
            "customer_name": {
                "type": ["string", "null"],
                "description": (
                    "Customer first name if mentioned. "
                    "Null if not provided."
                ),
            },

            # ── Order fields ──────────────────────────────────────
            "order_id": {
                "type": ["string", "null"],
                "description": (
                    "Order ID if explicitly stated "
                    "(format: ORD-#####). Null if not provided."
                ),
            },

            # ── Issue classification ──────────────────────────────
            "issue_type": {
                "type": "string",
                "enum": [
                    "refund_request",
                    "return_request",
                    "missing_package",
                    "damaged_item",
                    "wrong_item",
                    "delivery_delay",
                    "billing_issue",
                    "account_issue",
                    "other",
                ],
                "description": (
                    "Primary issue type. Use 'other' only when "
                    "no enum value fits — also populate "
                    "issue_type_detail in that case."
                ),
            },
            "issue_type_detail": {
                "type": ["string", "null"],
                "description": (
                    "Free-text detail when issue_type is 'other'. "
                    "Null for all standard issue types."
                ),
            },

            # ── Resolution request ────────────────────────────────
            "requested_resolution": {
                "type": ["string", "null"],
                "enum": [
                    "refund",
                    "replacement",
                    "return",
                    "tracking_info",
                    "account_help",
                    "explanation",
                    "other",
                    None,
                ],
                "description": (
                    "What the customer is asking for. "
                    "Null if not explicitly stated."
                ),
            },

            # ── Financial ─────────────────────────────────────────
            "amount_mentioned": {
                "type": ["number", "null"],
                "description": (
                    "Dollar amount mentioned by customer. "
                    "Null if no amount stated. "
                    "Extract as number, not string."
                ),
            },

            # ── Priority signals ──────────────────────────────────
            "urgency": {
                "type": "string",
                "enum": ["urgent", "high", "normal", "low"],
                "description": (
                    "urgent: explicit urgency words or threats. "
                    "high: strong frustration or financial impact. "
                    "normal: standard request. "
                    "low: general inquiry."
                ),
            },
            "sentiment": {
                "type": "string",
                "enum": ["positive", "neutral", "negative"],
                "description": (
                    "Overall customer sentiment in the message."
                ),
            },

            # ── Summary ───────────────────────────────────────────
            "key_facts": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "List of 2-5 key facts extracted from the "
                    "message. Each fact is a short phrase. "
                    "These are used for the agent's case summary."
                ),
                "minItems": 1,
                "maxItems": 5,
            },

            # ── Confidence ────────────────────────────────────────
            "extraction_confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": (
                    "high: all key fields clearly stated. "
                    "medium: some fields inferred from context. "
                    "low: message is ambiguous or very brief."
                ),
            },

        },
        "required": [
            "issue_type",
            "urgency",
            "sentiment",
            "key_facts",
            "extraction_confidence",
        ],
    },
}

# ── Resolution output schema ──────────────────────────────────────────────────
# Used in Day 4+ for subagent structured outputs.
# Defined here now so it's available when needed.

RESOLUTION_SCHEMA = {
    "name": "extract_resolution",
    "description": (
        "Extract structured resolution data from an agent's "
        "completed case handling."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "resolved": {
                "type": "boolean",
                "description": "Whether the issue was fully resolved.",
            },
            "resolution_type": {
                "type": ["string", "null"],
                "enum": [
                    "refund_processed",
                    "return_initiated",
                    "tracking_provided",
                    "escalated_to_human",
                    "information_provided",
                    "no_action_needed",
                    None,
                ],
            },
            "transaction_id": {
                "type": ["string", "null"],
                "description": "Transaction ID if refund was processed.",
            },
            "escalation_ticket": {
                "type": ["string", "null"],
                "description": "Ticket ID if escalated to human.",
            },
            "summary": {
                "type": "string",
                "description": "One sentence summary of what was done.",
            },
        },
        "required": ["resolved", "summary"],
    },
}