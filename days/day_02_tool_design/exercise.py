"""
days/day_02_tool_design/exercise.py
=====================================
Day 2 Exercise: Tool Design — Misrouting Demonstration.

WHAT THIS DEMONSTRATES:
    Part 1 — Vague descriptions cause misrouting.
             Same message, same tools, bad descriptions.
             Claude picks the wrong tool.

    Part 2 — Rich descriptions fix misrouting.
             Same message, same tools, good descriptions.
             Claude routes correctly.

    Part 3 — Structured errors guide recovery.
             Tools return errorCategory + isRetryable.
             Claude makes intelligent decisions, not generic ones.

IMPORTS:
    This file imports from sentinel.tools.day_02 — the Day 2 snapshot.
    sentinel.tools.day_01 is completely unaffected.

USAGE:
    python days/day_02_tool_design/exercise.py
    python days/day_02_tool_design/exercise.py --part 1
    python days/day_02_tool_design/exercise.py --part 2
    python days/day_02_tool_design/exercise.py --part 3
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..")
))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns

from sentinel.core.agentic_loop import run_agentic_loop
from sentinel.config.prompts import DAY_02_SUPPORT_AGENT
from sentinel.tools.day_02 import (
    ALL_TOOL_DEFINITIONS,
    VAGUE_TOOL_DEFINITIONS,
    execute_tool,
)

console = Console()

# ── Test message — deliberately ambiguous ────────────────────────────────────
# Customer C002 (James) does NOT provide an order ID.
# Correct tool: get_order_history (no ID provided)
# Wrong tool:   lookup_order (requires an order ID)
# With vague descriptions, Claude cannot distinguish between them.

AMBIGUOUS_MESSAGE = (
    "Hi, I'm customer C002. "
    "I placed an order a few days ago and it hasn't arrived yet. "
    "Can you tell me what's happening?"
)

# ── Part 3 message — triggers error handling ─────────────────────────────────
ESCALATION_MESSAGE = (
    "I'm customer C001. I want a full refund for my Smart Watch "
    "from order ORD-10091. The battery died after two days."
)


def run_part_1() -> list[str]:
    """Vague descriptions — observe misrouting."""
    console.print(Panel(
        "[bold red]PART 1: Vague Tool Descriptions[/bold red]\n\n"
        "Customer message does not include an order ID.\n"
        "[bold]Expected tool:[/bold] get_order_history\n"
        "[bold]Watch what happens with vague descriptions...[/bold]",
        border_style="red",
    ))

    result = run_agentic_loop(
        system_prompt=DAY_02_SUPPORT_AGENT,
        initial_message=AMBIGUOUS_MESSAGE,
        tools=VAGUE_TOOL_DEFINITIONS,
        tool_executor=execute_tool,
    )

    tools_used = result.tools_used()
    console.print(
        f"\n[red]Tools called (vague): {tools_used}[/red]\n"
    )
    return tools_used


def run_part_2() -> list[str]:
    """Rich descriptions — observe correct routing."""
    console.print(Panel(
        "[bold green]PART 2: Rich Tool Descriptions[/bold green]\n\n"
        "Same customer message. Same tools. Same Claude model.\n"
        "[bold]Only the descriptions changed.[/bold]\n"
        "[bold]Expected tool:[/bold] get_order_history",
        border_style="green",
    ))

    result = run_agentic_loop(
        system_prompt=DAY_02_SUPPORT_AGENT,
        initial_message=AMBIGUOUS_MESSAGE,
        tools=ALL_TOOL_DEFINITIONS,
        tool_executor=execute_tool,
    )

    tools_used = result.tools_used()
    console.print(
        f"\n[green]Tools called (rich): {tools_used}[/green]\n"
    )
    return tools_used


def run_part_3() -> None:
    """Structured errors guide escalation correctly."""
    console.print(Panel(
        "[bold yellow]PART 3: Structured Error Recovery[/bold yellow]\n\n"
        "Customer requests refund for $549 Smart Watch.\n"
        "process_refund will return a business error:\n"
        "  error_category: business\n"
        "  is_retryable: False\n"
        "  requires_escalation: True\n\n"
        "[bold]Watch Claude route to escalate_to_human[/bold]\n"
        "based on the structured error — not a generic failure.",
        border_style="yellow",
    ))

    result = run_agentic_loop(
        system_prompt=DAY_02_SUPPORT_AGENT,
        initial_message=ESCALATION_MESSAGE,
        tools=ALL_TOOL_DEFINITIONS,
        tool_executor=execute_tool,
    )

    tools_used = result.tools_used()
    console.print(
        f"\n[yellow]Tools called: {tools_used}[/yellow]"
    )

    escalated = result.was_tool_called("escalate_to_human")
    if escalated:
        console.print(
            "[bold green]✓ Agent correctly escalated based on "
            "business error response[/bold green]\n"
        )
    else:
        console.print(
            "[bold red]✗ Agent did not escalate — check "
            "process_refund error structure[/bold red]\n"
        )


def print_comparison(
    vague_tools: list[str],
    rich_tools: list[str]
) -> None:
    """Print side-by-side comparison of Parts 1 and 2."""
    table = Table(
        title="Part 1 vs Part 2 — Same Message, Same Tools, "
              "Different Descriptions"
    )
    table.add_column("", style="bold")
    table.add_column("Vague Descriptions", style="red")
    table.add_column("Rich Descriptions", style="green")

    table.add_row(
        "Tools called",
        " → ".join(vague_tools),
        " → ".join(rich_tools),
    )
    table.add_row(
        "Used get_order_history?",
        "✓" if "get_order_history" in vague_tools else "✗",
        "✓" if "get_order_history" in rich_tools else "✗",
    )
    table.add_row(
        "Correct routing?",
        "?" if "get_order_history" in vague_tools else "✗",
        "✓" if "get_order_history" in rich_tools else "?",
    )

    console.print(table)
    console.print(
        "\n[dim]Same Claude model. Same customer message. "
        "Same tool implementations.\n"
        "Only the description strings changed. "
        "This is the exam's core lesson for Domain 2.[/dim]\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SupportSentinel Day 2 — Tool Design Exercise"
    )
    parser.add_argument(
        "--part",
        type=int,
        choices=[1, 2, 3],
        default=None,
        help="Run a specific part (1, 2, or 3). "
             "Omit to run all three."
    )
    args = parser.parse_args()

    console.print(
        "\n[bold]SupportSentinel — Day 2: Tool Design[/bold]\n"
        "[dim]Imports from: sentinel.tools.day_02 (frozen snapshot)"
        "[/dim]\n"
        "[dim]sentinel.tools.day_01 is completely unaffected[/dim]\n"
    )

    if args.part == 1:
        run_part_1()
    elif args.part == 2:
        run_part_2()
    elif args.part == 3:
        run_part_3()
    else:
        vague_tools = run_part_1()
        console.print("─" * 60 + "\n")
        rich_tools = run_part_2()
        console.print("─" * 60 + "\n")
        print_comparison(vague_tools, rich_tools)
        console.print("─" * 60 + "\n")
        run_part_3()