from __future__ import annotations
import os
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, String, Integer, Float, DateTime, Text, Boolean,
    UniqueConstraint, ForeignKey,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/db/sites.db")
engine = create_engine(_DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    theme: Mapped[str] = mapped_column(String, nullable=False)
    base_url: Mapped[str] = mapped_column(String, nullable=False)
    publisher: Mapped[str] = mapped_column(String, default="hugo")
    status: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (UniqueConstraint("site_id", "slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[str] = mapped_column(String, ForeignKey("sites.id"), nullable=False)
    article_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False)
    target_keyword: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="draft")
    content_hash: Mapped[str | None] = mapped_column(String)
    output_path: Mapped[str | None] = mapped_column(String)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime)
    published_at: Mapped[datetime | None] = mapped_column(DateTime)


class AdRevenue(Base):
    __tablename__ = "ad_revenue"
    __table_args__ = (UniqueConstraint("site_id", "date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[str] = mapped_column(String, ForeignKey("sites.id"), nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)
    estimated_earnings_usd: Mapped[float] = mapped_column(Float, default=0.0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    page_views: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    cost_per_click_usd: Mapped[float] = mapped_column(Float, default=0.0)
    page_views_ctr: Mapped[float] = mapped_column(Float, default=0.0)
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class SearchMetrics(Base):
    __tablename__ = "search_metrics"
    __table_args__ = (UniqueConstraint("site_id", "date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[str] = mapped_column(String, ForeignKey("sites.id"), nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    ctr: Mapped[float] = mapped_column(Float, default=0.0)
    average_position: Mapped[float] = mapped_column(Float, default=0.0)
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class InternalLink(Base):
    __tablename__ = "internal_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[str] = mapped_column(String, ForeignKey("sites.id"), nullable=False)
    from_slug: Mapped[str] = mapped_column(String, nullable=False)
    to_slug: Mapped[str] = mapped_column(String, nullable=False)
    anchor_text: Mapped[str] = mapped_column(String, nullable=False)


def init_db() -> None:
    os.makedirs("data/db", exist_ok=True)
    Base.metadata.create_all(engine)


def get_session() -> Session:
    return SessionLocal()
