import pytest
from src.analytics.ga4 import parse_traffic_rows
from src.database.models import init_db, get_session, TrafficMetrics
from src.database.repository import upsert_traffic_metrics, get_site_traffic_summary

_TEST_SITE_ID = "test-ga4-site"


@pytest.fixture(autouse=True)
def _cleanup_test_rows():
    init_db()
    yield
    with get_session() as session:
        session.query(TrafficMetrics).filter_by(site_id=_TEST_SITE_ID).delete()
        session.commit()


def _fake_response():
    return {
        "rows": [
            {
                "dimensionValues": [{"value": "20260810"}],
                "metricValues": [{"value": "20"}, {"value": "15"}, {"value": "80"}],
            },
        ]
    }


def test_parse_traffic_rows():
    rows = parse_traffic_rows(_fake_response())
    assert rows == [{
        "date": "2026-08-10",
        "sessions": 20,
        "active_users": 15,
        "page_views": 80,
    }]


def test_parse_traffic_rows_handles_empty_response():
    assert parse_traffic_rows({"rows": []}) == []


def test_upsert_traffic_metrics_inserts_then_updates_same_day():
    upsert_traffic_metrics(
        site_id=_TEST_SITE_ID,
        date="2026-08-10",
        sessions=10,
        active_users=8,
        page_views=40,
    )
    upsert_traffic_metrics(
        site_id=_TEST_SITE_ID,
        date="2026-08-10",
        sessions=15,
        active_users=12,
        page_views=60,
    )

    summary = get_site_traffic_summary(_TEST_SITE_ID)
    assert summary["days_recorded"] == 1
    assert summary["total_sessions"] == 15
    assert summary["total_active_users"] == 12
    assert summary["total_page_views"] == 60
    assert summary["latest_date"] == "2026-08-10"
