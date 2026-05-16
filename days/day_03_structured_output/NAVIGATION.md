# Day 3 — Navigation Guide
## Read This Before Opening Any File

---

## 🗺️ What Gets Built Today

    sentinel/extraction/   ← New production module
    sentinel/tools/day_03/ ← New frozen snapshot (10 tools)

    sentinel/tools/day_01/ ← FROZEN — untouched
    sentinel/tools/day_02/ ← FROZEN — untouched

---

## 📖 Reading Order

### 1. Read First — The Schema
📄 `sentinel/extraction/schemas.py`

Read the module docstring. Find this distinction:

    tool_use guarantees: syntax, required fields, enum values
    tool_use does NOT guarantee: semantic correctness

Find INCIDENT_SCHEMA. For each field, notice:
- Required fields: always populated by Claude
- Nullable fields: ["string", "null"] — Claude returns null
  when data is absent

Find amount_mentioned:
    "type": ["number", "null"]
    NOT "type": "number"

If it were required with type "number", Claude would
hallucinate an amount when none is mentioned.
Making it nullable and optional prevents this entirely.

Find the "other" + detail pattern:
    issue_type enum includes "other"
    issue_type_detail field handles the detail
This is the extensible categorisation pattern — you capture
unknown issue types without losing the information.

---

### 2. The Extractor
📄 `sentinel/extraction/incident_extractor.py`

Read the module docstring. Find:
    tool_choice = {"type": "tool", "name": "extract_incident"}

This is FORCED selection. Not "auto" (may return text).
Not "any" (picks which tool). FORCED to call exactly this tool.

Find _build_prompt() — the few-shot injection pattern:
    Examples come BEFORE the target message.
    This is standard few-shot ordering.
    Claude reads examples, applies pattern to new input.

Find _build_retry_prompt() — retry with error feedback:
    Original message included (Claude needs context)
    Specific error included (what to fix)
    Attempt number shown (Claude knows it's a retry)
    Compare this to blind retry: same prompt repeated.

Find _parse_tool_response():
    response.content is a list of blocks
    Find block where block.type == "tool_use"
    Extract block.input — this is your structured data

Find _validate():
    This is semantic validation — not schema validation.
    Schema already guarantees: correct types, required fields.
    We check: positive amounts, non-empty arrays,
    conditional requirements (other → detail required).

---

### 3. The Validator
📄 `sentinel/extraction/validator.py`

Find is_retry_worthwhile(). Read both pattern lists:
    retryable_patterns:     format/structural errors
    non_retryable_patterns: missing data errors

The exam tests this distinction directly:
"Retries are ineffective when the required information
is simply absent from the source document."
(Task Statement 4.4)

A format error (amount as "$299" not 299.0) → retry.
Missing information (no order ID mentioned) → don't retry,
the order ID won't appear on the next attempt.

---

### 4. Day 3 Tool Registry
📄 `sentinel/tools/day_03/__init__.py`

Notice the import pattern:
    from sentinel.tools.day_02 import (
        ALL_TOOL_DEFINITIONS as DAY_02_TOOLS,
        execute_tool as day_02_execute_tool,
    )

Day 3 does NOT copy Day 2 files. It imports them.
This is different from Day 2 which created new files.
We extend — we don't duplicate.

Find EXTRACTION_TOOL_DEFINITION — the new tool.
Its description says WHEN TO USE ("at the start of any
support conversation") and WHEN NOT TO USE ("after already
extracting data this session") — the Day 2 pattern applied.

Find execute_tool():
    if tool_name == "extract_incident": → use extraction pipeline
    else: → delegate to day_02_execute_tool
Clean routing. No duplication.

---

### 5. Run the Exercise
📄 `days/day_03_structured_output/exercise.py`

Run Part 1 first. Observe:
- Which fields are populated vs null
- Whether the JSON is perfectly structured every time
- extraction_confidence value

Run Part 2. Compare with/without few-shot:
- Do nullable fields return null or hallucinated values?
- Is urgency classified consistently?
- Are key_facts formatted the same way?

Run Part 3. Look for retry behaviour:
- Does the retry prompt include the specific error?
- Does Claude correct the specific issue on retry?

Run Part 4. Observe tool_choice:
- Does "auto" always call the tool?
- Does "any" call the extraction tool or something else?
- Does forced always call extract_incident?

---

## 🧪 Experiments

### Experiment 1 — Remove nullable from amount
In schemas.py, change:
    "type": ["number", "null"]
to:
    "type": "number"
Run Part 2 (ambiguous message, no amount mentioned).
Watch Claude hallucinate an amount to satisfy the required field.
Restore after observing.

### Experiment 2 — No few-shot vs few-shot (already in Part 2)
Part 2 does this for you. But also try running Part 1
with use_few_shot=False and compare the key_facts format.
Without examples, key_facts may be verbose sentences.
With examples, key_facts are short phrases.

### Experiment 3 — Blind retry vs feedback retry
In incident_extractor.py, change _build_retry_prompt to
return the same prompt as _build_prompt (remove the error).
Run Part 3. Observe whether the same error repeats.
Restore after observing.

---

## 🔗 What Gets Extended in Future Days

| Today's file | Extended in | What changes |
|---|---|---|
| `schemas.py` | Day 4 | RESOLUTION_SCHEMA used by report_agent |
| `incident_extractor.py` | Day 5 | Context-aware extraction added |
| `tools/day_03/__init__.py` | Day 4 | Scoped subsets given to subagents |
| `prompts.py` few-shot | Day 8 | Escalation few-shot added same pattern |

---

## ✅ Ready for Day 4 When...

- [ ] pytest tests/test_day_03.py -v — all pass
- [ ] All 4 prior test files still pass
- [ ] Part 1 produces clean structured JSON
- [ ] Part 2 shows difference between few-shot and no few-shot
- [ ] Part 4 shows forced always calls extract_incident
- [ ] You can explain why nullable prevents hallucination
- [ ] You can explain when retries work vs when they don't
- [ ] You ran Experiment 1 and saw hallucinated amount

### Observed behaviour — content block types

Part 4 revealed an important production pattern:
`response.content` is a list of mixed block types.
`content[0]` is NOT always a tool_use block.

When tool_choice="auto" and Claude returns text:
    content[0] → TextBlock (has .text, no .name)

When tool_choice="any" or forced:
    content[0] → ToolUseBlock (has .name, .input, .id)

Always search for tool blocks explicitly:
    tool_block = next(
        (b for b in response.content if b.type == "tool_use"),
        None
    )

Never use content[0].name — it will crash on TextBlock.
This is a favourite source of AttributeError in production.