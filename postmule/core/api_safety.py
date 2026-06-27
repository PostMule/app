"""
API Safety Agent — tracks usage, enforces hard limits, warns at thresholds.

Persists daily usage counters to a JSON file so limits survive process restarts.
Call check_and_record() before every API call.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

log = logging.getLogger("postmule.api_safety")


class APILimitError(Exception):
    """Raised when a hard API limit would be exceeded."""


@dataclass
class ProviderLimits:
    daily_request_limit: int = 1400
    daily_token_limit: int = 900_000
    warn_at_percent: float = 0.80


@dataclass
class DayUsage:
    date: str = ""
    requests: int = 0
    tokens: int = 0
    estimated_cost_usd: float = 0.0
    # Monthly accumulators (owner-63 / app #116). The daily counters above reset
    # every calendar day; these reset only when the calendar month changes, so a
    # monthly dollar cap is compared against month-to-date spend, not a single day's.
    month: str = ""
    monthly_cost_usd: float = 0.0


class APISafetyAgent:
    """
    Tracks daily API usage for a named provider and enforces limits.

    Usage:
        agent = APISafetyAgent("gemini", limits, state_file)
        agent.check_and_record(tokens=1200)  # raises if limit exceeded
    """

    def __init__(
        self,
        provider: str,
        limits: ProviderLimits,
        state_file: Path,
        monthly_budget_usd: float = 0.0,
    ) -> None:
        self.provider = provider
        self.limits = limits
        self.state_file = state_file
        self.monthly_budget_usd = monthly_budget_usd
        self._usage = self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_and_record(
        self,
        tokens: int = 0,
        cost_usd: float = 0.0,
        dry_run: bool = False,
    ) -> None:
        """
        Check whether making an API call with *tokens* tokens would exceed limits.
        If safe, record the usage. If over limit, raise APILimitError.

        Args:
            tokens:   Estimated tokens for this call.
            cost_usd: Estimated cost for this call.
            dry_run:  If True, check limits but don't persist usage.

        Raises:
            APILimitError: If a hard limit would be exceeded.
        """
        self._maybe_reset_for_new_day()
        self._maybe_reset_for_new_month()
        usage = self._usage

        new_requests = usage.requests + 1
        new_tokens = usage.tokens + tokens
        # Estimated month-to-date spend if this call were made. Used for the pre-call
        # budget gate only; the dollars are not booked here (see record_cost) so a
        # failed API call after this check costs nothing.
        projected_monthly_cost = usage.monthly_cost_usd + cost_usd

        # Hard limits
        if new_requests > self.limits.daily_request_limit:
            raise APILimitError(
                f"{self.provider} daily request limit reached "
                f"({self.limits.daily_request_limit} req/day).\n"
                "PostMule will resume processing tomorrow.\n"
                "To increase this limit, edit api_safety in config.yaml."
            )

        if new_tokens > self.limits.daily_token_limit:
            raise APILimitError(
                f"{self.provider} daily token limit reached "
                f"({self.limits.daily_token_limit:,} tokens/day).\n"
                "PostMule will resume processing tomorrow."
            )

        if self.monthly_budget_usd > 0 and projected_monthly_cost > self.monthly_budget_usd:
            raise APILimitError(
                f"Monthly cost budget exceeded "
                f"(${self.monthly_budget_usd:.2f}/month limit; "
                f"${usage.monthly_cost_usd:.2f} spent month-to-date).\n"
                "Adjust monthly_cost_budget_usd in config.yaml."
            )

        # Warnings
        req_pct = new_requests / self.limits.daily_request_limit
        tok_pct = new_tokens / self.limits.daily_token_limit if self.limits.daily_token_limit else 0

        if req_pct >= self.limits.warn_at_percent:
            log.warning(
                f"{self.provider}: {req_pct:.0%} of daily request limit used "
                f"({new_requests}/{self.limits.daily_request_limit})"
            )
        if tok_pct >= self.limits.warn_at_percent:
            log.warning(
                f"{self.provider}: {tok_pct:.0%} of daily token limit used "
                f"({new_tokens:,}/{self.limits.daily_token_limit:,})"
            )

        if not dry_run:
            # Book the request/token counters pre-call (conservative against provider
            # quota — a failed attempt may still have reached the provider). Dollars are
            # booked only on success via record_cost so failures never consume budget.
            usage.requests = new_requests
            usage.tokens = new_tokens
            self._save()

    def summary(self) -> dict[str, Any]:
        """Return current day's usage as a dict (for inclusion in daily email)."""
        self._maybe_reset_for_new_day()
        self._maybe_reset_for_new_month()
        u = self._usage
        return {
            "provider": self.provider,
            "date": u.date,
            "requests": u.requests,
            "request_limit": self.limits.daily_request_limit,
            "tokens": u.tokens,
            "token_limit": self.limits.daily_token_limit,
            "estimated_cost_usd": round(u.estimated_cost_usd, 4),
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> DayUsage:
        today = date.today().isoformat()
        if not self.state_file.exists():
            return DayUsage(date=today, month=today[:7])
        try:
            raw = json.loads(self.state_file.read_text(encoding="utf-8"))
            # Old-format files (pre owner-63) carry no month/monthly_cost_usd keys;
            # the dataclass defaults fill them and the first check sets the month key.
            return DayUsage(**raw)
        except Exception:
            return DayUsage(date=today, month=today[:7])

    def record_additional_tokens(self, extra_tokens: int) -> None:
        """
        Add extra_tokens to today's recorded token count after an API call
        returned higher actual usage than the pre-call estimate.
        Does not re-check limits (the call already happened).
        """
        if extra_tokens <= 0:
            return
        self._usage.tokens += extra_tokens
        self._save()

    def record_cost(self, actual_cost_usd: float) -> None:
        """
        Book the actual dollar cost of a completed API call after it succeeded.

        Adds to both the daily display total (estimated_cost_usd, shown in the daily
        email) and the monthly accumulator (monthly_cost_usd, enforced by the budget
        gate in check_and_record). Called only on success so a failed call books no
        dollars. Like record_additional_tokens, this does not re-check limits — the
        call already happened.
        """
        if actual_cost_usd <= 0:
            return
        self._usage.estimated_cost_usd += actual_cost_usd
        self._usage.monthly_cost_usd += actual_cost_usd
        log.debug(f"{self.provider}: recorded ${actual_cost_usd:.6f} (month-to-date "
                  f"${self._usage.monthly_cost_usd:.4f})")
        self._save()

    def _save(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "date": self._usage.date,
            "requests": self._usage.requests,
            "tokens": self._usage.tokens,
            "estimated_cost_usd": self._usage.estimated_cost_usd,
            "month": self._usage.month,
            "monthly_cost_usd": self._usage.monthly_cost_usd,
        }
        content = json.dumps(data, indent=2)
        fd, tmp = tempfile.mkstemp(dir=self.state_file.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(tmp, self.state_file)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def _maybe_reset_for_new_day(self) -> None:
        today = date.today().isoformat()
        if self._usage.date != today:
            log.debug(f"{self.provider}: new day — resetting daily usage counters")
            # Reset only the daily fields; the monthly accumulator persists across days
            # (it is cleared separately by _maybe_reset_for_new_month).
            self._usage.date = today
            self._usage.requests = 0
            self._usage.tokens = 0
            self._usage.estimated_cost_usd = 0.0
            self._save()

    def _maybe_reset_for_new_month(self) -> None:
        this_month = date.today().isoformat()[:7]
        if self._usage.month != this_month:
            log.debug(f"{self.provider}: new month — resetting monthly cost accumulator")
            self._usage.month = this_month
            self._usage.monthly_cost_usd = 0.0
            self._save()


def build_safety_agent(config, provider_name: str, state_dir: Path) -> APISafetyAgent:
    """Convenience factory: build agent from config dict for any LLM provider."""
    safety_cfg = config.get("api_safety") or {}
    limits = ProviderLimits(
        daily_request_limit=safety_cfg.get("daily_request_limit", 1400),
        daily_token_limit=safety_cfg.get("daily_token_limit", 900_000),
        warn_at_percent=safety_cfg.get("warn_at_percent", 80) / 100,
    )
    # Default the monthly dollar cap ON (owner-63 / app #116) so a paid-key user who
    # forgets to set one is still protected. The free-tier default records $0 of cost
    # (usd_per_1k_tokens default 0.0), so this cap never fires there — no false stop.
    monthly_budget = safety_cfg.get("monthly_cost_budget_usd", 5.00)
    return APISafetyAgent(
        provider=provider_name,
        limits=limits,
        state_file=state_dir / f"api_usage_{provider_name}.json",
        monthly_budget_usd=float(monthly_budget),
    )
