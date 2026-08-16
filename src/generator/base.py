from __future__ import annotations
import hashlib
import re
from dataclasses import dataclass
from src.config.schema import SiteConfig
from src.config.loader import load_prompt_template


@dataclass
class ArticleData:
    article_type: str
    title: str
    slug: str
    target_keyword: str
    content: str
    content_hash: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    meta_description: str = ""
    tags: list[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class BaseGenerator:
    def __init__(self, config: SiteConfig) -> None:
        self.config = config

    def _load_system_prompt(self) -> str:
        template = load_prompt_template("system_base")
        return template.replace("{theme}", self.config.theme)

    def _load_prompt_template(self, name: str) -> str:
        return load_prompt_template(name)

    def _compute_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _to_slug(self, text: str) -> str:
        slug = re.sub(r"[^\w\s-]", "", text.lower())
        slug = re.sub(r"[\s_]+", "-", slug)
        return slug.strip("-")

    def _render_template(self, template: str, **kwargs) -> str:
        for key, value in kwargs.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template

    def _extract_meta_description(self, content: str) -> str:
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        for line in lines:
            if not line.startswith("#") and len(line) > 50:
                return line[:120] + "…" if len(line) > 120 else line
        return self.config.main_keyword
