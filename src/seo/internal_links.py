from __future__ import annotations
import re
from src.config.schema import SiteConfig, RankingItem
from src.generator.base import ArticleData


def build_link_map(config: SiteConfig, articles: list[ArticleData]) -> list[dict]:
    links = []
    slug_map = {a.slug: a for a in articles}

    for article in articles:
        for item in config.ranking_targets:
            tool_slug = f"{config.site_id}-{_to_slug(item.name)}-review"
            if article.slug != tool_slug and tool_slug in slug_map:
                links.append({
                    "from_slug": article.slug,
                    "to_slug": tool_slug,
                    "to_type": slug_map[tool_slug].article_type,
                    "anchor_text": f"{item.name}の詳細はこちら",
                })

        ranking_slug = f"{config.site_id}-ranking-top{len(config.ranking_targets)}"
        if article.article_type == "individual" and ranking_slug in slug_map:
            links.append({
                "from_slug": article.slug,
                "to_slug": ranking_slug,
                "to_type": slug_map[ranking_slug].article_type,
                "anchor_text": f"{config.theme}ランキング全体を見る",
            })

    return links


def inject_internal_links(
    content: str,
    article: ArticleData,
    links: list[dict],
    config: SiteConfig,
) -> str:
    outgoing = [l for l in links if l["from_slug"] == article.slug]
    inserted: set[str] = set()

    for link in outgoing:
        if link["to_slug"] in inserted:
            continue
        anchor = link["anchor_text"]
        url = f"{config.base_url.rstrip('/')}/{config.site_id}/{link['to_type']}/{link['to_slug']}/"
        md_link = f"[{anchor}]({url})"
        if anchor not in content and md_link not in content:
            content = content + f"\n\n{md_link}"
        inserted.add(link["to_slug"])

    return content


def _to_slug(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")
