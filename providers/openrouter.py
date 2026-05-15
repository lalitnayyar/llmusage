import json
import requests
from providers.base import BaseProvider, UsageResult

DEFAULT_URL = "https://openrouter.ai"


class OpenRouterProvider(BaseProvider):
    name = "openrouter"

    def fetch_usage(self) -> UsageResult:
        base = (self.api_url or DEFAULT_URL).rstrip("/")
        headers = {"Authorization": f"Bearer {self.api_key}"}

        resp = requests.get(f"{base}/api/v1/auth/key", headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        # Response shape: { "data": { "usage": <cents>, "limit": <usd>, "limit_remaining": <usd>, ... } }
        inner = data.get("data", data)
        usage_cents = inner.get("usage", 0)
        cost_usd = float(usage_cents) / 100.0 if usage_cents else 0.0
        balance_usd = inner.get("limit_remaining")
        if balance_usd is not None:
            balance_usd = float(balance_usd)

        # OpenRouter key endpoint doesn't break down token counts
        return UsageResult(
            tokens_in=0,
            tokens_out=0,
            cost_usd=round(cost_usd, 6),
            balance_usd=balance_usd,
            raw_response=json.dumps(data),
        )
