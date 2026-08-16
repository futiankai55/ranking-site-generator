from __future__ import annotations
import json
from src.config.schema import SiteConfig
from .base import BaseGenerator


class FaqArticleGenerator(BaseGenerator):
    def __init__(self, config: SiteConfig) -> None:
        super().__init__(config)

    def build_metadata(self, question_count: int = 10) -> dict:
        title = f"{self.config.theme}に関するよくある質問{question_count}選【Q&A】"
        slug = self._to_slug(f"{self.config.site_id}-faq")
        keyword = f"{self.config.theme} よくある質問"
        items_json = json.dumps(
            [item.model_dump() for item in self.config.ranking_targets],
            ensure_ascii=False,
            indent=2,
        )
        template = self._load_prompt_template("faq_article")
        prompt = self._render_template(
            template,
            theme=self.config.theme,
            main_keyword=keyword,
            target_audience=self.config.target_audience,
            word_count=2000,
            title=title,
            ranking_items_json=items_json,
            question_count=question_count,
        )
        return {
            "article_type": "faq",
            "title": title,
            "slug": slug,
            "target_keyword": keyword,
            "tags": [self.config.theme, "よくある質問", "FAQ"],
            "prompt": prompt,
            "system": self._load_system_prompt(),
        }
