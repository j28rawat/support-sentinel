"""
days/day_03_structured_output/exercise.py
============================================
Day 3 Exercise: Structured Output & Prompt Engineering.

WHAT THIS DEMONSTRATES:

    Part 1 — Basic extraction with few-shot examples.
             Watch Claude extract structured data from a
             clear customer message. Observe field population
             and null handling for absent data.

    Part 2 — Edge case handling.
             Ambiguous message, missing key fields.
             Watch how few-shot examples guide Claude to
             return null instead of hallucinating values.
             Compare with_few_shot vs without_few_shot.

    Part 3 — Validation-retry loop.
             A message designed to trigger a semantic error.
             Watch the retry prompt include the specific error.
             Claude corrects the specific issue on retry.

    Part 4 — tool_choice demonstration.
             Same message, three tool_choice values.
             Shows the difference between auto, any, forced.

IMPORTS:
    This file imports from sentinel.tools.day_03 and
    sentinel.extraction — Day 3 snapshot, frozen.
    All prior days completely unaffected.

USAGE:
    python days/day_03_structured_output/exercise.py
    python days/day_03_structured_output/exercise.py --part 1
    python days/day_03_structured_output/exercise.py --part 2
    python days/day_03_structured_output/exercise.py --part 3
    python days/day_03_structured_output/exercise.py --part 4
"""

import sys
import os
import argparse
import json

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..")
))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.columns import Columns

from sentinel.extraction import IncidentExtractor
from sentinel.core.claude_client import create_message
from sentinel.extraction.schemas import INCIDENT_SCHEMA
from sentinel.config.prompts import DAY_03_EXTRACTION_AGENT

console = Console()

# ── Test messages ─────────────────────────────────────────────────────────────

# Part 1 — Clear, complete message
CLEAR_MESSAGE = (
    "Hi, I'm Sarah, customer C001. My order ORD-10045 arrived "
    "with the headphones completely broken. I need a full refund "
    "of $299.99 urgently — I need these for work tomorrow."
)

# Part 2 — Ambiguous, partial information
AMBIGUOUS_MESSAGE = (
    "Hello, something went wrong with my purchase. "
    "I'm not happy about this at all. Can someone help me?"
)

# Part 3 — Triggers semantic validation error
# amount as a negative number (refund TO customer as negative)
VALIDATION_TRIGGER_MESSAGE = (
    "I'm customer C002. I placed order ORD-10078 three days ago "
    "and it still hasn't shipped. I want compensation of $90 "
    "for the inconvenience. This is very frustrating."
)

# Part 4 — Used to demonstrate tool_choice differences
TOOL_CHOICE_MESSAGE = (
    "I need help with my recent order."
)


def print_extraction_result(
    result,
    title: str = "Extraction Result"
) -> None:
    """Pretty-print an ExtractionResult."""
    table = Table(title=title)
    table.add_column("Field", style="bold", width=25)
    table.add_column("Value", width=50)

    data = result.data
    for field, value in data.items():
        if value is None:
            table.add_row(field, "[dim]null[/dim]")
        elif isinstance(value, list):
            table.add_row(field, "\n".join(f"• {v}" for v in value))
        else:
            table.add_row(field, str(value))

    console.print(table)
    console.print(
        f"[dim]Success: {result.success} | "
        f"Confidence: {result.confidence} | "
        f"Retries: {result.retries}[/dim]\n"
    )


def run_part_1() -> None:
    """Basic extraction — clear message with few-shot examples."""
    console.print(Panel(
        "[bold cyan]PART 1: Basic Extraction with Few-Shot Examples[/bold cyan]\n\n"
        "Clear message with customer ID, order ID, amount.\n"
        "Watch how few-shot examples produce consistent output format.",
        border_style="cyan",
    ))

    console.print(f"[dim]Message: \"{CLEAR_MESSAGE}\"[/dim]\n")

    extractor = IncidentExtractor(use_few_shot=True)
    result = extractor.extract(CLEAR_MESSAGE)
    print_extraction_result(result, "Part 1 — Clear Message")


def run_part_2() -> None:
    """Edge case — compare with and without few-shot examples."""
    console.print(Panel(
        "[bold yellow]PART 2: Ambiguous Message — Few-Shot vs No Few-Shot[/bold yellow]\n\n"
        "Vague message with no order ID, no customer ID.\n"
        "Without few-shot: Claude may hallucinate missing fields.\n"
        "With few-shot: Claude returns null for absent data.",
        border_style="yellow",
    ))

    console.print(f"[dim]Message: \"{AMBIGUOUS_MESSAGE}\"[/dim]\n")

    # Without few-shot
    console.print("[red]Without few-shot examples:[/red]")
    extractor_no_fs = IncidentExtractor(use_few_shot=False)
    result_no_fs = extractor_no_fs.extract(AMBIGUOUS_MESSAGE)
    print_extraction_result(result_no_fs, "No Few-Shot")

    # With few-shot
    console.print("[green]With few-shot examples:[/green]")
    extractor_fs = IncidentExtractor(use_few_shot=True)
    result_fs = extractor_fs.extract(AMBIGUOUS_MESSAGE)
    print_extraction_result(result_fs, "With Few-Shot")

    # Compare null handling
    console.print("[bold]Null field comparison:[/bold]")
    table = Table()
    table.add_column("Field")
    table.add_column("No Few-Shot", style="red")
    table.add_column("With Few-Shot", style="green")

    nullable_fields = [
        "customer_id", "customer_name",
        "order_id", "amount_mentioned",
    ]
    for field in nullable_fields:
        no_fs_val = str(result_no_fs.data.get(field, "N/A"))
        fs_val = str(result_fs.data.get(field, "N/A"))
        table.add_row(field, no_fs_val, fs_val)

    console.print(table)
    console.print()


def run_part_3() -> None:
    """Validation-retry loop demonstration."""
    console.print(Panel(
        "[bold magenta]PART 3: Validation-Retry Loop[/bold magenta]\n\n"
        "Extraction pipeline with semantic validation.\n"
        "If validation fails, retry with specific error feedback.\n"
        "Watch the retry prompt include the exact error message.",
        border_style="magenta",
    ))

    console.print(
        f"[dim]Message: \"{VALIDATION_TRIGGER_MESSAGE}\"[/dim]\n"
    )

    extractor = IncidentExtractor(use_few_shot=True)
    result = extractor.extract(
        VALIDATION_TRIGGER_MESSAGE,
        max_retries=2,
    )
    print_extraction_result(result, "Part 3 — Validation + Retry")

    if result.retries > 0:
        console.print(
            f"[yellow]⚡ Needed {result.retries} retry attempt(s) "
            f"to pass validation[/yellow]\n"
        )
    else:
        console.print(
            "[green]✓ Passed validation on first attempt[/green]\n"
        )


def run_part_4() -> None:
    """tool_choice demonstration — auto vs any vs forced."""
    console.print(Panel(
        "[bold blue]PART 4: tool_choice Comparison[/bold blue]\n\n"
        "Same message. Same tools. Three tool_choice values.\n"
        "  auto:   Claude decides — may not call any tool\n"
        "  any:    Claude must call a tool — picks which\n"
        "  forced: Claude must call extract_incident specifically",
        border_style="blue",
    ))

    console.print(
        f"[dim]Message: \"{TOOL_CHOICE_MESSAGE}\"[/dim]\n"
    )

    tools = [INCIDENT_SCHEMA]
    messages = [{"role": "user", "content": TOOL_CHOICE_MESSAGE}]

    def describe_response(response) -> tuple[str, str]:
        """
        Inspect ALL content blocks to find any tool_use block.
        Never assume content[0] is a tool block — it may be text.

        Returns (result_description, guaranteed_label)
        """
        tool_block = next(
            (b for b in response.content if b.type == "tool_use"),
            None
        )

        if tool_block:
            return (
                f"Called tool: {tool_block.name}",
                "✓ Tool called"
            )
        else:
            # Extract text if present
            text_block = next(
                (b for b in response.content if b.type == "text"),
                None
            )
            preview = (
                text_block.text if text_block
                else "(no content)"
            )
            return (
                f"Returned text: \"{preview}\"",
                "✗ No tool called"
            )

    # ── auto ──────────────────────────────────────────────────────
    console.print("[dim]Calling with tool_choice='auto'...[/dim]")
    response_auto = create_message(
        messages=messages,
        tools=tools,
        system=DAY_03_EXTRACTION_AGENT,
        tool_choice={"type": "auto"},
    )
    auto_desc, auto_guaranteed = describe_response(response_auto)
    console.print(f"[dim]  stop_reason: {response_auto.stop_reason}[/dim]")

    # ── any ───────────────────────────────────────────────────────
    console.print("[dim]Calling with tool_choice='any'...[/dim]")
    response_any = create_message(
        messages=messages,
        tools=tools,
        system=DAY_03_EXTRACTION_AGENT,
        tool_choice={"type": "any"},
    )
    any_desc, any_guaranteed = describe_response(response_any)
    console.print(f"[dim]  stop_reason: {response_any.stop_reason}[/dim]")

    # ── forced ────────────────────────────────────────────────────
    console.print(
        "[dim]Calling with tool_choice forced to "
        "extract_incident...[/dim]"
    )
    response_forced = create_message(
        messages=messages,
        tools=tools,
        system=DAY_03_EXTRACTION_AGENT,
        tool_choice={
            "type": "tool",
            "name": "extract_incident",
        },
    )
    forced_desc, forced_guaranteed = describe_response(response_forced)
    console.print(
        f"[dim]  stop_reason: {response_forced.stop_reason}[/dim]\n"
    )

    # ── Comparison table ──────────────────────────────────────────
    table = Table(title="tool_choice Comparison")
    table.add_column("tool_choice", style="bold", width=35)
    table.add_column("Result", width=40)
    table.add_column("Tool Called?", width=18)

    table.add_row("auto", auto_desc, auto_guaranteed)
    table.add_row("any", any_desc, any_guaranteed)
    table.add_row(
        'forced {"name": "extract_incident"}',
        forced_desc,
        forced_guaranteed,
    )

    console.print(table)
    console.print(
        "\n[dim]KEY INSIGHT:\n"
        "  auto   → Claude chose whether to call a tool\n"
        "  any    → Claude had to call a tool (but picked which)\n"
        "  forced → Claude had to call extract_incident exactly\n"
        "  For reliable structured output: always use forced.[/dim]\n"
    )

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SupportSentinel Day 3 — Structured Output"
    )
    parser.add_argument(
        "--part",
        type=int,
        choices=[1, 2, 3, 4],
        default=None,
        help="Run a specific part (1-4). Omit to run all.",
    )
    args = parser.parse_args()

    console.print(
        "\n[bold]SupportSentinel — Day 3: Structured Output[/bold]\n"
        "[dim]Imports from: sentinel.extraction + "
        "sentinel.tools.day_03[/dim]\n"
    )

    if args.part == 1:
        run_part_1()
    elif args.part == 2:
        run_part_2()
    elif args.part == 3:
        run_part_3()
    elif args.part == 4:
        run_part_4()
    else:
        run_part_1()
        console.print("─" * 60 + "\n")
        run_part_2()
        console.print("─" * 60 + "\n")
        run_part_3()
        console.print("─" * 60 + "\n")
        run_part_4()