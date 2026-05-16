# Day 3 — Study Guide & Exam Preparation
## Prompt Engineering & Structured Output

---

## 📚 Key Concepts Covered Today

### 1. tool_use + JSON Schema = Most Reliable Structured Output

    tool_use guarantees (syntax-level):
        ✓ Valid JSON — no markdown fences, no syntax errors
        ✓ Required fields always present
        ✓ Enum values from allowed list only
        ✓ Correct types (string, number, array)

    tool_use does NOT guarantee (semantic-level):
        ✗ Values in correct fields
        ✗ Amounts matching context
        ✗ Contradictory data caught
        These require code validation.

### 2. tool_choice — Three Values

| Value | Behaviour | Use When |
|---|---|---|
| `"auto"` | Claude decides — may return text | Default |
| `"any"` | Must call a tool, picks which | Need any tool call |
| `{"type":"tool","name":"X"}` | Must call tool X | Force specific extraction |

For structured output: always use forced selection.
"any" guarantees a tool call but not the right schema.

### 3. Nullable Fields Prevent Hallucination

    # ✅ Correct — Claude returns null when absent
    "customer_id": {"type": ["string", "null"]}

    # ❌ Wrong — Claude hallucinated "C000" to satisfy required
    "customer_id": {"type": "string"}

    Required field + absent data = hallucinated value.
    Nullable field + absent data = explicit null.
    null is always better than a wrong value.

### 4. Few-Shot Examples — Most Effective for Consistency

    When instructions alone produce inconsistent output:
    - Inconsistent key_facts format (sentences vs phrases)
    - Inconsistent urgency classification
    - Inconsistent null vs inferred values

    Few-shot examples demonstrate:
    - Exact output format
    - How to handle missing data (null)
    - Edge case classification
    - Key_facts as short phrases not sentences

    Include 2-4 examples covering common cases + edge cases.

### 5. Retry with Error Feedback

    Blind retry:    "Please try again"
    Feedback retry: "amount_mentioned must be a number.
                    Got: '$299.99'. Return 299.99 instead."

    Feedback retries are MORE effective for format errors.

    Retries are NOT effective for missing data:
    - Source document doesn't mention the order ID
    - Retrying won't make the order ID appear
    - Identify this limit to avoid wasted API calls

### 6. The "other" + Detail Pattern

    Enum fields with "other" + a detail string field:
        issue_type: "other"
        issue_type_detail: "Customer requesting gift wrap"

    Why: Closed enums miss unknown cases.
         "other" captures them without losing information.
         The detail field preserves the specifics.

### 7. Syntax vs Semantic Errors

    Syntax errors  → eliminated by tool_use
    Semantic errors → require your validation code

    Semantic error examples:
    - amount_mentioned: -50 (negative number)
    - key_facts: [] (empty array)
    - issue_type: "other" but no issue_type_detail

---

## 📝 Exam Questions — Day 3

---

**Q1.** You are building a data extraction system using Claude.
Which approach provides the MOST reliable guarantee that
Claude returns schema-compliant structured output?

A) Instruct Claude to "always respond in valid JSON format"
   in the system prompt

B) Use `tool_use` with a JSON schema and set `tool_choice`
   to force the specific extraction tool

C) Request JSON output and use `json.loads()` with a
   try/except to handle parsing failures

D) Use `tool_choice: "any"` to guarantee Claude calls
   a tool on every turn

**✅ Answer: B**

Task Statement 4.3: tool_use with JSON schema is the most
reliable approach. It eliminates JSON syntax errors entirely
(no markdown fences, no malformed JSON) and enforces
required fields and enum values at the API level.

Option A (system prompt) is probabilistic — Claude may still
wrap output in markdown or omit fields.
Option C handles failures but doesn't prevent them.
Option D guarantees a tool call but not the correct schema
— Claude might call a different tool.

---

**Q2.** Your extraction schema has `amount_mentioned` as
a required field with type "number". In production you
observe Claude returning values like "approximately $300"
and "unknown" for messages that don't mention an amount.
What is the root cause and fix?

A) Add more examples to the system prompt showing correct
   amount extraction

B) Change amount_mentioned to optional with type
   ["number", "null"] — Claude returns null when absent
   rather than hallucinating a value to satisfy required

C) Add a validation step that rejects non-numeric amounts
   and retries

D) Switch from tool_use to a plain JSON prompt

**✅ Answer: B**

When a field is required and the source document doesn't
contain the data, Claude hallucates a value to satisfy
the requirement. Making the field nullable
(["number", "null"]) with no required constraint signals
Claude to return null when the information is absent.

null is always better than a hallucinated value.
Option A (more examples) doesn't fix the schema constraint.
Option C (retry) addresses the symptom not the cause.
Option D loses all schema guarantees.

---

**Q3.** After a tool_use extraction, your validation code
finds that amount_mentioned contains the string "$299.99"
instead of the number 299.99. What is the correct approach?

A) Accept the string value and parse it in downstream code

B) Retry with blind repetition of the same prompt

C) Retry with a prompt that includes the specific error:
   "amount_mentioned must be a number. Got string '$299.99'.
   Return 299.99 without the dollar sign."

D) Mark the extraction as failed and skip this record

**✅ Answer: C**

Task Statement 4.4: retry with specific error feedback is
more effective than blind retry. Claude knows exactly what
to fix and can correct the specific type issue.

Blind retry (Option B) may produce the same error again.
Option A pushes the problem downstream and creates tech debt.
Option D is too aggressive for a format error that is
easily correctable via retry.

---

**Q4.** When are validation retries NOT effective, according
to Task Statement 4.4?

A) When the extraction confidence is "low"

B) When the source document does not contain the information
   being extracted — the data is simply absent

C) When the model has already made 2 retry attempts

D) When the validation error involves an enum field

**✅ Answer: B**

Retries fix format and structural errors — the data exists
but Claude formatted it wrong. Retries cannot fix absent
data — if the order ID is not mentioned in the customer
message, no number of retries will make it appear.

Identifying this limit prevents wasted API calls. When
validation fails because data is absent, return null
for that field rather than retrying indefinitely.

---

**Q5.** What is the difference between `tool_choice: "any"`
and `tool_choice: {"type": "tool", "name": "extract_incident"}`?

A) "any" is faster; forced selection has higher latency

B) "any" guarantees Claude calls a tool but Claude picks which
   one; forced selection guarantees Claude calls exactly the
   named tool with that specific schema

C) "any" works with multiple tools; forced selection only
   works when there is one tool defined

D) There is no meaningful difference for single-tool setups

**✅ Answer: B**

This distinction is directly tested in Task Statement 4.3.

"any": Claude must call A tool. If you have 5 tools defined,
Claude might call get_customer or lookup_order instead of
extract_incident. You get a tool call but not necessarily
the extraction schema.

Forced: Claude must call extract_incident specifically.
You are guaranteed the extraction schema is populated.
This is required for reliable structured output pipelines.

---

**Q6.** Your issue_type enum includes "other" with a
companion issue_type_detail field. What problem does
this pattern solve?

A) It reduces the number of API calls needed for extraction

B) It captures unknown or emerging issue types without
   losing information — "other" flags the case while
   issue_type_detail preserves the specific details

C) It makes the schema backward compatible with older systems

D) It prevents Claude from using incorrect enum values

**✅ Answer: B**

A closed enum captures only known categories. New issue
types appear in production that your enum doesn't cover.
Without "other" + detail, Claude either forces the wrong
category or the extraction fails.

With "other" + detail: unknown types are captured cleanly,
you can review issue_type_detail values to identify new
categories to add to the enum, and no information is lost.
This is the extensible categorisation pattern from
Task Statement 4.3.

---

**Q7.** Few-shot examples are added to an extraction prompt.
Where should the examples be placed relative to the
target message?

A) After the target message, as post-hoc examples

B) Interspersed randomly through the prompt

C) Before the target message — Claude reads examples
   first, then applies the demonstrated pattern to
   the new input

D) In the system prompt, separated from the user message

**✅ Answer: C**

Standard few-shot ordering: examples → target input.
Claude reads the demonstrations, infers the expected
pattern, then applies it to the new message.

Option D (system prompt placement) can work but separates
examples from context. The most reliable placement is
in the same user message, before the target input.

---

**Q8.** A customer message reads: "I have a problem.
Please help." Your extraction returns:
customer_id: "C000", order_id: "ORD-00000".
What caused this and how do you fix it?

A) The model version is too old — upgrade to a newer model

B) These fields are defined as required with non-nullable
   types. Claude hallucinated values to satisfy requirements.
   Fix: make customer_id and order_id nullable
   (["string", "null"]) and remove from required list.

C) The few-shot examples showed C000 and ORD-00000 as
   placeholder values — remove those examples

D) Claude is confused by the ambiguous message — add
   more specific instructions

**✅ Answer: B**

Required + non-nullable + absent data = hallucination.
This is the canonical hallucination trigger in structured
extraction. The fix is always the same:

    Before: "customer_id": {"type": "string"}  ← required
    After:  "customer_id": {"type": ["string", "null"]}
            removed from "required" list

Claude can then return null honestly instead of inventing
a value. This is Task Statement 4.3 core concept.

---

**Q9.** Your extraction pipeline processes 1000 documents
overnight using the Message Batches API. 47 documents fail
validation. What is the correct approach for the failed batch?

A) Resubmit all 1000 documents with an improved prompt

B) Identify failed documents by their custom_id, analyse
   the error types, resubmit only the 47 failed documents
   with modifications appropriate to each error type

C) Accept the 953 successful extractions and discard the 47

D) Retry all 47 failed documents with the same prompt

**✅ Answer: B**

Task Statement 4.5: handle batch failures by custom_id —
resubmit only failed documents with appropriate modifications.

Resubmitting all 1000 (Option A) is wasteful and may re-fail
on the same errors. Discarding failures (Option C) loses data.
Blind retry of 47 (Option D) will produce the same errors.

The correct approach: identify failure patterns across the
47 documents, determine if errors are format-based (retry
with feedback) or missing-data-based (accept nulls), then
resubmit with appropriate prompt modifications.

---

**Q10.** tool_use with JSON schema eliminates which class
of errors but NOT which other class?

A) Eliminates semantic errors; does not eliminate syntax errors

B) Eliminates syntax errors (malformed JSON, invalid enums,
   wrong types); does not eliminate semantic errors
   (wrong field values, contradictions, absent data)

C) Eliminates both syntax and semantic errors

D) Eliminates neither — tool_use only changes the response format

**✅ Answer: B**

This is the central concept of Task Statement 4.3.

Syntax errors eliminated by tool_use:
    Malformed JSON, markdown fences
    Required fields missing
    Invalid enum values
    Wrong types (string where number expected)

Semantic errors NOT eliminated:
    amount_mentioned: 0.01 when $299 was mentioned
    issue_type: "refund_request" when clearly a return
    Contradictory data
    Values technically valid but contextually wrong

Your validation code handles semantic errors.
tool_use handles syntax errors.
Both are necessary for a robust extraction pipeline.

---

**Q11.** What is the PRIMARY advantage of few-shot examples
over detailed textual instructions for structured extraction?

A) Few-shot examples are shorter and use fewer tokens

B) Few-shot examples demonstrate the exact format including
   ambiguous cases, allowing Claude to generalise the pattern
   to novel inputs rather than matching only specified rules

C) Few-shot examples are required by the Anthropic API
   for tool_use responses

D) Few-shot examples prevent Claude from calling the wrong tool

**✅ Answer: B**

Task Statement 4.2: few-shot examples are the most effective
technique when instructions alone produce inconsistent output.

Instructions say: "Return amount as a number."
Examples show: amount as 299.99 not "$299.99" not "299 dollars"

Instructions can describe every case. Examples demonstrate
them. Claude generalises from examples to novel inputs more
reliably than from rule lists alone.

This is especially powerful for ambiguous cases (urgency
classification, edge-case issue types) where rules are
hard to write exhaustively.

---

**Q12.** Your extraction schema defines urgency as a required
enum field with values: urgent, high, normal, low. A customer
message reads: "hi can I check my order status?"
What should urgency be?

A) null — the message doesn't express urgency

B) urgent — any customer contact should be treated as urgent

C) normal — no urgency indicators present, default to normal

D) This should cause a validation error

**✅ Answer: C**

"normal" is the correct default when no urgency signals
are present. The urgency enum is required (not nullable)
because every message has an urgency level — even absence
of urgency signals is information (it means normal).

null would be wrong for a required enum field.
urgent would be a hallucinated classification.
No validation error because "normal" is a valid enum value.

The few-shot examples demonstrate this explicitly:
Example 2 shows "urgency": "normal" for a message with
no urgency language — this is what guides Claude to
classify correctly.

---

**Q13.** Which scenario demonstrates that retrying an
extraction with error feedback will NOT be effective?

A) Claude returned amount as the string "$50" instead
   of the number 50.0

B) Claude returned urgency as "NORMAL" instead of "normal"

C) Customer message contains no order ID, but order_id
   field keeps returning null instead of a valid ID

D) Claude returned an empty key_facts array

**✅ Answer: C**

If the customer message genuinely contains no order ID,
retrying will not produce one. The data is absent from
the source — this is exactly the scenario Task Statement
4.4 identifies as where retries are ineffective.

Options A and B are format errors — correct type and case
via retry with specific feedback.
Option D is a structural error — retry with feedback
instructing Claude to extract at least one fact.

Option C: the correct action is to return null for order_id
and move on, not to retry. Identifying this distinction
is the core exam question for Task Statement 4.4.

---

## 🧠 Quick-Fire Revision

| Q | A |
|---|---|
| Most reliable structured output approach? | tool_use + JSON schema + forced tool_choice |
| tool_choice "auto" vs "any" vs forced? | May call/return text vs must call a tool vs must call X |
| How to prevent hallucination on optional fields? | Make them nullable: ["string", "null"] |
| What does tool_use NOT prevent? | Semantic errors (wrong values, contradictions) |
| Few-shot examples go before or after target? | Before — examples then target message |
| When are retries NOT effective? | When information is absent from source document |
| "other" + detail pattern solves what? | Captures unknown categories without losing data |
| Syntax vs semantic errors? | Syntax: tool_use eliminates. Semantic: your code validates. |
| Best retry approach? | Include specific error in retry prompt, not blind retry |
| Required field + absent data = ? | Hallucinated value — make it nullable instead |

---

## ✅ Readiness Check — Before Day 4

Complete without notes:
1. Explain why nullable fields prevent hallucination
2. Name the three tool_choice values and when to use each
3. Explain the difference between syntax and semantic errors
4. Explain when retries work vs when they don't
5. Describe the few-shot placement pattern
6. Name the "other" + detail pattern and what problem it solves
7. Answer Q1-Q13 without looking at explanations
8. Run Experiment 1 and observe the hallucinated amount