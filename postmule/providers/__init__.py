from dataclasses import dataclass


@dataclass
class HealthResult:
    ok: bool
    status: str  # "ok" | "warn" | "error"
    message: str = ""
