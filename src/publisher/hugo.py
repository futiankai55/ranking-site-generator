from __future__ import annotations
import os
from datetime import datetime, timezone
from pathlib import Path
import yaml
from src.config.schema import SiteConfig
from src.generator.base import ArticleData

_OUTPUT_ROOT = Path("output")

_TYPE_TO_SECTION = {
    "ranking": "ranking",
    "individual": "tools",
    "faq": "faq",
    "related": "related",
    "top": "",
}

_HUGO_CONFIG_TOML = """\
baseURL = "{base_url}"
languageCode = "ja"
title = "{name}"
theme = "adsense-ranking"

[params]
  description = "{theme}の最新ランキング・比較・おすすめ情報をお届けします。"
  theme_name = "{theme}"

[taxonomies]
  category = "categories"
  tag = "tags"

[markup]
  [markup.goldmark]
    [markup.goldmark.renderer]
      unsafe = true
"""


def publish(config: SiteConfig, article: ArticleData, dry_run: bool = False) -> Path:
    section = _TYPE_TO_SECTION.get(article.article_type, "posts")
    site_dir = _OUTPUT_ROOT / config.site_id

    if section:
        content_dir = site_dir / "content" / section
    else:
        content_dir = site_dir / "content"

    content_dir.mkdir(parents=True, exist_ok=True)

    filename = "_index.md" if article.article_type == "top" else f"{article.slug}.md"
    output_path = content_dir / filename

    frontmatter = {
        "title": article.title,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lastmod": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "description": article.meta_description,
        "tags": article.tags,
        "draft": False,
        "type": article.article_type,
        "slug": article.slug,
    }

    md_content = f"---\n{yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)}---\n\n{article.content}\n"

    if not dry_run:
        output_path.write_text(md_content, encoding="utf-8")
        _ensure_hugo_config(config, site_dir)

    return output_path


def _ensure_hugo_config(config: SiteConfig, site_dir: Path) -> None:
    config_path = site_dir / "config.toml"
    if not config_path.exists():
        site_dir.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            _HUGO_CONFIG_TOML.format(
                base_url=config.base_url,
                name=config.name,
                theme=config.theme,
            ),
            encoding="utf-8",
        )

    static_dir = site_dir / "static"
    static_dir.mkdir(exist_ok=True)
    layouts_dir = site_dir / "layouts"
    layouts_dir.mkdir(exist_ok=True)
