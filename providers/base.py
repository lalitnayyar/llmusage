from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class UsageResult:
    tokens_in: int
    tokens_out: int
    cost_usd: float
    balance_usd: float | None
    raw_response: str  # JSON string


class BaseProvider(ABC):
    name: str = ""

    def __init__(self, api_key: str, api_url: str = ""):
        self.api_key = api_key
        self.api_url = api_url

    @abstractmethod
    def fetch_usage(self) -> UsageResult:
        """Fetch current usage/balance from the provider API."""
