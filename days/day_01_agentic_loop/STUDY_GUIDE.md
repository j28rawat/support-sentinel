# Day 1 — Study Guide & Exam Preparation
## The Agentic Loop

---

## 📚 Core Concepts

### 1. The Agentic Loop — Four Phases

    SEND    → Call Claude with full message history + tools
    INSPECT → Check stop_reason on response
    EXECUTE → If "tool_use": run tools, append results, loop
    RETURN  → If "end_turn": extract text, return AgentResponse

### 2. stop_reason — The Only Valid Control Signal

| stop_reason | Meaning | Your Action |
|---|---|---|
| `"end_turn"` | Claude has finished | Extract text, exit loop |
| `"tool_use"` | Claude wants tools | Execute, append, loop again |
| `"max_tokens"` | Response cut off | Handle gracefully |

### 3. The Two Critical Appends (Missing Either = Bug)

    # After stop_reason == "tool_use":

    # Append 1: Claude's full response (REQUIRED)
    messages.append({
        "role": "assistant",
        "content": response.content   ← includes tool_use blocks
    })

    # Execute tools...

    # Append 2: Tool results as user turn (REQUIRED)
    messages.append({
        "role": "user",
        "content": tool_results        ← list of tool_result dicts
    })

    # Missing Append 1: Claude sees its previous turn as absent
    # Missing Append 2: Claude never sees what tools returned
    #                   → calls same tool repeatedly → infinite loop

### 4. tool_choice Values

| Value | Behaviour | Use When |
|---|---|---|
| `"auto"` | Claude decides | Default — most conversations |
| `"any"` | Must call a tool, picks which | Need guaranteed tool call |
| `{"type":"tool","name":"X"}` | Must call tool X | Force first action |

### 5. Model-Driven vs Pre-Configured

    Model-driven (agentic loop):
        Claude decides which tools to call and when to stop.
        Sequence varies based on context.
        This is what SupportSentinel uses.

    Pre-configured (decision tree):
        Code determines exact tool sequence.
        Same path every time regardless of context.

### 6. Anti-Patterns (Exam Distractors)

    ❌ Parsing text: if "anything else" in response.text: break
    ❌ Cap as primary: for i in range(10): ...
    ❌ Missing append: executing tools without updating messages
    ❌ Partial append: appending tool results but not assistant turn
    ❌ Wrong format: returning dict instead of json.dumps(dict)

### 7. Dependency Injection

    tool_executor: Callable[[str, dict], str]

    The loop doesn't import tools directly.
    You inject the executor from outside.
    Same loop → any agent → any tool set.
    Tests inject mock executors without touching loop code.

### 8. Message History Growth

    Start:        [user: initial message]
    After tool 1: [user, assistant(tool_use), user(tool_result)]
    After tool 2: [..., assistant(tool_use), user(tool_result)]
    After tool 3: [..., assistant(tool_use), user(tool_result)]
    Final:        [...] → Claude returns end_turn (not appended)

    3 tool calls = 7 messages in history.

---

## 📝 Exam Questions — Day 1

---

**Q1.** What is the correct primary mechanism for determining
when an agentic loop should terminate?

A) Check if Claude's response text contains a closing phrase
   such as "Is there anything else I can help you with?"

B) Increment an iteration counter and stop after a fixed
   maximum number of iterations

C) Inspect `stop_reason` — continue when `"tool_use"`,
   terminate when `"end_turn"`

D) Check whether the response content list is empty

**✅ Answer: C**

`stop_reason` is the authoritative signal from the Claude API.
Option A (text parsing) and Option B (iteration cap as primary)
are explicitly listed as anti-patterns in Task Statement 1.1.
Option D is incorrect — content can be non-empty on end_turn.

---

**Q2.** After Claude returns `stop_reason == "tool_use"` with
two tool_use blocks, what is the correct sequence of actions?

A) Execute only the first tool_use block to keep things simple

B) Return Claude's text portion to the user, then handle
   tool calls in the next conversation turn

C) Append Claude's full response to history, execute both
   tool_use blocks, collect both results into a single user
   turn, append it, then call Claude again

D) Reset the messages list and start a fresh conversation
   with the tool results

**✅ Answer: C**

When `stop_reason == "tool_use"`, the response is incomplete.
Execute ALL tool_use blocks (not just first), collect ALL
results into one user turn, append both assistant turn AND
user turn, then loop. Resetting messages (D) destroys context.

---

**Q3.** Your agent enters an infinite loop, calling
`get_customer` repeatedly without progressing. Root cause?

A) The tool description for `get_customer` is too detailed

B) `tool_choice` is set to `"any"`, forcing repeated tool calls

C) Tool results from get_customer are not being appended...
   The API immediately returns a 400 BadRequestError because
   every tool_use block must have a corresponding tool_result
   block in the next message — the conversation is structurally
   invalid without it.

D) The system prompt creates a circular dependency

**✅ Answer: C**

Without appending tool results to messages, Claude sees the
same conversation state every iteration — it has no memory
that `get_customer` was already called, so it calls it again.
Fix: ensure `messages.append({"role": "user", "content": tool_results})`
runs after every tool execution.

---

**Q4.** What is the key difference between an agentic loop
and a pre-configured decision tree?

A) Agentic loops make fewer API calls

B) In an agentic loop, Claude determines which tools to call
   and when to stop based on context; decision trees have
   code-determined fixed sequences

C) Decision trees are preferred for production reliability

D) Agentic loops only work with the Claude Agent SDK

**✅ Answer: B**

Model-driven decision-making (Claude reasons about next step)
vs pre-configured sequences (code determines flow) is the
core distinction tested in Task Statement 1.1. Neither is
universally better — but the exam tests whether you can
identify which pattern a system uses.

---

**Q5.** You need `verify_identity` to always be Claude's
FIRST tool call in every conversation. Which approach
guarantees this?

A) `tool_choice = "auto"`

B) `tool_choice = "any"`

C) `tool_choice = {"type": "tool", "name": "verify_identity"}`

D) System prompt instruction: "Always call verify_identity first"

**✅ Answer: C**

Forced tool selection guarantees a specific tool is called
on the first turn. `"auto"` may call any tool or none.
`"any"` calls a tool but Claude picks which one.
Option D (prompt instruction) has a non-zero failure rate —
prompts are probabilistic, not deterministic.

---

**Q6.** A response with `stop_reason == "tool_use"` contains:
[text_block, tool_use_block_1, tool_use_block_2]. How many
tools should your executor run?

A) Zero — the text block means Claude wants to respond

B) One — only the first tool_use block

C) Two — all tool_use blocks regardless of position or
   presence of text blocks

D) Depends on the content of the text block

**✅ Answer: C**

When `stop_reason == "tool_use"`, ALL tool_use blocks must
be executed. Text blocks alongside tool_use blocks are
Claude's commentary ("Let me check that..."), not final
responses. Position is irrelevant — iterate `response.content`
and execute every block where `block.type == "tool_use"`.

---

**Q7.** Your tool executor returns Python dicts directly
but you get: `"tool_result content must be a string"`.
Correct fix?

A) Change all tool functions to return strings

B) Wrap results in a list before appending

C) Use `json.dumps()` to serialise dicts to JSON strings
   before returning from the executor

D) Set Content-Type headers on the API call

**✅ Answer: C**

The Anthropic API requires tool_result content to be strings.
Use `json.dumps(result, default=str)`. Claude can parse JSON
strings — returning serialised dicts preserves structure
while satisfying the API's string requirement.

---

**Q8.** After 3 tool-calling iterations, how many entries
does the messages list contain before the final API call?

A) 1 — only the original user message

B) 3 — one per tool call

C) 7 — initial user + 3 assistant turns + 3 user turns

D) Messages are reset after each iteration

**✅ Answer: C**

Growth: 1 initial + (1 assistant + 1 user) × 3 iterations = 7.
The messages list is the agent's complete memory.
Never reset it between iterations — doing so would make
Claude stateless and repeat the same first tool call forever.

---

**Q9.** The `max_iterations` cap fires before `end_turn` is
reached. What does this indicate?

A) Normal behaviour — 10 iterations is the expected maximum

B) The agent is making too many API calls and needs optimising

C) Something is likely wrong — tool results may not be
   appending correctly, or instructions are preventing resolution.
   Investigate; do not treat this as normal termination.

D) The customer's request is too complex and should be rejected

**✅ Answer: C**

The iteration cap is a safety net for bugs, not a normal
termination path. If it fires, the loop failed to reach
`end_turn` naturally. Common causes: missing append, tool
errors Claude can't recover from, contradictory instructions.

---

**Q10.** Why is `tool_executor` injected as a `Callable`
parameter rather than imported directly by the loop?

A) Python doesn't support direct imports in while loops

B) It reduces the number of API calls made

C) Dependency injection decouples the loop from specific
   tools — the same loop works for any agent, and tests
   can inject mock executors without touching loop code

D) The Anthropic SDK requires callable parameters

**✅ Answer: C**

Dependency injection is an architectural pattern that keeps
the loop reusable and testable. Without it, `agentic_loop.py`
would need to import specific tool modules — making it
impossible to use the same loop for different agents.

---

**Q11.** A customer's request results in Claude calling
`get_customer`, then `lookup_order`, then `process_refund`
without calling `check_refund_eligibility`. What is the
most reliable fix?

A) Add "Always call check_refund_eligibility before
   process_refund" to the system prompt

B) Add a PREREQUISITES note to process_refund's tool
   description

C) Implement a programmatic prerequisite gate that blocks
   `process_refund` unless eligibility has been confirmed

D) Both A and B together — layered prompt guidance

**✅ Answer: C**

For financial operations, prompt instructions (A, B, D)
are probabilistic — they have a non-zero failure rate.
A programmatic gate provides deterministic enforcement.
The exam explicitly states this for Task Statement 1.4.
(We implement this in Day 7 using hooks.)

---

**Q12.** What happens if you append the tool results to
messages but forget to append the assistant's response
(the tool_use turn)?

A) Nothing — the tool results are sufficient

B) Claude will call the same tool again because it doesn't
   see its own previous request in history

C) The API will raise an error about missing assistant turn

D) Claude will proceed but ignore the tool results

**✅ Answer: C**

The Anthropic API requires messages to alternate roles
properly. An assistant turn with a tool_use block MUST be
followed by a user turn with the corresponding tool_result.
If the assistant turn is missing, the API rejects the
malformed conversation history.

Both appends are required. Missing either one is a bug.

---

**Q13.** Why does SupportSentinel centralise all system
prompts in `sentinel/config/prompts.py`?

A) The Anthropic API requires prompts to be in a specific file

B) Centralising prompts means one place to iterate, version
   control shows prompt changes in PRs, and no prompt strings
   are buried in agent files

C) Prompts must be loaded before the API client initialises

D) Distributed prompts cause rate limiting

**✅ Answer: B**

Centralised prompts are a production best practice.
When prompts are scattered across agent files:
- Hard to find which prompt controls which behaviour
- Git diffs don't show what changed in agent behaviour
- Multiple places to update when policy changes

In `prompts.py`, every prompt change is visible, reviewed,
and traceable to its effect on agent behaviour.

---

## 🧠 Quick-Fire Revision

| Q | A |
|---|---|
| Primary loop termination signal? | `stop_reason == "end_turn"` |
| What does `stop_reason == "tool_use"` require? | Execute ALL tools, append both turns, loop again |
| Two critical appends? | Assistant turn + User turn (tool results) |
| Missing Append 2 causes? | Error code: 400 — Claude never sees tool results |
| `tool_choice = "any"` does what? | Forces Claude to call a tool — picks which |
| Iteration cap is? | Safety net for bugs — NOT primary controller |
| Tool result format required? | String — use `json.dumps()` |
| Messages after 3 tool calls? | 7 entries (1 + 3×2) |
| Model-driven means? | Claude decides tool sequence, not code |
| Dependency injection benefit? | Loop works for any agent, tests mock cleanly |

---

## ✅ Readiness Check — Before Day 2

Complete without notes:
1. Draw the agentic loop as a flowchart
2. Write the two critical append statements from memory
3. Explain the three `tool_choice` values and when to use each
4. Name three anti-patterns for loop control
5. Answer Q1-Q13 without looking at explanations
6. Run all 3 experiments and explain what you observed