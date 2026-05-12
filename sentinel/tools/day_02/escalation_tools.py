"""
sentinel/tools/day_02/escalation_tools.py
============================================
Human escalation and ticket creation.

FROZEN: Do not modify after Day 2 is complete.

EXAM CRITICAL — Task Statement 5.2:

WHEN TO ESCALATE (explicit criteria):
    ✓ Customer explicitly requests a human agent
    ✓ Refund amount exceeds auto-approval limit ($500)
    ✓ Business policy is ambiguous or silent on the issue
    ✓ Agent cannot make meaningful progress after investigation
    ✓ Any tool returns requires_escalation=True

WHEN NOT TO ESCALATE:
    ✗ Customer is frustrated — offer to resolve first,
      escalate only if they reiterate preference for human
    ✗ Case seems complex — complexity alone is not a trigger
    ✗ Agent is uncertain — investigate before escalating
    ✗ Sentiment-based signals — explicitly an anti-pattern

EXAM TRAP:
    Sentiment-based escalation and self-reported confidence
    scores are BOTH listed as unreliable proxies in the exam.
    Explicit criteria + few-shot examples is the correct approach.
    Day 8 adds few-shot examples to the escalation system prompt.

STRUCTURED HANDOFF (Task Statement 1.4):
    Human agents often lack access to the AI conversation.
    Every escalation must include complete context so the
    human does not ask the customer to repeat themselves.
    Required fields: customer_id, issue_summary,
    investigation_summary, recommended_action, escalation_reason.
"""

import json
import random
from datetime import datetime


def escalate_to_human(
    customer_id: str,
    issue_summary: str,
    investigation_summary: str,
    recommended_action: str,
    escalation_reason: str,
) -> dict:
    """
    Transfer case to a human agent with full structured handoff.

    WHEN TO USE:
        Customer explicitly requests a human agent.
        Refund exceeds $500 auto-approval limit.
        Policy is ambiguous or does not cover this situation.
        Cannot resolve after thorough investigation.
        Any tool returns requires_escalation=True.

    WHEN NOT TO USE:
        Customer is frustrated but issue is within agent capability.
        Offer to resolve first — escalate only if they insist.
        Agent is uncertain — investigate more before escalating.

    PARAMETERS:
        customer_id:           Human agent needs this to pull account
        issue_summary:         What the customer wants (1-2 sentences)
        investigation_summary: What was already checked and tried
        recommended_action:    What the human agent should do next
        escalation_reason:     Specific reason WHY escalating

    RETURNS:
        ticket_id and estimated wait time for the customer.

    EXAM NOTE:
        All 5 parameters are required. Missing investigation_summary
        means the human agent starts from scratch — a poor customer
        experience. Every parameter has a specific purpose.
    """
    ticket_id = f"TKT-{random.randint(10000, 99999)}"
    timestamp = datetime.now().isoformat()

    # Build structured handoff record
    # In production: write to Zendesk / ServiceNow / ticketing DB
    handoff = {
        "ticket_id": ticket_id,
        "timestamp": timestamp,
        "customer_id": customer_id,
        "issue_summary": issue_summary,
        "investigation_summary": investigation_summary,
        "recommended_action": recommended_action,
        "escalation_reason": escalation_reason,
        "priority": _determine_priority(escalation_reason),
    }

    # Print handoff for visibility during exercises
    print(
        f"\n{'─'*50}"
        f"\n[ESCALATION HANDOFF — {ticket_id}]"
        f"\n{json.dumps(handoff, indent=2)}"
        f"\n{'─'*50}\n"
    )

    return {
        "error": False,
        "escalated": True,
        "ticket_id": ticket_id,
        "priority": handoff["priority"],
        "estimated_wait_minutes": 8,
        "message": (
            f"I've connected you with a team member who can help. "
            f"Your reference number is {ticket_id}. "
            f"Estimated wait: 5-10 minutes. "
            f"They will have full context from our conversation."
        ),
    }


def _determine_priority(escalation_reason: str) -> str:
    """Assign ticket priority based on escalation reason keywords."""
    high_priority_keywords = [
        "refund", "payment", "fraud", "lost",
        "urgent", "manager", "complaint",
    ]
    if any(
        kw in escalation_reason.lower()
        for kw in high_priority_keywords
    ):
        return "high"
    return "normal"