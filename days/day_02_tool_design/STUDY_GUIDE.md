# Day 2 — Study Guide & Exam Preparation
## Tool Design & MCP Integration

---

## 📚 Key Concepts Covered Today

### 1. Tool Descriptions Are Routing Instructions
Not documentation for humans — instructions to the model.
Claude reads descriptions to decide which tool to call.
A vague description is a routing bug.

Three things every description must contain:
    What it returns (specific fields, not vague "information")
    WHEN TO USE (trigger condition)
    WHEN NOT TO USE (boundary — names the alternative)

### 2. The Four Error Categories

| Category | is_retryable | Claude's Action |
|---|---|---|
| transient | True | Retry after brief wait |
| validation | False | Fix the input, don't retry |
| business | False | Explain policy to customer |
| permission | False | Escalate to human |

### 3. Empty Result ≠ Error (Exam Critical)

    # ✅ Correct — no orders found
    {"error": False, "orders": [], "order_count": 0}

    # ❌ Wrong — causes unnecessary retries
    {"error": True, "message": "No orders found"}

Empty result = valid query, no data.
Access failure = service down, may have data.
These require completely different responses from Claude.

### 4. Prerequisite Chain

    get_customer → check_refund_eligibility → process_refund

    Day 2: description-enforced (probabilistic)
    Day 7: programmatic hooks (deterministic)

    For financial operations, probabilistic is insufficient.

### 5. Escalation Criteria — Explicit Not Sentiment

    ✓ Customer explicitly requests human
    ✓ Amount exceeds auto-approval limit
    ✓ Policy ambiguous or silent
    ✓ Cannot resolve after investigation
    ✗ Customer is frustrated (not a trigger)
    ✗ Agent is uncertain (not a trigger)

### 6. Structured Handoff — Why All 5 Fields Required

    customer_id:           Human pulls up account
    issue_summary:         What customer wants
    investigation_summary: What was already tried
    recommended_action:    What human should do
    escalation_reason:     WHY escalating

    Missing any field = human starts from scratch.

### 7. Tool Scoping (Preview of Day 4)

    Too many tools → degraded selection reliability.
    Recommended: 4-5 tools per agent.
    Day 4: each subagent receives only its relevant tools.
    Today: all 9 tools on one agent (baseline).

---

## 📝 Exam Questions — Day 2

---

**Q1.** Your agent frequently calls `lookup_order` when customers
say "my order" without providing an order ID. Both `lookup_order`
and `get_order_history` have the description "Gets order
information." What is the MOST effective first fix?

A) Remove `lookup_order` from the tool list entirely

B) Add a system prompt instruction: "Call get_order_history
   when customer has not provided an order ID"

C) Expand both tool descriptions with explicit WHEN TO USE
   and WHEN NOT TO USE boundaries that reference each other

D) Merge both tools into one `get_order_data` tool

**✅ Answer: C**

Tool descriptions are the primary mechanism Claude uses for
tool selection. When two descriptions are identical or near-
identical, Claude cannot distinguish between them. Adding
explicit boundaries ("WHEN NOT TO USE: Customer has provided
an order ID — use lookup_order instead") gives Claude the
signal it needs at selection time.

Option B (system prompt) is less reliable — descriptions
are the selection signal, not the system prompt.
Options A and D are architectural changes that don't fix
the underlying description problem.

---

**Q2.** `search_customers` is called for a customer who has
never registered. Which response is correct?

A) `{"error": True, "message": "Customer not found"}`

B) `{"error": False, "matches": [], "match_count": 0,
    "message": "No customers found matching criteria"}`

C) Raise `CustomerNotFoundError` exception

D) `{"error": True, "error_category": "validation",
    "is_retryable": False}`

**✅ Answer: B**

An empty search result is a VALID outcome — no matching
customer exists. This is NOT an error. Marking it error=True
would cause Claude to retry a query that will never succeed,
or to escalate unnecessarily.

This distinction — empty result vs access failure — is
directly tested in Task Statements 2.2 and 5.3.
The only time to return error=True is when the service
failed (transient) or input was invalid (validation),
not when the query succeeded with zero results.

---

**Q3.** `process_refund` is called with $650, exceeding the
$500 limit. Which structured error response is correct?

A) `{"error": True, "error_category": "transient",
    "is_retryable": True}`

B) `{"error": True, "error_category": "business",
    "is_retryable": False, "requires_escalation": True,
    "message": "Refunds over $500 require manager approval..."}`

C) `{"error": True, "error_category": "permission",
    "is_retryable": False, "requires_escalation": True}`

D) Process the refund silently and log a warning

**✅ Answer: B**

A policy limit is a business error — a rule prevents the
operation, not a technical failure or access rights issue.
is_retryable=False because the policy will not change
between retries. requires_escalation=True signals Claude
to call escalate_to_human next.

Option A (transient) would cause Claude to retry.
Option C (permission) is wrong category — the agent has
permission in principle but the amount exceeds policy.
Option D bypasses the business rule entirely.

---

**Q4.** Your support agent has access to 15 tools.
Production logs show frequent wrong-tool selection despite
detailed descriptions. What is the most effective fix?

A) Improve all 15 descriptions further

B) Add a system prompt listing all 15 tools and when to use each

C) Distribute tools across specialised subagents — each
   receiving only the 4-5 tools relevant to its role

D) Consolidate all 15 tools into 3 general-purpose tools

**✅ Answer: C**

Task Statement 2.3: giving an agent too many tools degrades
selection reliability by increasing decision complexity.
The correct pattern is scoped tool access — each specialised
subagent receives only tools relevant to its role.

Option A has diminishing returns beyond a certain count.
Option B adds more tokens without solving cognitive load.
Option D creates ambiguous mega-tools — a different problem.

---

**Q5.** When should `escalate_to_human` be called IMMEDIATELY,
without attempting to resolve first?

A) When the customer's tone is frustrated or angry

B) When the agent is uncertain about the correct resolution

C) When the customer explicitly requests a human agent

D) When the case involves more than two tool calls

**✅ Answer: C**

Task Statement 5.2: "Honoring explicit customer requests for
human agents immediately without first attempting investigation."

An explicit request IS the escalation trigger. Investigating
first (frustrated tone, uncertain agent, complex case) all
violate this principle.

Options A and B are explicitly identified as unreliable
proxies in the exam guide. Sentiment-based and confidence-
based escalation are both anti-patterns.

---

**Q6.** What is the key difference between a `business`
error and a `permission` error?

A) Business errors are retryable; permission errors are not

B) Business errors relate to policy limits a human agent
   can override; permission errors relate to access rights
   requiring system-level changes

C) Business errors always require escalation

D) There is no meaningful difference — both trigger escalation

**✅ Answer: B**

Both are non-retryable, but they signal different paths:

business: Policy limit hit (e.g., refund >$500). A human
agent with manager access CAN override this in the same
support workflow. requires_escalation may be True or False.

permission: Access rights denied entirely. May require
admin intervention beyond standard support capability.
requires_escalation is always True.

Option C is wrong — some business errors just explain
policy to the customer (no escalation needed).

---

**Q7.** Your `track_shipment` description says "Get shipment
information." A customer asks "what items were in my order?"
and Claude calls `track_shipment` instead of `lookup_order`.
What is the root cause?

A) The agentic loop is not appending tool results correctly

B) tool_choice should be set to "any" to force correct selection

C) "Get shipment information" overlaps conceptually with
   order information — the description needs explicit WHEN NOT
   TO USE boundaries referencing lookup_order

D) Shipping tools should be removed from the agent entirely

**✅ Answer: C**

"Get shipment information" and "get order information" are
conceptually adjacent without explicit boundaries.
The fix is to add:
"WHEN NOT TO USE: Order status questions about items or
amounts — use lookup_order. Tracking and order status
are different concepts."

Option A is a loop bug — unrelated to this problem.
Option B forces a tool call but doesn't fix routing.
Option D is too aggressive — tracking is still needed.

---

**Q8.** Why does `escalate_to_human` require
`investigation_summary` as a mandatory parameter?

A) To satisfy a required field in the Anthropic tool schema

B) Human agents receiving escalated tickets often lack access
   to the AI conversation and need complete context to avoid
   asking the customer to repeat everything

C) To ensure the ticket has enough content for SLA compliance

D) It is optional — the human can pull up the conversation log

**✅ Answer: B**

Task Statement 1.4: structured handoff protocols for mid-
process escalation must include enough context for the
receiving agent to act without starting from scratch.

In most production systems, AI conversations exist in one
system while support tickets exist in another. They are not
automatically linked. Missing investigation_summary means
the customer must repeat their entire issue to a new person.

Every parameter in escalate_to_human prevents a specific
failure mode in the human handoff.

---

**Q9.** `get_order_history` returns an empty list for a
customer who has never placed an order. A junior developer
says this should return error=True so Claude knows
"nothing was found." What is wrong with this reasoning?

A) Nothing — error=True for empty results is correct practice

B) error=True would cause Claude to treat a successful query
   with no results as a failure — triggering retries or
   escalation for a normal situation that needs neither

C) error=True is only wrong if is_retryable is also True

D) The error field is optional and can be omitted

**✅ Answer: B**

A customer having no orders is a completely normal and valid
situation. Marking it error=True confuses two fundamentally
different states:

Valid empty result: query succeeded, no data exists.
  → error=False, orders=[], no retry needed

Access failure: query failed due to service issue.
  → error=True, error_category=transient, is_retryable=True

Claude uses the error field to decide its next action.
Mislabelling a valid empty result as an error causes
unnecessary retries, unnecessary escalations, and confuses
the agent's reasoning about what actually happened.

---

**Q10.** What is the MOST reliable way to ensure Claude calls
`check_refund_eligibility` before `process_refund`?

A) System prompt instruction: "Always check eligibility first"

B) process_refund tool description: "PREREQUISITES: call
   check_refund_eligibility first"

C) Both A and B together — layered prompt guidance

D) A programmatic prerequisite gate that blocks process_refund
   from being available until eligibility is confirmed, combined
   with description-based guidance

**✅ Answer: D**

For financial operations, prompt instructions (A, B, C) are
probabilistic — they have a non-zero failure rate. The exam
explicitly states this for Task Statement 1.4.

A programmatic gate provides deterministic enforcement.
Combined with descriptions (so Claude understands WHY),
you get both reliability and comprehension.

We implement this in Day 7 using hooks. Today's descriptions
are the probabilistic foundation. Day 7 makes it deterministic.

---

**Q11.** A `service_unavailable_error` and a `not_found_error`
both return `error=True`. What distinguishes how Claude should
respond to each?

A) Nothing — both should trigger an immediate escalation

B) service_unavailable has is_retryable=True (transient failure,
   try again); not_found has is_retryable=False (record genuinely
   absent, trying again will not help)

C) not_found should trigger escalation; service_unavailable
   should not

D) Both should be retried exactly once before escalating

**✅ Answer: B**

The is_retryable field is specifically designed to distinguish
these two cases:

service_unavailable (transient): The service is temporarily
down. The record MAY exist. Retrying may succeed.
is_retryable=True → Claude should retry.

not_found (validation): The record genuinely does not exist.
Retrying the same query will return the same result.
is_retryable=False → Claude should not retry.

Without this distinction, Claude either retries everything
(wasteful) or retries nothing (misses recoverable failures).

---

**Q12.** In the Day 2 exercise, Parts 1 and 2 use identical
Python tool implementations but different description strings.
What does this demonstrate about the relationship between
tool implementation and tool selection?

A) Tool selection is determined by the Python function signature

B) Tool selection is determined entirely by the description
   string Claude reads — implementation has no effect on
   which tool gets called

C) Longer descriptions always lead to better tool selection

D) Tool selection is random when implementations are similar

**✅ Answer: B**

Claude never sees your Python code. It only sees:
- The tool name
- The tool description
- The input schema

Two tools can have identical implementations and radically
different routing behaviour based solely on their descriptions.

This is why the exercise runs VAGUE_TOOL_DEFINITIONS and
ALL_TOOL_DEFINITIONS with the same execute_tool() function.
The function code is irrelevant to routing.
The description is everything.

---

**Q13.** When a tool returns `requires_escalation=True`,
what should Claude do next?

A) Immediately end the conversation and return an error
   to the customer

B) Retry the tool call with different parameters

C) Call `escalate_to_human` with complete investigation summary
   as the next action

D) Ask the customer if they would prefer a human agent before
   escalating

**✅ Answer: C**

requires_escalation=True is an explicit signal from the tool
layer that this situation needs a human. Claude should act
on it immediately by calling escalate_to_human with:
- What the customer wanted (issue_summary)
- What was already investigated (investigation_summary)
- What the human should do (recommended_action)
- Why escalating (escalation_reason — be specific)

Option D introduces unnecessary friction — the tool has
already determined escalation is required (e.g., refund
exceeds limit). Asking the customer for permission to follow
a mandatory business rule is incorrect.

---

## 🧠 Quick-Fire Revision

| Q | A |
|---|---|
| What are the 4 error categories? | transient, validation, business, permission |
| Which is the only retryable category? | transient |
| Empty result → error=True or False? | False — valid empty result |
| What must every description include? | Returns + WHEN TO USE + WHEN NOT TO USE |
| Explicit escalation trigger #1? | Customer explicitly requests human |
| What does requires_escalation=True signal? | Call escalate_to_human next |
| Recommended tools per agent? | 4-5 scoped to the agent's role |
| Prerequisite chain today vs Day 7? | Descriptions (probabilistic) vs hooks (deterministic) |
| Sentiment-based escalation: reliable? | No — explicitly an anti-pattern |
| 5 required fields of escalate_to_human? | customer_id, issue_summary, investigation_summary, recommended_action, escalation_reason |

---

## ✅ Readiness Check — Before Day 3

Complete without notes:
1. Name the four error categories and their is_retryable values
2. Explain why empty result ≠ error with a concrete example
3. Write the WHEN TO USE / WHEN NOT TO USE pattern for
   lookup_order and get_order_history from memory
4. Explain why Day 2's prerequisite enforcement is insufficient
   for financial operations (and what Day 7 fixes)
5. Name the 5 escalation triggers and 2 non-triggers
6. Answer Q1-Q13 without looking at explanations
7. Run at least one experiment and explain what you observed