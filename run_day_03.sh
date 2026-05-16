# Step 1 — Tests (no API calls)
pytest tests/test_day_03.py -v

# Step 2 — Verify all prior days still work
pytest tests/test_day_01.py tests/test_day_02.py tests/test_day_03.py -v

# Step 3 — Basic extraction (uses API)
python days/day_03_structured_output/exercise.py --part 1

# Step 4 — Few-shot comparison (uses API — 2 calls)
python days/day_03_structured_output/exercise.py --part 2

# Step 5 — Validation retry loop (uses API)
python days/day_03_structured_output/exercise.py --part 3

# Step 6 — tool_choice comparison (uses API — 3 calls)
python days/day_03_structured_output/exercise.py --part 4

# Step 7 — All parts
python days/day_03_structured_output/exercise.py