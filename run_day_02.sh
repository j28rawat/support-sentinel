# Step 1 — Tests (no API calls)
pytest tests/test_day_02.py -v

# Step 2 — Verify Day 1 still works
pytest tests/test_day_01.py -v

# Step 3 — Run the misrouting demonstration (uses API)
python days/day_02_tool_design/exercise.py --part 1
python days/day_02_tool_design/exercise.py --part 2

# Step 4 — Run the structured error demonstration
python days/day_02_tool_design/exercise.py --part 3

# Step 5 — Run all parts with comparison table
python days/day_02_tool_design/exercise.py