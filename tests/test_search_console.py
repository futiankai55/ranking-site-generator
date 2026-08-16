import pytest
from src.analytics.search_console import extract_site_url, parse_search_rows
from src.database.models import init_db, get_session, SearchMetrics
from src.database.repository import upsert_search_metrics, get_site_search_summary

_TEST_SITE_ID = "test-search-console-site"


@pytest.fixture(autouse=True)
def _cleanup_test_rows():
    init_db()
    yield
    with get_session() as session:
        session.query(SearchMetrics).filter_by(site_id=_TEST_SITE_ID).delete()
        session.commit()


def _fake_response():
    return {
        "rows": [
            {"keys": ["2026-08-10"], "clicks": 12, "impressions": 300, "ctr": 0.04, "position": 5.5},
        ]
    }


def test_extract_site_url():
    assert extract_site_url("https://kenjatimejp.com/foo") == "sc-domain:kenjatimejp.com"


def test_parse_search_rows():
    rows = parse_search_rows(_fake_response())
    assert rows == [{
        "date": "2026-08-10",
        "clicks": 12,
        "impressions": 300,
        "ctr": 0.04,
        "average_position": 5.5,
    }]


def test_parse_search_rows_handles_empty_response():
    assert parse_search_rows({"rows": []}) == []


def test_upsert_search_metrics_inserts_then_updates_same_day():
    upsert_search_metrics(
        site_id=_TEST_SITE_ID,
        date="2026-08-10",
        clicks=10,
        impressions=200,
        ctr=0.05,
        average_position=6.0,
    )
    upsert_search_metrics(
        site_id=_TEST_SITE_ID,
        date="2026-08-10",
        clicks=15,
        impressions=250,
        ctr=0.06,
        average_position=5.0,
    )

    summary = get_site_search_summary(_TEST_SITE_ID)
    assert summary["days_recorded"] == 1
    assert summary["total_clicks"] == 15
    assert summary["total_impressions"] == 250
    assert summary["avg_ctr"] == pytest.approx(15 / 250)
    assert summary["avg_position"] == pytest.approx(5.0)
    assert summary["latest_date"] == "2026-08-10"
