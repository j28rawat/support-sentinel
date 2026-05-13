# 🛡️ SupportSentinel

A production-grade multi-agent AI customer support system built with Claude,
and a structured 10-day learning path for the **Claude Certified Architect:
Foundations** certification exam.

---

## What This Is

**A real system** that autonomously resolves e-commerce support cases —
returns, refunds, shipping issues, escalations — using the Anthropic Claude API.

**A learning path** where each day adds one production layer to the same
codebase while teaching one exam domain deeply. Every day is independently
runnable forever.

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/j28rawat/support-sentinel.git
cd support-sentinel

# 2. Environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# 4. Verify (no API call)
python3 -c "
from sentinel.config.data_loader import MockDataLoader
MockDataLoader().debug_scenario_dates()
"

# 5. Run tests (no API call)
pytest tests/ -v

# 6. Run your first agent
python days/day_01_agentic_loop/exercise.py
```

---

## The 10-Day Path

| Day | Topic | Exam Domain | Weight |
|-----|-------|-------------|--------|
| 1 | Agentic loop — `stop_reason`, tool calling, message history | Agentic Architecture | 27% |
| 2 | Tool design — descriptions, structured errors, misrouting demo | Tool Design & MCP | 18% |
| 3 | Structured output — JSON schemas, validation-retry loops | Prompt Engineering | 20% |
| 4 | Multi-agent — coordinator + subagents in parallel | Agentic Architecture | 27% |
| 5 | Context management — case facts, trimming, scratchpad | Context Management | 15% |
| 6 | Claude Code config — CLAUDE.md, path rules, slash commands | Claude Code | 20% |
| 7 | Hooks — data normalisation, programmatic enforcement | Agentic Architecture | 27% |
| 8 | Escalation — explicit criteria, structured human handoff | Context Management | 15% |
| 9 | Batch processing — Message Batches API, CI/CD integration | Prompt Engineering | 20% |
| 10 | Full integration — FastAPI layer, end-to-end demo | All domains | — |

Each day's folder contains:

```text
days/day_XX_topic/
├── NAVIGATION.md   read-in-this-order guide with line references
├── STUDY_GUIDE.md  concepts + 10-15 exam Q&As with explanations
└── exercise.py     runnable script demonstrating the day's concepts
```
---

## Running Any Day

Because of the versioning contract (see below), every day is
self-contained and independently runnable:

```bash
# Day 1
python days/day_01_agentic_loop/exercise.py --scenario 1

# Day 2
python days/day_02_tool_design/exercise.py --part 2

# Run tests for a specific day
pytest tests/test_day_01.py -v
pytest tests/test_day_02.py -v
```

---

## The Versioning Contract

The single design rule that makes every day independently runnable:

ADDITIVE    New code appended, existing code never modified.
sentinel/core/agentic_loop.py
sentinel/config/prompts.py

VERSIONED   New frozen snapshot per day in day_XX/ subfolder.
sentinel/tools/day_01/   ← frozen after Day 1
sentinel/tools/day_02/   ← frozen after Day 2

`days/day_01/exercise.py` imports from `sentinel.tools.day_01`
and runs correctly in 6 months regardless of what later days add.

---

## Project Structure

```text
sentinel/
├── core/           agentic loop, Claude client, types
├── tools/day_XX/   frozen tool snapshots per day
├── config/         settings, prompts, data loader
├── agents/         multi-agent system (Day 4+)
├── hooks/          enforcement hooks (Day 7+)
├──  extraction/     structured output (Day 3+)
├──  days/           one folder per learning day
├──  data/mock/      dynamic mock e-commerce data
└── tests/          unit tests — no API calls required
```

---

## Requirements

- Python 3.10+
- Anthropic API key — [get one here](https://console.anthropic.com)
- Free tier works for all exercises

---

## License

MIT