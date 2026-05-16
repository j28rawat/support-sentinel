"""
sentinel/tools/day_03/__init__.py
====================================
Tool registry — Day 3 frozen snapshot.

FROZEN: Do not modify after Day 3 is complete.

CHANGES FROM DAY 2:
    + extract_incident tool added — wraps the extraction pipeline
      so Claude can call it as part of the support workflow

INHERITED FROM DAY 2 (imported, not copied):
    All 9 tools from sentinel.tools.day_02 unchanged.
    Re-exporting them here keeps day_03 self-contained.

VERSIONING NOTE:
    days/day_03_structured_output/exercise.py imports from HERE.
    days/day_01 and day_02 exercises are completely unaffected.
"""

import json

# ── Import all Day 2 tools ────────────────────────────────────────────────────
from sentinel.tools.day_02 import (
    ALL_TOOL_DEFINITIONS as DAY_02_TOOLS,
    execute_tool as day_02_execute_tool,
)

# ── Import Day 3 extraction pipeline ─────────────────────────────────────────
from sentinel.extraction import IncidentExtractor

# ── Day 3 new tool definition ─────────────────────────────────────────────────
EXTRACTION_TOOL_DEFINITION = {
    "name": "extract_incident",
    "description": (
        "Extract structured incident data from a raw customer message. "
        "Returns customer_id, order_id, issue_type, urgency, sentiment, "
        "and key_facts. "
        "WHEN TO USE: At the start of any support conversation to "
        "understand the customer's issue before taking action. "
        "The extracted data guides which tools to call next. "
        "WHEN NOT TO USE: After already extracting data in this session."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The raw customer message to extract from",
            }
        },
        "required": ["message"],
    },
}

# ── Combined tool set for Day 3 ───────────────────────────────────────────────
ALL_TOOL_DEFINITIONS = DAY_02_TOOLS + [EXTRACTION_TOOL_DEFINITION]


# ── Tool executor ─────────────────────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict) -> str:
    """
    Route tool calls — Day 3 tools + all Day 2 tools.

    New tool: extract_incident
    All Day 2 tools delegated to day_02_execute_tool.
    """
    if tool_name == "extract_incident":
        extractor = IncidentExtractor(use_few_shot=True)
        result = extractor.extract(tool_input["message"])
        return json.dumps(result.to_dict(), default=str)

    # Delegate all other tools to Day 2 executor
    return day_02_execute_tool(tool_name, tool_input)