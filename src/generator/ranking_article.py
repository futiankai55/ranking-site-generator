from __future__ import annotations
import json
from src.config.schema import SiteConfig, RankingItem
from .base import BaseGenerator, ArticleData

_LSI_KEYWORDS_TEMPLATE = [
    "{theme} 比較",
    "{theme} おすすめ",
    "{theme} 選び方",
    "{theme} 無料",
    "{theme} 有料",
]


class RankingArticleGenerator(BaseGenerator):
    def __init__(self, config: SiteConfig) -> None:
        super().__init__(config)

    def build_metadata(self, items: list[RankingItem] | None = None, title: str | None = None) -> dict:
        targets = items or self.config.ranking_targets
        title = title or f"{self.config.theme}おすすめランキング{len(targets)}選【比較】"
        slug = self._to_slug(f"{self.config.site_id}-ranking-top{len(targets)}")
        keyword = self.config.main_keyword
        lsi = [k.replace("{theme}", self.config.theme) for k in _LSI_KEYWORDS_TEMPLATE]
        items_json = json.dumps(
            [{"rank": i + 1, **item.model_dump()} for i, item in enumerate(targets)],
            ensure_ascii=False,
            indent=2,
        )
        template = self._load_prompt_template("ranking_article")
        prompt = self._render_template(
            template,
            theme=self.config.theme,
            main_keyword=keyword,
            target_audience=self.config.target_audience,
            word_count=5000,
            title=title,
            ranking_items_json=items_json,
            lsi_keywords="\n".join(f"- {k}" for k in lsi),
            item_count=len(targets),
        )
        return {
            "article_type": "ranking",
            "title": title,
            "slug": slug,
            "target_keyword": keyword,
            "tags": [self.config.theme, "ランキング", "比較"],
            "prompt": prompt,
            "system": self._load_system_prompt(),
        }
