import pytest
from src.config.loader import load_site_config, list_site_ids
from src.config.schema import SiteConfig


def test_load_ai_tools_config():
    config = load_site_config("ai-tools")
    assert config.site_id == "ai-tools"
    assert config.name == "AIツールランキング"
    assert len(config.ranking_targets) > 0
    assert config.publisher == "hugo"


def test_config_has_valid_ranking_targets():
    config = load_site_config("ai-tools")
    for item in config.ranking_targets:
        assert item.name
        assert item.url
        assert item.category


def test_list_site_ids_includes_ai_tools():
    ids = list_site_ids()
    assert "ai-tools" in ids


def test_invalid_site_id_raises():
    with pytest.raises(FileNotFoundError):
        load_site_config("nonexistent-site")
