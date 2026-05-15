import json
import requests
from providers.base import BaseProvider, UsageResult

DEFAULT_URL = "https://api.anthropic.com"


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def fetch_usage(self) -> UsageResult:
        base = (self.api_url or DEFAULT_URL).rstrip("/")
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        # Usage endpoint — returns monthly usage aggregates
        resp = requests.get(
            f"{base}/v1/usage",
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        # Response shape: { "input_tokens": N, "output_tokens": N, ... }
        tokens_in = data.get("input_tokens", 0)
        tokens_out = data.get("output_tokens", 0)

        # Cost estimation based on Sonnet 3 pricing as a reasonable default
        cost_usd = (tokens_in / 1_000_000 * 3.0) + (tokens_out / 1_000_000 * 15.0)

        return UsageResult(
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=round(cost_usd, 6),
            balance_usd=None,  # Anthropic doesn't expose credit balance via API
            raw_response=json.dumps(data),
        )
