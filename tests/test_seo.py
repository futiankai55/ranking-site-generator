import json
import pytest
from src.config.loader import load_site_config
from src.generator.base import ArticleData
from src.seo.structured_data import build_itemlist_jsonld, build_article_jsonld, build_faq_jsonld
from src.seo.internal_links import build_link_map, inject_internal_links


@pytest.fixture
def config():
    return load_site_config("ai-tools")


@pytest.fixture
def sample_articles(config):
    return [
        ArticleData(
            article_type="ranking",
            title="AIツールランキング",
            slug=f"{config.site_id}-ranking-top5",
            target_keyword="AIツール ランキング",
            content="## ランキング\n\nChatGPTはすばらしい。",
            content_hash="hash1",
            input_tokens=100,
            output_tokens=200,
            cost_usd=0.003,
        ),
        ArticleData(
            article_type="individual",
            title="ChatGPT レビュー",
            slug=f"{config.site_id}-chatgpt-review",
            target_keyword="ChatGPT 評判",
            content="## ChatGPTとは\n\n詳細説明。",
            content_hash="hash2",
            input_tokens=100,
            output_tokens=200,
            cost_usd=0.003,
        ),
    ]


def test_itemlist_jsonld_is_valid(config):
    jsonld_str = build_itemlist_jsonld(config, config.ranking_targets)
    assert "application/ld+json" in jsonld_str
    inner = jsonld_str.split("</script>")[0].split(">", 1)[1]
    data = json.loads(inner)
    assert data["@type"] == "ItemList"
    assert len(data["itemListElement"]) == len(config.ranking_targets)


def test_faq_jsonld_is_valid():
    qa_pairs = [{"question": "Q1?", "answer": "A1"}, {"question": "Q2?", "answer": "A2"}]
    jsonld_str = build_faq_jsonld(qa_pairs)
    inner = jsonld_str.split("</script>")[0].split(">", 1)[1]
    data = json.loads(inner)
    assert data["@type"] == "FAQPage"
    assert len(data["mainEntity"]) == 2


def test_build_link_map_generates_links(config, sample_articles):
    links = build_link_map(config, sample_articles)
    assert isinstance(links, list)


def test_inject_internal_links_appends_links(config, sample_articles):
    links = build_link_map(config, sample_articles)
    article = sample_articles[0]
    result = inject_internal_links(article.content, article, links, config.base_url)
    assert isinstance(result, str)
