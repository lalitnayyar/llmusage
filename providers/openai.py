import json
import requests
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlparse

from providers.base import BaseProvider, UsageResult

DEFAULT_URL = "https://api.openai.com"


def _origin_base(url: str) -> str:
    """Use only scheme + host so pasted paths like /v1/organization/usage/... do not break requests."""
    raw = (url or "").strip() or DEFAULT_URL
    parsed = urlparse(raw)
    if not parsed.scheme and not parsed.netloc and parsed.path and "/" not in parsed.path:
        parsed = urlparse("https://" + parsed.path)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    return DEFAULT_URL.rstrip("/")


def _month_range_utc(today: date) -> tuple[int, int]:
    start = datetime.combine(today.replace(day=1), datetime.min.time(), tzinfo=timezone.utc)
    end = datetime.combine(today + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    return int(start.timestamp()), int(end.timestamp())


def _aggregate_completion_usage(base: str, headers: dict, start_ts: int, end_ts: int) -> tuple[int, int, dict]:
    url = f"{base}/v1/organization/usage/completions"
    params: dict = {
        "start_time": start_ts,
        "end_time": end_ts,
        "bucket_width": "1d",
        "limit": 31,
    }
    tokens_in = 0
    tokens_out = 0
    pages: list[dict] = []
    while True:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        pages.append(data)
        for bucket in data.get("data", []):
            for r in bucket.get("results", []):
                if r.get("object") == "organization.usage.completions.result":
                    tokens_in += int(r.get("input_tokens") or 0)
                    tokens_out += int(r.get("output_tokens") or 0)
        if not data.get("has_more") or not data.get("next_page"):
            break
        params = {"page": data["next_page"]}
    return tokens_in, tokens_out, {"pages": pages}


def _aggregate_org_costs_usd(base: str, headers: dict, start_ts: int, end_ts: int) -> float | None:
    url = f"{base}/v1/organization/costs"
    params: dict = {
        "start_time": start_ts,
        "end_time": end_ts,
        "bucket_width": "1d",
        "limit": 180,
    }
    total = 0.0
    any_row = False
    while True:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code in (401, 403, 404):
            return None
        resp.raise_for_status()
        data = resp.json()
        for bucket in data.get("data", []):
            for r in bucket.get("results", []):
                if r.get("object") != "organization.costs.result":
                    continue
                amt = r.get("amount") or {}
                if (amt.get("currency") or "").lower() == "usd" and amt.get("value") is not None:
                    total += float(amt["value"])
                    any_row = True
        if not data.get("has_more") or not data.get("next_page"):
            break
        params = {"page": data["next_page"]}
    return round(total, 6) if any_row else None


class OpenAIProvider(BaseProvider):
    name = "openai"

    def fetch_usage(self) -> UsageResult:
        base = _origin_base(self.api_url or DEFAULT_URL)
        headers = {"Authorization": f"Bearer {self.api_key}"}

        balance_usd = None
        try:
            sub = requests.get(
                f"{base}/v1/dashboard/billing/subscription",
                headers=headers,
                timeout=15,
            )
            sub.raise_for_status()
            sub_data = sub.json()
            hard_limit = sub_data.get("hard_limit_usd", 0)
            soft_limit = sub_data.get("soft_limit_usd", 0)
            balance_usd = float(hard_limit) if hard_limit else float(soft_limit)
        except Exception:
            pass

        today = date.today()
        start_date = today.replace(day=1).isoformat()
        end_date = (today + timedelta(days=1)).isoformat()
        start_ts, end_ts = _month_range_utc(today)

        usage_resp = requests.get(
            f"{base}/v1/dashboard/billing/usage",
            headers=headers,
            params={"start_date": start_date, "end_date": end_date},
            timeout=15,
        )

        # Project/scoped keys often get 403 on dashboard billing; same as 404 — use org usage API.
        if usage_resp.status_code in (401, 403, 404):
            tokens_in, tokens_out, raw_usage = _aggregate_completion_usage(
                base, headers, start_ts, end_ts
            )
            cost = _aggregate_org_costs_usd(base, headers, start_ts, end_ts)
            if cost is None:
                cost = 0.0
            return UsageResult(
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost_usd=cost,
                balance_usd=balance_usd,
                raw_response=json.dumps({"source": "organization_usage", "usage": raw_usage}),
            )

        usage_resp.raise_for_status()
        data = usage_resp.json()

        total_tokens = data.get("total_tokens", 0)
        cost = data.get("total_usage", 0) / 100.0

        tokens_in = total_tokens // 2
        tokens_out = total_tokens - tokens_in

        return UsageResult(
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=round(cost, 6),
            balance_usd=balance_usd,
            raw_response=json.dumps(data),
        )
