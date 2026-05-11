# Day 1 — Navigation Guide
## Read This Before Opening Any File

---

## 🗺️ The Versioning Contract

Before reading any code, understand this rule — everything
in the project follows it:

    ADDITIVE modules:  Functions appended, never modified.
                       sentinel/core/agentic_loop.py

    VERSIONED modules: New day_XX/ snapshot each day, frozen after.
                       sentinel/tools/day_01/ ← this day's snapshot

    CONSEQUENCE: days/day_01_agentic_loop/exercise.py imports from
                 sentinel.tools.day_01 — it runs correctly forever.

---

## 📖 Reading Order

### 1. Configuration Foundation (5 min)
📄 `sentinel/config/settings.py`

What to find:
- `refund_approval_limit = 500.00` — this value is enforced
  in customer_tools today (description-based) and Day 7 (hooks)
- `CLAUDE_MODEL` — what model runs all your exercises
- The singleton pattern: `settings = Settings()` at bottom

---

### 2. The API Wrapper (10 min)
📄 `sentinel/core/claude_client.py`

What to find:
Read the `tool_choice` comment in the module docstring.
Memorise the three values — they appear on every exam:

    "auto"  → Claude decides (may not call any tool)
    "any"   → Claude must call A tool (picks which)
    {"type": "tool", "name": "X"} → Claude must call X

Why `get_client()` is a factory function, not a global:
Tests mock `get_client()` to avoid real API calls.
A module-level `client = Anthropic()` can't be mocked cleanly.

---

### 3. The Heart (30 min — read every line)
📄 `sentinel/core/agentic_loop.py`

Read the ASCII diagram at the top first.
Then read the function in this order:

3a. The messages list initialisation
    `messages = [{"role": "user", "content": initial_message}]`
    This list IS Claude's memory. It grows by 2 entries per
    tool-calling iteration. By end of Scenario 1: ~8 entries.

3b. The while loop header
    `while iteration < max_iterations:`
    Note: this is the SAFETY NET, not the controller.

3c. The if/elif branches on stop_reason
    `if response.stop_reason == "end_turn":` → done
    `elif response.stop_reason == "tool_use":` → continue

3d. Inside "tool_use" branch — the two critical appends:
    Append 1: `messages.append({"role": "assistant", ...})`
              Claude's response (including tool request)
    Append 2: `messages.append({"role": "user", content: tool_results})`
              Your tool results

    If either append is missing → infinite loop bug.
    Experiment 1 removes Append 2 so you can see this live.

3e. The dependency injection:
    `tool_executor: Callable[[str, dict], str]`
    The loop doesn't import tools. You inject the executor.
    Same loop works for any agent with any tools.

---

### 4. The Types (5 min)
📄 `sentinel/core/types.py`

Find `AgentResponse` and its helper methods:
    `tools_used()` → ordered list of tool names called
    `was_tool_called(name)` → bool check for specific tool

These are used in tests and the result summary table.

---

### 5. Day 1 Tools — Frozen Snapshot (20 min)
📄 `sentinel/tools/day_01/customer_tools.py`

Read each function's docstring.
Notice: descriptions say WHEN TO USE and basic boundaries.
But notice what's MISSING compared to Day 2:
- No explicit WHEN NOT TO USE referencing the alternative tool
- No separate modules (order, refund, shipping all in one file)
- No structured error schema (basic dicts only)

Day 2 fixes all three of these. Running Experiments 1-3
will show you exactly why each fix matters.

---

### 6. The Tool Registry (15 min)
📄 `sentinel/tools/day_01/__init__.py`

Read `ALL_TOOL_DEFINITIONS` — the 5 tool description dicts.
For each one, compare the `description` to the function
docstring in customer_tools.py.
Notice how the description is what Claude reads —
the function docstring is what you read.

Then read `execute_tool()` — the dispatch map.
Note: returns `json.dumps(result)` — strings required.

---

### 7. The Exercise (10 min — read before running)
📄 `days/day_01_agentic_loop/exercise.py`

Read `SCENARIOS` dict — understand what each scenario tests.
Read `print_result_summary()` — understand the output table.
Then run: `python days/day_01_agentic_loop/exercise.py`

---

## 🧪 Experiments (Do These — They Teach More Than Reading)

### Experiment 1 — Break the append (5 min)
In `sentinel/core/agentic_loop.py`:
Comment out: `messages.append({"role": "user", "content": tool_results})`
Run Scenario 1. Watch Claude call get_customer 10 times.
This is the most common beginner mistake AND a favourite exam trap.
Restore the line.

### Experiment 2 — Vague descriptions (5 min)
In `sentinel/tools/day_01/__init__.py`:
Change lookup_order description to: `"Gets order information"`
Change get_order_history description to: `"Gets order info for customer"`
Run Scenario 3 (James, no order ID). Watch misrouting.
Restore descriptions.

### Experiment 3 — Iteration cap as controller (5 min)
In `sentinel/core/agentic_loop.py`:
Change `max_iterations=10` to `max_iterations=2`.
Run Scenario 1. Agent cuts off mid-resolution.
This is why caps are safety nets, not controllers.
Restore.

---

## 🔗 What Gets Extended in Future Days

| Today's file | Extended in | What changes |
|---|---|---|
| `agentic_loop.py` | Day 4 | Coordinator variant added |
| `agentic_loop.py` | Day 7 | Hook-intercepted variant added |
| `tools/day_01/` | Day 2 | New snapshot with 9 tools, structured errors |
| `prompts.py` | Day 4 | Coordinator + subagent prompts appended |
| `types.py` | Day 4 | SubAgentResult type appended |
| `settings.py` | Day 7 | Hook config settings appended |

---

## ✅ Ready for Day 2 When...

- [ ] `pytest tests/test_day_01.py -v` — all tests pass
- [ ] All 3 scenarios run without errors
- [ ] Experiment 1 shows the infinite loop bug
- [ ] Experiment 2 shows misrouting with vague descriptions
- [ ] You can draw the agentic loop flowchart from memory
- [ ] You can explain the two critical appends and why each matters