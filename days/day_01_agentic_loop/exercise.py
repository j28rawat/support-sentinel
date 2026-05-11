"""
days/day_01_agentic_loop/exercise.py
======================================
Day 1 Exercise: Your first working agentic loop.

WHAT THIS DEMONSTRATES:
    - Claude autonomously handles customer support requests
    - stop_reason drives every loop decision
    - Tool results accumulated in message history
    - Three distinct resolution paths (standard, escalated, discovery)

IMPORTS:
    This file imports from sentinel.tools.day_01 — the Day 1 snapshot.
    It will run correctly forever, regardless of what later days add.

USAGE:
    # From project root (with .venv active):
    python days/day_01_agentic_loop/exercise.py

    # To run a specific scenario:
    python days/day_01_agentic_loop/exercise.py --scenario 2

WHAT TO OBSERVE:
    Watch the console output carefully:
    - "stop_reason: tool_use"  → Claude wants a tool, loop continues
    - "stop_reason: end_turn"  → Claude is done, loop exits
    - Each tool call logged with input + result
    - Final summary shows tools used and iteration count
"""

import sys
import os
import argparse

# Ensure project root is on Python path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..")
))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sentinel.core.agentic_loop import run_agentic_loop
from sentinel.config.prompts import DAY_01_SUPPORT_AGENT

# ── Day 1 versioned imports ───────────────────────────────────────────────────
# These always point to the Day 1 snapshot — never break.
from sentinel.tools.day_01 import ALL_TOOL_DEFINITIONS, execute_tool

console = Console()

# ── Test Scenarios ────────────────────────────────────────────────────────────
# Three scenarios exercising different loop paths.
# Each one tests a different aspect of the agentic loop.

SCENARIOS = {
    1: {
        "name": "Standard Return — Happy Path",
        "description": (
            "Customer provides order ID and wants a refund. "
            "Expected path: get_customer → lookup_order → "
            "check_eligibility → process_refund → end_turn. "
            "Tests: basic loop, prerequisite chain, successful resolution."
        ),
        "message": (
            "Hi, I'm customer C001. I'd like to return my headphones "
            "from order ORD-10045. They stopped working after a week. "
            "Can I get a refund please?"
        ),
    },
    2: {
        "name": "High-Value Refund — Escalation Path",
        "description": (
            "Refund amount exceeds $500 auto-approval limit. "
            "Expected path: get_customer → lookup_order → "
            "check_eligibility → process_refund (blocked) → "
            "escalate_to_human → end_turn. "
            "Tests: business rule enforcement, escalation trigger."
        ),
        "message": (
            "I'm customer C001. I want a full refund for my Smart Watch "
            "from order ORD-10091. It never worked properly from day one."
        ),
    },
    3: {
        "name": "No Order ID — Discovery Path",
        "description": (
            "Customer doesn't provide an order ID. Agent must discover "
            "which order they mean. "
            "Expected path: get_customer → get_order_history → "
            "(finds in-transit order) → end_turn. "
            "Tests: ambiguous intent, history lookup, no order ID."
        ),
        "message": (
            "Hi there, I'm James — customer C002. "
            "I ordered something a few days ago and haven't received it. "
            "Can you tell me what's happening with my delivery?"
        ),
    },
}


def print_scenario_header(scenario_num: int, scenario: dict) -> None:
    console.print(Panel(
        f"[bold]Scenario {scenario_num}: {scenario['name']}[/bold]\n\n"
        f"{scenario['description']}\n\n"
        f"[italic]Customer message:[/italic]\n"
        f"[cyan]\"{scenario['message']}\"[/cyan]",
        title="[bold blue]SupportSentinel — Day 1[/bold blue]",
        border_style="blue",
    ))


def print_result_summary(
    scenario_num: int,
    scenario: dict,
    result
) -> None:
    table = Table(title=f"Result — Scenario {scenario_num}")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Resolved", "✓ Yes" if result.resolved else "✗ No")
    table.add_row("Escalated", "Yes" if result.escalated else "No")
    table.add_row("Iterations", str(result.iterations))
    table.add_row("Tools Used", " → ".join(result.tools_used()))
    table.add_row(
        "Final Response",
        result.final_response[:200] + "..."
        if len(result.final_response) > 200
        else result.final_response
    )

    console.print(table)
    console.print()


def run_scenario(scenario_num: int) -> None:
    scenario = SCENARIOS[scenario_num]
    print_scenario_header(scenario_num, scenario)

    result = run_agentic_loop(
        system_prompt=DAY_01_SUPPORT_AGENT,
        initial_message=scenario["message"],
        tools=ALL_TOOL_DEFINITIONS,
        tool_executor=execute_tool,
    )

    print_result_summary(scenario_num, scenario, result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SupportSentinel Day 1 — Agentic Loop Exercise"
    )
    parser.add_argument(
        "--scenario",
        type=int,
        choices=[1, 2, 3],
        default=None,
        help="Run a specific scenario (1, 2, or 3). "
             "Omit to run all three."
    )
    args = parser.parse_args()

    console.print(
        "\n[bold]SupportSentinel — Day 1: The Agentic Loop[/bold]\n"
        "[dim]Imports from: sentinel.tools.day_01 (frozen snapshot)[/dim]\n"
    )

    if args.scenario:
        run_scenario(args.scenario)
    else:
        for num in SCENARIOS:
            run_scenario(num)
            console.print("─" * 60 + "\n")