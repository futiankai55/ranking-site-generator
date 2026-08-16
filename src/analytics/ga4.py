from __future__ import annotations
from datetime import date, datetime

from googleapiclient.discovery import build

from src.analytics import google_auth


def _format_date(raw: str) -> str:
    return datetime.strptime(raw, "%Y%m%d").strftime("%Y-%m-%d")


def parse_traffic_rows(response: dict) -> list[dict]:
    """GA4 Data API `properties.runReport` のレスポンスを upsert_traffic_metrics 用のdictリストへ変換する"""
    rows = []
    for row in response.get("rows", []):
        dimension_values = row.get("dimensionValues", [])
        metric_values = row.get("metricValues", [])
        rows.append({
            "date": _format_date(dimension_values[0]["value"]) if dimension_values else None,
            "sessions": int(metric_values[0]["value"]) if len(metric_values) > 0 else 0,
            "active_users": int(metric_values[1]["value"]) if len(metric_values) > 1 else 0,
            "page_views": int(metric_values[2]["value"]) if len(metric_values) > 2 else 0,
        })
    return rows


def fetch_daily_traffic(property_id: str, since: date, until: date) -> list[dict]:
    credentials = google_auth.load_credentials()
    service = build("analyticsdata", "v1beta", credentials=credentials, cache_discovery=False)
    body = {
        "dateRanges": [{"startDate": since.isoformat(), "endDate": until.isoformat()}],
        "dimensions": [{"name": "date"}],
        "metrics": [{"name": "sessions"}, {"name": "activeUsers"}, {"name": "screenPageViews"}],
    }
    response = service.properties().runReport(property=f"properties/{property_id}", body=body).execute()
    return parse_traffic_rows(response)
