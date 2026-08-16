from __future__ import annotations
from src.config.schema import SiteConfig, RankingItem
from .base import BaseGenerator


class IndividualArticleGenerator(BaseGenerator):
    def __init__(self, config: SiteConfig) -> None:
        super().__init__(config)

    def build_metadata(self, item: RankingItem) -> dict:
        title = f"{item.name}の評判・口コミ・使い方を徹底解説【{self.config.theme}】"
        slug = self._to_slug(f"{self.config.site_id}-{item.name}-review")
        keyword = f"{item.name} 評判 使い方"
        lsi = [
            f"{item.name} 料金",
            f"{item.name} 無料",
            f"{item.name} デメリット",
            f"{item.name} おすすめ",
            f"{item.name} 比較",
        ]
        template = self._load_prompt_template("individual_article")
        prompt = self._render_template(
            template,
            theme=self.config.theme,
            main_keyword=keyword,
            target_audience=self.config.target_audience,
            word_count=3000,
            title=title,
            tool_name=item.name,
            tool_url=item.url,
            category=item.category,
            price_free="あり" if item.price_free else "なし",
            price_paid=item.price_paid,
            description=item.description,
            pros="\n".join(f"- {p}" for p in item.pros),
            cons="\n".join(f"- {c}" for c in item.cons),
            lsi_keywords="\n".join(f"- {k}" for k in lsi),
        )
        return {
            "article_type": "individual",
            "title": title,
            "slug": slug,
            "target_keyword": keyword,
            "tags": [item.name, item.category, self.config.theme, "レビュー"],
            "prompt": prompt,
            "system": self._load_system_prompt(),
        }
