# Day 2 — Navigation Guide
## Read This Before Opening Any File

---

## 🗺️ The Versioning Contract in Action

Before reading any Day 2 code, confirm this:

    sentinel/tools/day_01/  ← FROZEN. Nothing changed here.
    sentinel/tools/day_02/  ← NEW snapshot built today.

    days/day_01_agentic_loop/exercise.py still imports from
    sentinel.tools.day_01 and runs identically to Day 1.
    Open it and check the import line if you want to verify.

---

## 📖 Reading Order

### 1. Read First — The Error Foundation
📄 `sentinel/tools/day_02/error_schemas.py`

Read the module docstring. Find the table of four categories.
Then read each constructor function — notice what changes:

    not_found_error         is_retryable=False  (validation)
    service_unavailable     is_retryable=True   (transient)
    business_rule_error     is_retryable=False  (business)
    permission_error        is_retryable=False  (permission)

Key distinction to memorise:

    not_found_error     → record doesn't exist (don't retry).
    service_unavailable → service is down (do retry).
    Both return error=True, but for completely different reasons.
    Claude uses error_category to distinguish them.

Find the EXAM TRAP comment about empty results vs errors.
This is tested in both Task Statement 2.2 and 5.3.

---

### 2. The Boundary Pattern — Two Customer Tools
📄 `sentinel/tools/day_02/customer_tools.py`

Read the WHEN TO USE and WHEN NOT TO USE for both functions.
Find where each description explicitly names the other tool:

    get_customer:      "WHEN NOT TO USE: use search_customers"
    search_customers:  "WHEN NOT TO USE: use get_customer"

This cross-referencing is what prevents misrouting.
Without it, Claude has no signal to choose between them.

```
Find the empty search result return:
    error=False, matches=[], match_count=0
This is NOT an error. A customer not being found is a valid
outcome, not a failure. Marking it error=True would cause
Claude to retry a query that will never succeed.
```

---

### 3. The Separation Pattern — Order Tools
📄 `sentinel/tools/day_02/order_tools.py`

Read the module docstring — specifically WHY two tools
instead of one merged tool.

Then read both descriptions focusing on the boundary:

    lookup_order:      "WHEN NOT TO USE: use get_order_history"
    get_order_history: "WHEN NOT TO USE: use lookup_order"

```
Find get_order_history's empty result:
    error=False, orders=[], order_count=0
Same pattern as search_customers — valid empty, not an error.
```

---

### 4. The Prerequisite Chain — Refund Tools
📄 `sentinel/tools/day_02/refund_tools.py`

Read the module docstring. Find this section:

    TODAY (Day 2): Description-based enforcement (probabilistic)
    DAY 7:         Programmatic enforcement (deterministic)

This is the most important thing to understand in Day 2.
You will experience the probabilistic version running today.
Day 7 will show you why that's insufficient for financial ops.

```
Find process_refund's business rule check:
    if amount > settings.refund_approval_limit:
        return business_rule_error(..., requires_escalation=True)
```

The requires_escalation=True flag is what tells Claude to
call escalate_to_human next. Claude reads this flag and
routes appropriately — this is structured error recovery
in action.

---

### 5. The Scoping Pattern — Shipping Tools
📄 `sentinel/tools/day_02/shipping_tools.py`

Read the module docstring. Find the explanation of why
shipping tools are separated from order tools.

```
Find track_shipment's description:
    "WHEN NOT TO USE: Order status questions — use lookup_order.
     Refund questions — use refund tools."
```

This tool explicitly redirects to other tools for adjacent
but different use cases. Three-way disambiguation.

Find _resolve_tracking_dates() — the same offset system
used for orders is applied to tracking events.

---

### 6. Escalation Design — Escalation Tools
📄 `sentinel/tools/day_02/escalation_tools.py`

```
Read the module docstring. Find the explicit criteria table:
    ✓ Customer explicitly requests human
    ✓ Refund exceeds limit
    ✓ Policy is ambiguous
    ✗ Customer is frustrated (NOT a trigger)
    ✗ Case seems complex (NOT a trigger)
```

Find the five required parameters of escalate_to_human.
Understand why each one exists:

    customer_id:           Human pulls up the account
    issue_summary:         What customer wants
    investigation_summary: What was already tried
    recommended_action:    What human should do
    escalation_reason:     WHY escalating (specific)

Missing investigation_summary means the human asks the
customer to repeat everything. Every parameter prevents
a specific failure mode.

---

### 7. The Central Registry — Most Important Read
📄 `sentinel/tools/day_02/__init__.py`

This is the most important file in Day 2.

Read ALL_TOOL_DEFINITIONS and VAGUE_TOOL_DEFINITIONS
side by side for the same tools.

```
Example — lookup_order:

VAGUE:
    "Gets order information."

RICH:
    "Retrieve complete details for ONE specific order by its ID
    (format: ORD-#####). Returns status, line items, total amount,
    order_date, delivery_date, days_since_delivery,
    within_return_window.
    WHEN TO USE: Customer provides a specific order ID.
    WHEN NOT TO USE: Customer says 'my order' without an ID —
    use get_order_history to find which order they mean."
```

Same tool. Same implementation. Completely different
routing reliability. This is the exam's core lesson.

---

### 8. Run and Observe — The Exercise
📄 `days/day_02_tool_design/exercise.py`

Run Part 1 first. With vague descriptions and customer C002
(no order ID provided), watch what Claude calls.
Expected: get_order_history
Possible with vague: lookup_order (can't tell them apart)

Then run Part 2. Same message. Same tools. Rich descriptions.
Claude should now correctly call get_order_history.

Then run Part 3. Watch Claude route to escalate_to_human
based on the business error from process_refund.
This is structured error recovery, not generic failure handling.

---

## 🧪 Experiments

### Experiment 1 — Make descriptions identical
In sentinel/tools/day_02/__init__.py, change lookup_order
description to exactly match get_order_history:
    "Gets order information for a customer."
Run exercise Part 1. Claude now cannot distinguish between them.
Restore after observing.

### Experiment 2 — Remove is_retryable from business error
In error_schemas.py, change business_rule_error to
is_retryable=True. Run exercise Part 3. Observe whether
Claude attempts to retry the refund or escalates.
Restore after observing.

### Experiment 3 — Make empty result an error
In order_tools.py, change get_order_history to return
error=True when orders list is empty. Run a scenario with
customer C999 (no orders). Watch Claude retry or escalate
for what should be a valid empty result.
Restore after observing.

---

## 🔗 What Gets Extended in Future Days

| Today's file | Extended in | What changes |
|---|---|---|
| `error_schemas.py` | Day 5 | Error propagation across agents |
| `refund_tools.py` prerequisite | Day 7 | Hooks enforce deterministically |
| `escalation_tools.py` criteria | Day 8 | Few-shot examples added to prompt |
| Tool modules (all 6) | Day 4 | Scoped subsets given to each subagent |
| `VAGUE_TOOL_DEFINITIONS` | Never | Frozen as a teaching artifact |

---

## ✅ Ready for Day 3 When...

- [ ] pytest tests/test_day_02.py -v — all tests pass
- [ ] pytest tests/test_day_01.py -v — still passes (contract)
- [ ] Part 1 shows different tool selection than Part 2
- [ ] Part 3 shows Claude calling escalate_to_human
- [ ] You can name the four error categories from memory
- [ ] You can explain why empty result ≠ error
- [ ] You ran at least one experiment and understood the result