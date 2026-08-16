from __future__ import annotations
import yaml
from pathlib import Path
from .schema import SiteConfig

_CONFIG_DIR = Path(__file__).parent.parent.parent / "config" / "sites"


def load_site_config(site_id: str) -> SiteConfig:
    config_path = _CONFIG_DIR / f"{site_id}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Site config not found: {config_path}")
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return SiteConfig.model_validate(data)


def list_site_ids() -> list[str]:
    return [p.stem for p in _CONFIG_DIR.glob("*.yaml")]


def load_prompt_template(template_name: str) -> str:
    prompt_path = Path(__file__).parent.parent.parent / "config" / "prompts" / f"{template_name}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")
