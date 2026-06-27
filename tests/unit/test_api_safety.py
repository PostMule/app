"""Unit tests for postmule.core.api_safety."""

import json
from datetime import date

import pytest

from postmule.core.api_safety import (
    APILimitError,
    APISafetyAgent,
    ProviderLimits,
    build_safety_agent,
)


@pytest.fixture
def limits():
    return ProviderLimits(daily_request_limit=10, daily_token_limit=1000, warn_at_percent=0.80)


@pytest.fixture
def agent(tmp_path, limits):
    return APISafetyAgent("gemini", limits, tmp_path / "usage.json")


class TestAPISafetyAgent:
    def test_records_usage(self, agent, tmp_path):
        agent.check_and_record(tokens=100)
        assert agent._usage.requests == 1
        assert agent._usage.tokens == 100

    def test_raises_on_request_limit(self, agent):
        for _ in range(10):
            agent.check_and_record(tokens=1)
        with pytest.raises(APILimitError, match="request limit"):
            agent.check_and_record(tokens=1)

    def test_raises_on_token_limit(self, agent):
        agent.check_and_record(tokens=999)
        with pytest.raises(APILimitError, match="token limit"):
            agent.check_and_record(tokens=2)

    def test_dry_run_does_not_persist(self, agent):
        agent.check_and_record(tokens=100, dry_run=True)
        assert agent._usage.requests == 0

    def test_persists_to_file(self, agent, tmp_path):
        agent.check_and_record(tokens=200)
        data = json.loads((tmp_path / "usage.json").read_text())
        assert data["requests"] == 1
        assert data["tokens"] == 200

    def test_resets_on_new_day(self, agent):
        agent.check_and_record(tokens=100)
        assert agent._usage.requests == 1
        # Simulate a new day
        agent._usage.date = "2000-01-01"
        agent._maybe_reset_for_new_day()
        assert agent._usage.requests == 0

    def test_monthly_budget_limit(self, tmp_path, limits):
        agent = APISafetyAgent("gemini", limits, tmp_path / "usage.json", monthly_budget_usd=0.01)
        with pytest.raises(APILimitError, match="budget"):
            agent.check_and_record(tokens=1, cost_usd=0.02)

    def test_summary(self, agent):
        agent.check_and_record(tokens=500)
        summary = agent.summary()
        assert summary["provider"] == "gemini"
        assert summary["requests"] == 1
        assert summary["tokens"] == 500

    def test_summary_rounds_cost_to_4_decimal_places(self, tmp_path, limits):
        agent = APISafetyAgent("gemini", limits, tmp_path / "usage.json")
        agent.record_cost(0.123456789)
        summary = agent.summary()
        assert summary["estimated_cost_usd"] == round(0.123456789, 4)

    def test_zero_monthly_budget_disables_cost_limit(self, tmp_path, limits):
        agent = APISafetyAgent("gemini", limits, tmp_path / "usage.json", monthly_budget_usd=0.0)
        # Should not raise even with very high cost
        agent.check_and_record(tokens=1, cost_usd=9999.0)

    def test_persists_across_reinstantiation(self, tmp_path, limits):
        state = tmp_path / "usage.json"
        agent1 = APISafetyAgent("gemini", limits, state)
        agent1.check_and_record(tokens=300)
        agent1.check_and_record(tokens=200)

        agent2 = APISafetyAgent("gemini", limits, state)
        assert agent2._usage.requests == 2
        assert agent2._usage.tokens == 500

    def test_record_additional_tokens(self, agent):
        agent.check_and_record(tokens=100)
        agent.record_additional_tokens(50)
        assert agent._usage.tokens == 150

    def test_record_additional_tokens_negative_is_noop(self, agent):
        agent.check_and_record(tokens=100)
        agent.record_additional_tokens(-10)
        assert agent._usage.tokens == 100

    def test_corrupted_state_file_fallback(self, tmp_path, limits):
        state = tmp_path / "usage.json"
        state.write_text("not valid json", encoding="utf-8")
        agent = APISafetyAgent("gemini", limits, state)
        assert agent._usage.requests == 0
        assert agent._usage.tokens == 0

    def test_build_safety_agent_reads_config(self, tmp_path):
        cfg = {
            "api_safety": {
                "daily_request_limit": 50,
                "daily_token_limit": 5000,
                "warn_at_percent": 70,
                "monthly_cost_budget_usd": 1.50,
            }
        }
        agent = build_safety_agent(cfg, "gemini", tmp_path)
        assert agent.limits.daily_request_limit == 50
        assert agent.limits.daily_token_limit == 5000
        assert agent.limits.warn_at_percent == pytest.approx(0.70)
        assert agent.monthly_budget_usd == pytest.approx(1.50)

    def test_build_safety_agent_uses_defaults_when_no_config(self, tmp_path):
        agent = build_safety_agent({}, "gemini", tmp_path)
        assert agent.limits.daily_request_limit == 1400
        assert agent.limits.daily_token_limit == 900_000


class TestMonthlyCostAccumulator:
    """owner-63 / app #116: monthly dollar cap that is not zeroed daily and not
    consumed by failed calls."""

    def test_record_cost_adds_to_daily_and_monthly(self, agent):
        agent.record_cost(1.5)
        assert agent._usage.estimated_cost_usd == pytest.approx(1.5)
        assert agent._usage.monthly_cost_usd == pytest.approx(1.5)

    def test_record_cost_nonpositive_is_noop(self, agent):
        agent.record_cost(0.0)
        agent.record_cost(-2.0)
        assert agent._usage.monthly_cost_usd == 0.0
        assert agent._usage.estimated_cost_usd == 0.0

    def test_check_and_record_does_not_book_cost(self, tmp_path, limits):
        # Cost is booked only on success via record_cost, so a check (which may be
        # followed by a failed API call) and any retry book zero dollars.
        agent = APISafetyAgent(
            "gemini", limits, tmp_path / "usage.json", monthly_budget_usd=100.0
        )
        agent.check_and_record(tokens=1, cost_usd=2.0)
        agent.check_and_record(tokens=1, cost_usd=2.0)  # retry
        assert agent._usage.monthly_cost_usd == 0.0
        assert agent._usage.estimated_cost_usd == 0.0

    def test_monthly_cost_survives_day_boundary(self, tmp_path, limits):
        agent = APISafetyAgent(
            "gemini", limits, tmp_path / "usage.json", monthly_budget_usd=10.0
        )
        agent.check_and_record(tokens=5)
        agent.record_cost(2.0)
        # Simulate a new day within the same month.
        agent._usage.date = "2000-01-01"
        agent._maybe_reset_for_new_day()
        assert agent._usage.requests == 0  # daily counters reset
        assert agent._usage.estimated_cost_usd == 0.0  # daily cost reset
        assert agent._usage.monthly_cost_usd == pytest.approx(2.0)  # monthly preserved

    def test_monthly_cost_resets_on_new_month(self, agent):
        agent.record_cost(3.0)
        assert agent._usage.monthly_cost_usd == pytest.approx(3.0)
        agent._usage.month = "2000-01"
        agent._maybe_reset_for_new_month()
        assert agent._usage.monthly_cost_usd == 0.0
        assert agent._usage.month == date.today().isoformat()[:7]

    def test_budget_blocks_before_booking(self, tmp_path, limits):
        agent = APISafetyAgent(
            "gemini", limits, tmp_path / "usage.json", monthly_budget_usd=5.0
        )
        agent.record_cost(4.5)
        with pytest.raises(APILimitError, match="month"):
            agent.check_and_record(tokens=1, cost_usd=1.0)  # 4.5 + 1.0 > 5.0
        assert agent._usage.monthly_cost_usd == pytest.approx(4.5)  # not booked

    def test_budget_uses_monthly_total_not_single_call(self, tmp_path, limits):
        # The old bug: a daily-reset counter could never accumulate to a monthly cap.
        # Now the accumulator must trip once month-to-date crosses the budget.
        agent = APISafetyAgent(
            "gemini", limits, tmp_path / "usage.json", monthly_budget_usd=3.0
        )
        agent.record_cost(1.5)
        agent.record_cost(1.0)  # month-to-date 2.5, under budget
        agent.check_and_record(tokens=1, cost_usd=0.4)  # 2.5 + 0.4 = 2.9, ok
        with pytest.raises(APILimitError, match="month"):
            agent.check_and_record(tokens=1, cost_usd=0.6)  # 2.5 + 0.6 = 3.1 > 3.0

    def test_old_format_state_loads_and_initializes_monthly(self, tmp_path, limits):
        state = tmp_path / "usage.json"
        state.write_text(
            json.dumps(
                {
                    "date": date.today().isoformat(),
                    "requests": 5,
                    "tokens": 50,
                    "estimated_cost_usd": 0.0,
                }
            ),
            encoding="utf-8",
        )
        agent = APISafetyAgent("gemini", limits, state)
        assert agent._usage.requests == 5
        assert agent._usage.monthly_cost_usd == 0.0
        # First check initializes the month key without error.
        agent.check_and_record(tokens=1)
        assert agent._usage.month == date.today().isoformat()[:7]

    def test_monthly_cost_persists_across_reinstantiation(self, tmp_path, limits):
        state = tmp_path / "usage.json"
        agent1 = APISafetyAgent("gemini", limits, state)
        agent1.record_cost(2.25)
        agent2 = APISafetyAgent("gemini", limits, state)
        assert agent2._usage.monthly_cost_usd == pytest.approx(2.25)

    def test_default_monthly_budget_is_nonzero(self, tmp_path):
        agent = build_safety_agent({}, "gemini", tmp_path)
        assert agent.monthly_budget_usd > 0
