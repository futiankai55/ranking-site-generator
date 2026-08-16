import pytest
from src.config.loader import load_site_config
from src.generator.ranking_article import RankingArticleGenerator
from src.generator.individual_article import IndividualArticleGenerator
from src.generator.faq_article import FaqArticleGenerator


@pytest.fixture
def config():
    return load_site_config("ai-tools")


def test_ranking_article_generator(config):
    gen = RankingArticleGenerator(config)
    meta = gen.build_metadata()
    assert meta["article_type"] == "ranking"
    assert meta["title"]
    assert meta["slug"]
    assert meta["target_keyword"]
    assert meta["prompt"]
    assert meta["system"]


def test_individual_article_generator(config):
    item = config.ranking_targets[0]
    gen = IndividualArticleGenerator(config)
    meta = gen.build_metadata(item)
    assert meta["article_type"] == "individual"
    assert item.name in meta["title"]
    assert meta["slug"]
    assert meta["prompt"]


def test_faq_article_generator(config):
    gen = FaqArticleGenerator(config)
    meta = gen.build_metadata(question_count=5)
    assert meta["article_type"] == "faq"
    assert meta["slug"].endswith("faq")


def test_ranking_slug_is_deterministic(config):
    gen = RankingArticleGenerator(config)
    m1 = gen.build_metadata()
    m2 = gen.build_metadata()
    assert m1["slug"] == m2["slug"]
