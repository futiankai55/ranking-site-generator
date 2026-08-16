import pytest
from pathlib import Path
from unittest.mock import MagicMock
from src.config.loader import load_site_config
from src.generator.base import ArticleData
from src.publisher import hugo


@pytest.fixture
def config():
    return load_site_config("ai-tools")


@pytest.fixture
def sample_article():
    return ArticleData(
        article_type="ranking",
        title="AIツールおすすめランキング5選",
        slug="ai-tools-ranking-top5",
        target_keyword="AIツール ランキング",
        content="## AIツールランキング\n\nこれはテスト記事です。",
        content_hash="abc123",
        input_tokens=100,
        output_tokens=200,
        cost_usd=0.003,
        meta_description="AIツールのランキング記事です。",
        tags=["AIツール", "ランキング"],
    )


def test_publish_dry_run_returns_path(config, sample_article, tmp_path, monkeypatch):
    monkeypatch.setattr(hugo, "_OUTPUT_ROOT", tmp_path)
    path = hugo.publish(config, sample_article, dry_run=True)
    assert isinstance(path, Path)
    assert not path.exists()


def test_publish_creates_markdown_file(config, sample_article, tmp_path, monkeypatch):
    monkeypatch.setattr(hugo, "_OUTPUT_ROOT", tmp_path)
    path = hugo.publish(config, sample_article, dry_run=False)
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "title:" in content
    assert sample_article.title in content
    assert "## AIツールランキング" in content


def test_publish_creates_hugo_config(config, sample_article, tmp_path, monkeypatch):
    monkeypatch.setattr(hugo, "_OUTPUT_ROOT", tmp_path)
    hugo.publish(config, sample_article, dry_run=False)
    config_path = tmp_path / config.site_id / "config.toml"
    assert config_path.exists()
