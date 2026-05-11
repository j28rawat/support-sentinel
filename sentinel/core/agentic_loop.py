"""
sentinel/core/agentic_loop.py
===============================
The agentic loop — the heartbeat of every Claude-powered agent.

ADDITIVE MODULE:
    Day 1:  run_agentic_loop()     — core loop, single agent
    Day 4+: Will add coordinator loop variant
    Day 7+: Will add hook-intercepted loop variant

    Existing functions are NEVER modified after their day.
    New variants are appended below.

═══════════════════════════════════════════════════════════════
THE CORE CONCEPT
═══════════════════════════════════════════════════════════════

An agentic loop is a while loop with exactly this structure:

    ┌─────────────────────────────────┐
    │  Send messages to Claude        │
    └──────────────┬──────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────┐
    │  Inspect stop_reason            │
    └──────────────┬──────────────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
    "tool_use"          "end_turn"
          │                 │
          ▼                 ▼
    Execute tools      Return response
    Append results     to caller
    Loop again         ✓ Done


═══════════════════════════════════════════════════════════════
EXAM ANTI-PATTERNS — These appear as wrong-answer distractors
═══════════════════════════════════════════════════════════════

    ❌  Parsing text to detect completion:
        if "Is there anything else" in response.text: break

    ❌  Iteration cap as PRIMARY stopping mechanism:
        for i in range(10): ...  # breaks at 10 regardless

    ❌  Missing message append (causes infinite loop):
        # Executing tool but NOT appending result to messages
        # Claude sees same state every iteration → loops forever

    ❌  Appending only tool results, not assistant turn:
        # Must append BOTH assistant response AND tool results
"""

from typing import Callable
from rich.console import Console
from sentinel.core.claude_client import create_message
from sentinel.core.types import AgentResponse

console = Console()


def run_agentic_loop(
    system_prompt: str,
    initial_message: str,
    tools: list[dict],
    tool_executor: Callable[[str, dict], str],
    max_iterations: int = 10,
) -> AgentResponse:
    """
    Run a complete agentic loop until Claude signals end_turn.

    Args:
        system_prompt:    Defines the agent's role and rules.
                          Sent with every API call but not stored
                          in messages history.

        initial_message:  The customer's opening message.
                          Becomes the first entry in messages.

        tools:            List of tool definitions.
                          Claude reads descriptions to decide
                          which tool to call and when.

        tool_executor:    Callable(tool_name, tool_input) → str
                          Your Python functions that actually
                          execute the tools. Returns JSON string.
                          The loop calls this — it never imports
                          tools directly (dependency injection).

        max_iterations:   SAFETY NET ONLY — not primary control.
                          If loop hits this, something is wrong.
                          Primary termination: stop_reason.

    Returns:
        AgentResponse with final text, tool call history,
        iteration count, and resolution status.

    EXAM NOTE — Dependency Injection:
        tool_executor is injected as a Callable rather than
        imported directly. This means:
        - The same loop works for ANY agent with ANY tools
        - Tests can inject mock executors trivially
        - No coupling between loop logic and tool logic
    """

    # ── Initialise conversation history ──────────────────────────────
    # This list GROWS with every iteration.
    # It is Claude's only memory across calls.
    # By end of a 4-tool session: 8+ entries in this list.
    messages: list[dict] = [
        {"role": "user", "content": initial_message}
    ]

    tool_calls_made: list[dict] = []
    iteration = 0

    console.print(
        f"\n[bold blue]━━━ Agent Starting ━━━[/bold blue]"
        f"\n[dim]Customer: {initial_message[:80]}..."
        f"[/dim]\n"
        if len(initial_message) > 80
        else f"\n[bold blue]━━━ Agent Starting ━━━[/bold blue]"
        f"\n[dim]Customer: {initial_message}[/dim]\n"
    )

    while iteration < max_iterations:
        iteration += 1
        console.print(
            f"[dim]──── Iteration {iteration} "
            f"({'tool_use expected' if iteration > 1 else 'first call'}) "
            f"────[/dim]"
        )

        # ── STEP 1: Call Claude ───────────────────────────────────────
        # Pass FULL message history every time.
        # Claude has no state between calls — history IS memory.
        response = create_message(
            messages=messages,
            tools=tools,
            system=system_prompt,
        )

        # ── STEP 2: Inspect stop_reason ───────────────────────────────
        # THIS IS THE ONLY VALID LOOP CONTROL SIGNAL.
        # Do not use text content, iteration count, or any other
        # signal as the primary termination mechanism.
        console.print(
            f"[dim]  stop_reason: "
            f"[bold]{response.stop_reason}[/bold][/dim]"
        )

        # ── BRANCH A: Claude is done ──────────────────────────────────
        if response.stop_reason == "end_turn":
            final_text = _extract_text(response)
            escalated = any(
                t["tool"] == "escalate_to_human"
                for t in tool_calls_made
            )

            console.print(
                f"\n[bold green]✓ Resolved in "
                f"{iteration} iteration(s)[/bold green]"
                f"\n[green]{final_text}[/green]\n"
            )

            return AgentResponse(
                final_response=final_text,
                tool_calls=tool_calls_made,
                iterations=iteration,
                resolved=True,
                escalated=escalated,
            )

        # ── BRANCH B: Claude wants to call tool(s) ───────────────────
        elif response.stop_reason == "tool_use":

            # ── CRITICAL STEP: Append assistant's FULL response ───────
            # This includes BOTH any text blocks AND all tool_use blocks.
            # Claude needs to see its own previous turn on next iteration.
            # Missing this line = Claude repeats same tool call forever.
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # ── Execute ALL tool_use blocks in this response ──────────
            # Claude can request multiple tools in one response.
            # All must be executed before the next API call.
            tool_results: list[dict] = []

            for block in response.content:
                if block.type != "tool_use":
                    continue

                tool_name = block.name
                tool_input = block.input
                tool_use_id = block.id

                console.print(
                    f"  [yellow]→ Tool: [bold]{tool_name}[/bold][/yellow]"
                    f"\n  [dim]  Input: {tool_input}[/dim]"
                )

                # Execute via injected executor
                # Returns JSON string (Anthropic API requirement)
                result_str = tool_executor(tool_name, tool_input)

                # Truncate display for readability
                display = (
                    result_str[:120] + "..."
                    if len(result_str) > 120
                    else result_str
                )
                console.print(f"  [dim]  Result: {display}[/dim]")

                tool_calls_made.append({
                    "tool": tool_name,
                    "input": tool_input,
                    "result": result_str,
                    "iteration": iteration,
                })

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": result_str,
                })

            # ── CRITICAL STEP: Append tool results as user turn ───────
            # Tool results are appended as a "user" role message.
            # This is how Claude sees what the tools returned.
            # Missing this = Claude has no memory of tool results.
            messages.append({
                "role": "user",
                "content": tool_results
            })

            # Loop continues → Claude reasons about tool results
            # and decides next action (another tool or end_turn)

        # ── BRANCH C: Unexpected stop_reason ─────────────────────────
        else:
            raise ValueError(
                f"Unexpected stop_reason: '{response.stop_reason}'. "
                f"Expected 'tool_use' or 'end_turn'. "
                f"Check Claude API documentation for new values."
            )

    # ── Safety net fired ─────────────────────────────────────────────
    # If we reach here, max_iterations was hit without end_turn.
    # This should be investigated — likely a bug in tool appending
    # or contradictory instructions preventing resolution.
    console.print(
        f"\n[bold red]⚠ Max iterations ({max_iterations}) reached "
        f"without resolution.[/bold red]"
        f"\n[red]Investigate: are tool results being appended "
        f"correctly?[/red]\n"
    )

    return AgentResponse(
        final_response=(
            "I wasn't able to complete your request. "
            "A team member will follow up with you shortly."
        ),
        tool_calls=tool_calls_made,
        iterations=iteration,
        resolved=False,
    )


def _extract_text(response) -> str:
    """
    Extract plain text from Claude's response content blocks.

    A response may contain multiple blocks of different types.
    We find the first text block and return its content.
    """
    for block in response.content:
        if hasattr(block, "text"):
            return block.text
    return ""