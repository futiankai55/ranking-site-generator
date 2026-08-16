from __future__ import annotations
from datetime import datetime
from sqlalchemy.orm import Session
from .models import Site, Article, InternalLink, AdRevenue, SearchMetrics, get_session
from src.config.schema import SiteConfig


def upsert_site(config: SiteConfig) -> None:
    with get_session() as session:
        existing = session.get(Site, config.site_id)
        if existing:
            existing.name = config.name
            existing.theme = config.theme
            existing.base_url = config.base_url
            existing.publisher = config.publisher
        else:
            session.add(Site(
                id=config.site_id,
                name=config.name,
                theme=config.theme,
                base_url=config.base_url,
                publisher=config.publisher,
            ))
        session.commit()


def get_article_by_slug(site_id: str, slug: str) -> Article | None:
    with get_session() as session:
        return session.query(Article).filter_by(site_id=site_id, slug=slug).first()


def is_duplicate(content_hash: str) -> bool:
    with get_session() as session:
        return session.query(Article).filter_by(content_hash=content_hash).first() is not None


def save_article(
    site_id: str,
    article_type: str,
    title: str,
    slug: str,
    target_keyword: str,
    content_hash: str,
    output_path: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    status: str = "published",
) -> Article:
    with get_session() as session:
        existing = session.query(Article).filter_by(site_id=site_id, slug=slug).first()
        now = datetime.utcnow()
        if existing:
            existing.title = title
            existing.content_hash = content_hash
            existing.output_path = output_path
            existing.input_tokens = input_tokens
            existing.output_tokens = output_tokens
            existing.cost_usd = cost_usd
            existing.status = status
            existing.generated_at = now
            existing.published_at = now if status == "published" else None
            session.commit()
            return existing
        article = Article(
            site_id=site_id,
            article_type=article_type,
            title=title,
            slug=slug,
            target_keyword=target_keyword,
            content_hash=content_hash,
            output_path=output_path,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            status=status,
            generated_at=now,
            published_at=now if status == "published" else None,
        )
        session.add(article)
        session.commit()
        return article


def get_site_articles(site_id: str) -> list[Article]:
    with get_session() as session:
        return session.query(Article).filter_by(site_id=site_id).all()


def get_site_cost_summary(site_id: str) -> dict:
    articles = get_site_articles(site_id)
    return {
        "article_count": len(articles),
        "total_input_tokens": sum(a.input_tokens for a in articles),
        "total_output_tokens": sum(a.output_tokens for a in articles),
        "total_cost_usd": sum(a.cost_usd for a in articles),
    }


def upsert_ad_revenue(
    site_id: str,
    date: str,
    estimated_earnings_usd: float,
    clicks: int,
    page_views: int,
    impressions: int,
    cost_per_click_usd: float,
    page_views_ctr: float,
) -> AdRevenue:
    with get_session() as session:
        existing = session.query(AdRevenue).filter_by(site_id=site_id, date=date).first()
        now = datetime.utcnow()
        if existing:
            existing.estimated_earnings_usd = estimated_earnings_usd
            existing.clicks = clicks
            existing.page_views = page_views
            existing.impressions = impressions
            existing.cost_per_click_usd = cost_per_click_usd
            existing.page_views_ctr = page_views_ctr
            existing.synced_at = now
            session.commit()
            return existing
        revenue = AdRevenue(
            site_id=site_id,
            date=date,
            estimated_earnings_usd=estimated_earnings_usd,
            clicks=clicks,
            page_views=page_views,
            impressions=impressions,
            cost_per_click_usd=cost_per_click_usd,
            page_views_ctr=page_views_ctr,
            synced_at=now,
        )
        session.add(revenue)
        session.commit()
        return revenue


def get_site_revenue_summary(site_id: str) -> dict:
    with get_session() as session:
        rows = session.query(AdRevenue).filter_by(site_id=site_id).all()
        return {
            "days_recorded": len(rows),
            "total_earnings_usd": sum(r.estimated_earnings_usd for r in rows),
            "total_clicks": sum(r.clicks for r in rows),
            "total_page_views": sum(r.page_views for r in rows),
            "latest_date": max((r.date for r in rows), default=None),
        }


def upsert_search_metrics(
    site_id: str,
    date: str,
    clicks: int,
    impressions: int,
    ctr: float,
    average_position: float,
) -> SearchMetrics:
    with get_session() as session:
        existing = session.query(SearchMetrics).filter_by(site_id=site_id, date=date).first()
        now = datetime.utcnow()
        if existing:
            existing.clicks = clicks
            existing.impressions = impressions
            existing.ctr = ctr
            existing.average_position = average_position
            existing.synced_at = now
            session.commit()
            return existing
        metrics = SearchMetrics(
            site_id=site_id,
            date=date,
            clicks=clicks,
            impressions=impressions,
            ctr=ctr,
            average_position=average_position,
            synced_at=now,
        )
        session.add(metrics)
        session.commit()
        return metrics


def get_site_search_summary(site_id: str) -> dict:
    with get_session() as session:
        rows = session.query(SearchMetrics).filter_by(site_id=site_id).all()
        total_clicks = sum(r.clicks for r in rows)
        total_impressions = sum(r.impressions for r in rows)
        weighted_position = sum(r.average_position * r.impressions for r in rows)
        return {
            "days_recorded": len(rows),
            "total_clicks": total_clicks,
            "total_impressions": total_impressions,
            "avg_ctr": (total_clicks / total_impressions) if total_impressions else 0.0,
            "avg_position": (weighted_position / total_impressions) if total_impressions else 0.0,
            "latest_date": max((r.date for r in rows), default=None),
        }


def save_internal_links(site_id: str, links: list[dict]) -> None:
    with get_session() as session:
        session.query(InternalLink).filter_by(site_id=site_id).delete()
        for link in links:
            session.add(InternalLink(
                site_id=site_id,
                from_slug=link["from_slug"],
                to_slug=link["to_slug"],
                anchor_text=link["anchor_text"],
            ))
        session.commit()
