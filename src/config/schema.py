from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, HttpUrl, field_validator


class RankingItem(BaseModel):
    name: str
    url: str
    category: str
    price_free: bool = True
    price_paid: str = "要問い合わせ"
    description: str = ""
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)


class Category(BaseModel):
    name: str
    slug: str
    description: str = ""


class ArticlePlan(BaseModel):
    top_page: int = 1
    ranking_articles: int = 2
    individual_articles: int = 5
    faq_articles: int = 1
    related_articles: int = 0


class SiteConfig(BaseModel):
    site_id: str
    name: str
    theme: str
    target_audience: str
    main_keyword: str
    base_url: str
    publisher: Literal["hugo", "wordpress"] = "hugo"
    article_plan: ArticlePlan = Field(default_factory=ArticlePlan)
    max_monthly_cost_usd: float = 10.0
    ranking_targets: list[RankingItem] = Field(default_factory=list)
    categories: list[Category] = Field(default_factory=list)

    @field_validator("site_id")
    @classmethod
    def site_id_slug(cls, v: str) -> str:
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("site_id must be alphanumeric with hyphens/underscores only")
        return v
