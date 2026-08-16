from __future__ import annotations
import json
from src.config.schema import SiteConfig, RankingItem
from src.generator.base import ArticleData


def build_article_jsonld(config: SiteConfig, article: ArticleData) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article.title,
        "description": article.meta_description,
        "author": {
            "@type": "Organization",
            "name": config.name,
            "url": config.base_url,
        },
        "publisher": {
            "@type": "Organization",
            "name": config.name,
            "url": config.base_url,
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": f"{config.base_url}/{article.slug}/",
        },
    }
    return f'<script type="application/ld+json">\n{json.dumps(data, ensure_ascii=False, indent=2)}\n</script>'


def build_itemlist_jsonld(config: SiteConfig, items: list[RankingItem]) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{config.theme}ランキング",
        "url": config.base_url,
        "numberOfItems": len(items),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": item.name,
                "url": item.url,
                "description": item.description,
            }
            for i, item in enumerate(items)
        ],
    }
    return f'<script type="application/ld+json">\n{json.dumps(data, ensure_ascii=False, indent=2)}\n</script>'


def build_faq_jsonld(qa_pairs: list[dict]) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": qa["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": qa["answer"],
                },
            }
            for qa in qa_pairs
        ],
    }
    return f'<script type="application/ld+json">\n{json.dumps(data, ensure_ascii=False, indent=2)}\n</script>'


def build_breadcrumb_jsonld(config: SiteConfig, crumbs: list[dict]) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": crumb["name"],
                "item": crumb["url"],
            }
            for i, crumb in enumerate(crumbs)
        ],
    }
    return f'<script type="application/ld+json">\n{json.dumps(data, ensure_ascii=False, indent=2)}\n</script>'


def inject_jsonld(content: str, jsonld: str) -> str:
    return content + f"\n\n{jsonld}\n"
