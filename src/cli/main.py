from __future__ import annotations
import hashlib
import os
import shutil
from datetime import date, timedelta
from pathlib import Path
import yaml
import click
from src.config.loader import load_site_config, list_site_ids
from src.database.models import init_db
from src.database.repository import (
    upsert_site,
    save_article,
    get_site_cost_summary,
    save_internal_links,
    upsert_ad_revenue,
    get_site_revenue_summary,
    upsert_search_metrics,
    get_site_search_summary,
)
from src.generator.base import ArticleData
from src.publisher import hugo as hugo_publisher
from src.seo.internal_links import build_link_map, inject_internal_links
from src.seo.structured_data import build_itemlist_jsonld, build_article_jsonld, build_faq_jsonld, inject_jsonld
from src.analytics import adsense, search_console, google_auth


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    try:
        end = text.index("---", 3)
    except ValueError:
        return {}, text
    fm = yaml.safe_load(text[3:end].strip()) or {}
    body = text[end + 3:].strip()
    return fm, body


def _scan_articles(site_id: str) -> list[ArticleData]:
    base = Path("output") / site_id / "content"
    articles = []
    for md_file in sorted(base.rglob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        fm, body = _parse_frontmatter(text)
        if not fm:
            continue
        articles.append(ArticleData(
            article_type=fm.get("article_type", ""),
            title=fm.get("title", ""),
            slug=fm.get("slug", md_file.stem),
            target_keyword=fm.get("keywords", [""])[0] if fm.get("keywords") else "",
            content=body,
            content_hash=hashlib.sha256(body.encode()).hexdigest(),
            meta_description=fm.get("description", ""),
            tags=fm.get("keywords", []),
        ))
    return articles


@click.group()
def cli():
    """ランキングサイト自動生成システム"""
    init_db()


@cli.command()
@click.option("--site", "site_id", required=True, help="サイトID")
def seo(site_id: str):
    """生成済みMarkdownファイルにSEO後処理（構造化データ・内部リンク）を適用する"""
    config = load_site_config(site_id)
    articles = _scan_articles(site_id)

    if not articles:
        click.echo(f"記事が見つかりません: output/{site_id}/content/")
        return

    link_map = build_link_map(config, articles)
    base = Path("output") / site_id / "content"

    for md_file in sorted(base.rglob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        fm, body = _parse_frontmatter(text)
        if not fm:
            continue

        article = next((a for a in articles if a.slug == fm.get("slug", md_file.stem)), None)
        if article is None:
            continue

        article_type = fm.get("article_type", "")
        if article_type == "ranking":
            jsonld = build_itemlist_jsonld(config, config.ranking_targets)
        elif article_type == "faq":
            jsonld = build_faq_jsonld([])
        else:
            jsonld = build_article_jsonld(config, article)

        body = inject_jsonld(body, jsonld)
        body = inject_internal_links(body, article, link_map, config.base_url)

        frontmatter_end = text.index("---", 3) + 3
        md_file.write_text(text[:frontmatter_end] + "\n\n" + body, encoding="utf-8")
        click.echo(f"  SEO適用: {md_file.relative_to(base.parent.parent)}")

    save_internal_links(site_id, link_map)
    click.echo(f"SEO後処理完了: {len(articles)}記事")


@cli.command()
@click.option("--site", "site_id", required=True, help="サイトID")
@click.option("--scan", "scan_dir", required=True, help="スキャンするディレクトリ（例: output/portal/content/）")
def record(site_id: str, scan_dir: str):
    """生成済みMarkdownファイルをDBに記録する"""
    config = load_site_config(site_id)
    upsert_site(config)
    base = Path(scan_dir)
    count = 0

    for md_file in sorted(base.rglob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        fm, body = _parse_frontmatter(text)
        if not fm:
            continue

        save_article(
            site_id=site_id,
            article_type=fm.get("article_type", ""),
            title=fm.get("title", ""),
            slug=fm.get("slug", md_file.stem),
            target_keyword=(fm.get("keywords") or [""])[0],
            content_hash=hashlib.sha256(body.encode()).hexdigest(),
            output_path=str(md_file),
            input_tokens=0,
            output_tokens=0,
            cost_usd=0.0,
            status="published",
        )
        count += 1
        click.echo(f"  記録: {md_file.name}")

    click.echo(f"DB記録完了: {count}記事")


_PORTAL_SITE_ID = "portal"


@cli.command("sync-portal")
@click.option("--site", "site_id", required=True, help="サイトID")
def sync_portal(site_id: str):
    """generate-article/seo/recordで生成済みのサイトを、ポータル（output/portal）のテーマとして取り込む"""
    config = load_site_config(site_id)
    src = Path("output") / site_id / "content"
    if not src.exists():
        raise click.ClickException(f"生成済みコンテンツが見つかりません: {src}")

    portal_root = Path("output") / _PORTAL_SITE_ID
    dest = portal_root / "content" / site_id
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    click.echo(f"  コピー: {src} -> {dest}")

    themes_path = portal_root / "data" / "themes.yaml"
    themes_path.parent.mkdir(parents=True, exist_ok=True)
    themes = yaml.safe_load(themes_path.read_text(encoding="utf-8")) if themes_path.exists() else []
    themes = [t for t in themes if t.get("id") != site_id]
    themes.append({
        "id": site_id,
        "title": config.name,
        "description": f"{config.theme}の最新ランキング・比較・おすすめ情報をお届けします。",
        "url": f"/{site_id}/",
    })
    themes_path.write_text(
        yaml.dump(themes, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    click.echo(f"ポータル取り込み完了: {dest} ・ {themes_path} を更新")


@cli.command()
@click.option("--site", "site_id", required=True, help="サイトID")
def report(site_id: str):
    """コスト・記事数・広告収益・検索指標レポートを表示する"""
    summary = get_site_cost_summary(site_id)
    revenue = get_site_revenue_summary(site_id)
    search = get_site_search_summary(site_id)
    click.echo(f"\n=== {site_id} レポート ===")
    click.echo(f"記事数:          {summary['article_count']}")
    click.echo(f"入力トークン:    {summary['total_input_tokens']:,}")
    click.echo(f"出力トークン:    {summary['total_output_tokens']:,}")
    click.echo(f"合計コスト:      ${summary['total_cost_usd']:.4f}")
    click.echo(f"広告収益記録日数: {revenue['days_recorded']}日（最新: {revenue['latest_date'] or '未同期'}）")
    click.echo(f"合計広告収益:    ${revenue['total_earnings_usd']:.4f}")
    click.echo(f"合計クリック数:  {revenue['total_clicks']:,}")
    profit = revenue['total_earnings_usd'] - summary['total_cost_usd']
    click.echo(f"利益（収益-コスト）: ${profit:.4f}")
    click.echo(f"検索指標記録日数: {search['days_recorded']}日（最新: {search['latest_date'] or '未同期'}）")
    click.echo(f"検索クリック数:  {search['total_clicks']:,}")
    click.echo(f"検索表示回数:    {search['total_impressions']:,}")
    click.echo(f"平均CTR:         {search['avg_ctr'] * 100:.2f}%")
    click.echo(f"平均掲載順位:    {search['avg_position']:.1f}")


@cli.command("sync-adsense")
@click.option("--site", "site_id", required=True, help="サイトID")
@click.option("--days", default=7, show_default=True, help="さかのぼって同期する日数")
def sync_adsense(site_id: str, days: int):
    """AdSense Management APIから広告収益を取得しDBに保存する"""
    config = load_site_config(site_id)
    account_id = os.getenv("ADSENSE_ACCOUNT_ID")
    if not account_id:
        raise click.ClickException(
            "ADSENSE_ACCOUNT_ID が未設定です。docs/google-api-setup.md を参照してください。"
        )

    domain = adsense.extract_domain(config.base_url)
    until = date.today()
    since = until - timedelta(days=days - 1)

    try:
        rows = adsense.fetch_daily_revenue(account_id, domain, since, until)
    except google_auth.GoogleCredentialsError as e:
        raise click.ClickException(str(e))

    if not rows:
        click.echo(f"該当データなし（ドメイン: {domain}, 期間: {since}〜{until}）")
        return

    for row in rows:
        upsert_ad_revenue(
            site_id=site_id,
            date=row["date"],
            estimated_earnings_usd=row["estimated_earnings_usd"],
            clicks=row["clicks"],
            page_views=row["page_views"],
            impressions=row["impressions"],
            cost_per_click_usd=row["cost_per_click_usd"],
            page_views_ctr=row["page_views_ctr"],
        )
        click.echo(f"  同期: {row['date']} 収益${row['estimated_earnings_usd']:.4f}")

    click.echo(f"AdSense同期完了: {len(rows)}日分（ドメイン: {domain}）")


@cli.command("sync-search-console")
@click.option("--site", "site_id", required=True, help="サイトID")
@click.option("--days", default=7, show_default=True, help="さかのぼって同期する日数")
def sync_search_console(site_id: str, days: int):
    """Search Console APIから検索指標を取得しDBに保存する"""
    config = load_site_config(site_id)
    site_url = search_console.extract_site_url(config.base_url)
    until = date.today()
    since = until - timedelta(days=days - 1)

    try:
        rows = search_console.fetch_daily_search_metrics(site_url, since, until)
    except google_auth.GoogleCredentialsError as e:
        raise click.ClickException(str(e))

    if not rows:
        click.echo(f"該当データなし（サイト: {site_url}, 期間: {since}〜{until}）")
        return

    for row in rows:
        upsert_search_metrics(
            site_id=site_id,
            date=row["date"],
            clicks=row["clicks"],
            impressions=row["impressions"],
            ctr=row["ctr"],
            average_position=row["average_position"],
        )
        click.echo(f"  同期: {row['date']} クリック{row['clicks']}件 表示{row['impressions']}回")

    click.echo(f"Search Console同期完了: {len(rows)}日分（サイト: {site_url}）")


@cli.command("google-auth")
@click.option("--client-secret", "client_secret_path", required=True, help="OAuthクライアントシークレットJSONのパス")
@click.option("--token-out", "token_out_path", required=True, help="発行したトークンJSONの出力先パス")
def google_auth_cmd(client_secret_path: str, token_out_path: str):
    """Google API（AdSense・Search Console）共通のOAuth同意フローをローカルで実行し、トークンファイルを発行する（CI非対応）"""
    google_auth.run_oauth_flow(client_secret_path, token_out_path)
    click.echo(f"トークンを発行しました: {token_out_path}")


@cli.command("list-sites")
def list_sites():
    """設定済みのサイト一覧を表示する"""
    ids = list_site_ids()
    if not ids:
        click.echo("設定ファイルが見つかりません (config/sites/*.yaml)")
        return
    click.echo("利用可能なサイト:")
    for sid in ids:
        click.echo(f"  - {sid}")


if __name__ == "__main__":
    cli()
