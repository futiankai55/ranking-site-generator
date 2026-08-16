from __future__ import annotations
from datetime import date
from urllib.parse import urlparse

from googleapiclient.discovery import build

from src.analytics import google_auth

_METRICS = [
    "ESTIMATED_EARNINGS",
    "CLICKS",
    "PAGE_VIEWS",
    "IMPRESSIONS",
    "COST_PER_CLICK",
    "PAGE_VIEWS_CTR",
]


def extract_domain(base_url: str) -> str:
    return urlparse(base_url).netloc


def _report_request_params(account_id: str, domain: str, since: date, until: date) -> dict:
    return {
        "account": f"accounts/{account_id}",
        "dateRange": "CUSTOM",
        "startDate_year": since.year,
        "startDate_month": since.month,
        "startDate_day": since.day,
        "endDate_year": until.year,
        "endDate_month": until.month,
        "endDate_day": until.day,
        "metrics": _METRICS,
        "dimensions": ["DATE", "DOMAIN_NAME"],
        "filters": [f"DOMAIN_NAME=={domain}"],
    }


def parse_report_rows(report: dict) -> list[dict]:
    """AdSense `reports.generate` のレスポンスを upsert_ad_revenue 用のdictリストへ変換する"""
    columns = [header.get("name") for header in report.get("headers", [])]
    rows = []
    for row in report.get("rows", []):
        values = {
            column: cell.get("value")
            for column, cell in zip(columns, row.get("cells", []))
        }
        rows.append({
            "date": values.get("DATE"),
            "estimated_earnings_usd": float(values.get("ESTIMATED_EARNINGS") or 0.0),
            "clicks": int(values.get("CLICKS") or 0),
            "page_views": int(values.get("PAGE_VIEWS") or 0),
            "impressions": int(values.get("IMPRESSIONS") or 0),
            "cost_per_click_usd": float(values.get("COST_PER_CLICK") or 0.0),
            "page_views_ctr": float(values.get("PAGE_VIEWS_CTR") or 0.0),
        })
    return rows


def fetch_daily_revenue(account_id: str, domain: str, since: date, until: date) -> list[dict]:
    credentials = google_auth.load_credentials()
    service = build("adsense", "v2", credentials=credentials, cache_discovery=False)
    params = _report_request_params(account_id, domain, since, until)
    report = service.accounts().reports().generate(**params).execute()
    return parse_report_rows(report)
