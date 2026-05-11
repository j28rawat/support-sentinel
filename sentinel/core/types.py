"""
sentinel/core/types.py
=======================
Shared data types for the entire SupportSentinel system.

ADDITIVE MODULE:
    New types appended as new days introduce new concepts.
    Existing types never modified (only extended via subclass
    or new fields with defaults).

    Day 1:  AgentResponse    — output of any agentic loop run
    Day 4+: SubAgentResult   — output of coordinator subagents
    Day 8+: EscalationRecord — structured handoff data
"""

from dataclasses import dataclass, field


@dataclass
class AgentResponse:
    """
    Standardised output from any agentic loop run.

    DESIGN DECISION — dataclass over dict:
        Typed fields mean callers know exactly what to expect.
        FastAPI (Day 10) can serialise this directly.
        Tests can make precise field assertions.

    Fields:
        final_response:   The text Claude returns to the customer
        tool_calls:       Ordered list of every tool called + result
        iterations:       How many loop iterations were needed
        resolved:         True if loop ended naturally via end_turn
        escalated:        True if escalate_to_human was called
        escalation_reason: Why escalation was triggered (if applicable)
    """
    final_response: str
    tool_calls: list[dict] = field(default_factory=list)
    iterations: int = 0
    resolved: bool = False
    escalated: bool = False
    escalation_reason: str | None = None

    def tools_used(self) -> list[str]:
        """Return ordered list of tool names called."""
        return [t["tool"] for t in self.tool_calls]

    def was_tool_called(self, tool_name: str) -> bool:
        """Check if a specific tool was called during this run."""
        return tool_name in self.tools_used()