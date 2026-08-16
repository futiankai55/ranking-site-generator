from __future__ import annotations
from datetime import date
from urllib.parse import urlparse

from googleapiclient.discovery import build

from src.analytics import google_auth


def extract_site_url(base_url: str) -> str:
    return f"sc-domain:{urlparse(base_url).netloc}"


def parse_search_rows(response: dict) -> list[dict]:
    """Search Console `searchanalytics.query` のレスポンスを upsert_search_metrics 用のdictリストへ変換する"""
    rows = []
    for row in response.get("rows", []):
        keys = row.get("keys", [])
        rows.append({
            "date": keys[0] if keys else None,
            "clicks": int(row.get("clicks") or 0),
            "impressions": int(row.get("impressions") or 0),
            "ctr": float(row.get("ctr") or 0.0),
            "average_position": float(row.get("position") or 0.0),
        })
    return rows


def fetch_daily_search_metrics(site_url: str, since: date, until: date) -> list[dict]:
    credentials = google_auth.load_credentials()
    service = build("searchconsole", "v1", credentials=credentials, cache_discovery=False)
    body = {
        "startDate": since.isoformat(),
        "endDate": until.isoformat(),
        "dimensions": ["date"],
        "rowLimit": 1000,
    }
    response = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
    return parse_search_rows(response)
