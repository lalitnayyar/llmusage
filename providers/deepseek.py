import json
import requests
from urllib.parse import urlparse

from providers.base import BaseProvider, UsageResult

DEFAULT_URL = "https://api.deepseek.com"


def _origin_base(url: str) -> str:
    """Balance lives at /user/balance on the API host, not under /v1 — strip accidental path prefixes."""
    raw = (url or "").strip() or DEFAULT_URL
    parsed = urlparse(raw)
    if not parsed.scheme and not parsed.netloc and parsed.path and "/" not in parsed.path:
        parsed = urlparse("https://" + parsed.path)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    return DEFAULT_URL.rstrip("/")


class DeepSeekProvider(BaseProvider):
    name = "deepseek"

    def fetch_usage(self) -> UsageResult:
        base = _origin_base(self.api_url or DEFAULT_URL)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

        resp = requests.get(f"{base}/user/balance", headers=headers, timeout=15)
        resp.raise_for_status()
        text = (resp.text or "").strip()
        if not text:
            raise ValueError(
                "DeepSeek returned an empty body. Check API URL (use https://api.deepseek.com with no path) "
                "and that your API key is valid."
            )
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            raise ValueError(
                f"DeepSeek response was not JSON (HTTP {resp.status_code}). "
                f"Check API URL. First bytes: {text[:120]!r}"
            ) from e

        balance_usd = None
        for entry in data.get("balance_infos", []):
            if entry.get("currency", "").upper() == "USD":
                try:
                    balance_usd = float(entry.get("total_balance", 0))
                except (TypeError, ValueError):
                    pass

        return UsageResult(
            tokens_in=0,
            tokens_out=0,
            cost_usd=0.0,
            balance_usd=balance_usd,
            raw_response=json.dumps(data),
        )
