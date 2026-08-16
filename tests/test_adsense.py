import pytest
from src.analytics.adsense import extract_domain, parse_report_rows
from src.database.models import init_db, get_session, AdRevenue
from src.database.repository import upsert_ad_revenue, get_site_revenue_summary

_TEST_SITE_ID = "test-adsense-site"


@pytest.fixture(autouse=True)
def _cleanup_test_rows():
    init_db()
    yield
    with get_session() as session:
        session.query(AdRevenue).filter_by(site_id=_TEST_SITE_ID).delete()
        session.commit()


def _fake_report():
    return {
        "headers": [
            {"name": "DATE"},
            {"name": "DOMAIN_NAME"},
            {"name": "ESTIMATED_EARNINGS"},
            {"name": "CLICKS"},
            {"name": "PAGE_VIEWS"},
            {"name": "IMPRESSIONS"},
            {"name": "COST_PER_CLICK"},
            {"name": "PAGE_VIEWS_CTR"},
        ],
        "rows": [
            {
                "cells": [
                    {"value": "2026-08-10"},
                    {"value": "kenjatimejp.com"},
                    {"value": "1.2345"},
                    {"value": "10"},
                    {"value": "500"},
                    {"value": "600"},
                    {"value": "0.1234"},
                    {"value": "1.6667"},
                ]
            }
        ],
    }


def test_extract_domain():
    assert extract_domain("https://kenjatimejp.com/foo") == "kenjatimejp.com"
    assert extract_domain("https://ai-tools-ranking.example.com") == "ai-tools-ranking.example.com"


def test_parse_report_rows():
    rows = parse_report_rows(_fake_report())
    assert rows == [{
        "date": "2026-08-10",
        "estimated_earnings_usd": 1.2345,
        "clicks": 10,
        "page_views": 500,
        "impressions": 600,
        "cost_per_click_usd": 0.1234,
        "page_views_ctr": 1.6667,
    }]


def test_parse_report_rows_handles_empty_report():
    assert parse_report_rows({"headers": [], "rows": []}) == []


def test_upsert_ad_revenue_inserts_then_updates_same_day():
    upsert_ad_revenue(
        site_id=_TEST_SITE_ID,
        date="2026-08-10",
        estimated_earnings_usd=1.0,
        clicks=5,
        page_views=100,
        impressions=120,
        cost_per_click_usd=0.2,
        page_views_ctr=4.16,
    )
    upsert_ad_revenue(
        site_id=_TEST_SITE_ID,
        date="2026-08-10",
        estimated_earnings_usd=1.5,
        clicks=8,
        page_views=150,
        impressions=180,
        cost_per_click_usd=0.1875,
        page_views_ctr=4.44,
    )

    summary = get_site_revenue_summary(_TEST_SITE_ID)
    assert summary["days_recorded"] == 1
    assert summary["total_earnings_usd"] == pytest.approx(1.5)
    assert summary["total_clicks"] == 8
    assert summary["latest_date"] == "2026-08-10"
