# 1. Verify environment
python -c "
from sentinel.config.settings import settings
print(f'Model: {settings.claude_model}')
print(f'Refund limit: {settings.refund_approval_limit}')
print('Settings OK')
"

# 2. Debug the date resolution (no API needed)
python -c "
from sentinel.config.data_loader import MockDataLoader
MockDataLoader().debug_scenario_dates()

# 3. Run unit tests (no API calls)
pytest tests/test_day_01.py -v

# 4. Run Scenario 1 (uses API — watch your usage)
python days/day_01_agentic_loop/exercise.py --scenario 1

# 5. Run Scenario 2 (escalation path)
python days/day_01_agentic_loop/exercise.py --scenario 2

# 6. Run Scenario 3 (discovery path)
python days/day_01_agentic_loop/exercise.py --scenario 3

# 7. Run all three
python days/day_01_agentic_loop/exercise.py