import json
import requests
from providers.base import BaseProvider, UsageResult

DEFAULT_URL = "https://generativelanguage.googleapis.com"


class GeminiProvider(BaseProvider):
    name = "gemini"

    def fetch_usage(self) -> UsageResult:
        """
        Google AI Studio doesn't expose a public usage/billing REST endpoint.
        We perform a lightweight models list call purely to validate the key,
        then return zeros — the user can view usage at aistudio.google.com/usage.
        """
        base = (self.api_url or DEFAULT_URL).rstrip("/")
        resp = requests.get(
            f"{base}/v1beta/models",
            params={"key": self.api_key},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        return UsageResult(
            tokens_in=0,
            tokens_out=0,
            cost_usd=0.0,
            balance_usd=None,
            raw_response=json.dumps({"note": "Gemini usage not available via API", "models_count": len(data.get("models", []))}),
        )
