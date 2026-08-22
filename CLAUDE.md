# Ranking Site Generator

Google AdSense収益化を目的とした、ランキングサイト自動生成システム。
テーマを指定するだけで、記事生成・Hugo静的サイト出力・SEO最適化まで自動化する。

## 記事生成（Claude Codeスキル）

記事生成は `SKILL.md` で定義されたClaude Codeスキルで実行する。**APIキー不要**。

```
# Claude Code内で実行（/generate-article スキルを呼ぶ）
/generate-article --site ai-tools
/generate-article --site ai-tools --type ranking
/generate-article --site ai-tools --type individual
/generate-article --site ai-tools --dry-run
```

## Python CLIコマンド（SEO・DB・レポート）

```bash
# SEO後処理（構造化データ・内部リンクを生成済みMarkdownに適用）
python -m src.cli.main seo --site ai-tools

# 生成済みMarkdownをDBに記録
python -m src.cli.main record --site ai-tools --scan output/ai-tools/content/

# コスト・記事数・広告収益レポート
python -m src.cli.main report --site ai-tools

# AdSense広告収益を同期（要セットアップ: docs/google-api-setup.md）
python -m src.cli.main sync-adsense --site ai-tools --days 3

# Search Console検索指標を同期（要セットアップ: docs/google-api-setup.md）
python -m src.cli.main sync-search-console --site ai-tools --days 3

# Google APIのOAuthトークンをローカルで発行（AdSense・Search Console共通、初回セットアップ用）
python -m src.cli.main google-auth --client-secret credentials/adsense_client_secret.json --token-out credentials/adsense_token.json

# 利用可能なサイト一覧
python -m src.cli.main list-sites

# テスト
pytest tests/ -v

# Hugo ローカルプレビュー（事前に hugo コマンドが必要。ポータル本体は output/portal/）
cd output/portal && hugo server
```

## 環境変数 (.env)

| 変数名 | 説明 |
|---|---|
| `OPENAI_API_KEY` | DALL-E 3 画像生成用（Phase2以降・任意） |
| `ADSENSE_ACCOUNT_ID` | AdSense広告収益同期用のアカウントID（`pub-`から始まる） |
| `GOOGLE_CLIENT_SECRET_PATH` | Google OAuthクライアントシークレットJSONのパス（AdSense・Search Console共通） |
| `GOOGLE_TOKEN_PATH` | Google OAuthトークンJSONのパス（AdSense・Search Console共通） |

広告収益・検索指標計測のセットアップ手順は `docs/google-api-setup.md` を参照。

## 設定ファイル

- `config/sites/*.yaml` — サイトごとの設定（テーマ・ランキング対象・記事数など）
- `config/prompts/*.md` — 記事タイプごとのプロンプトテンプレート
- `SKILL.md` — 記事生成スキル定義（Claude Code が読み込む）

## プロジェクト構成

```
ranking-site-generator/
├── SKILL.md                          # 記事生成スキル定義
├── config/
│   ├── sites/ai-tools.yaml           # サイト設定
│   └── prompts/                      # プロンプトテンプレート
├── src/
│   ├── cli/main.py                   # CLIエントリポイント（seo・record・report・sync-adsense・sync-search-console）
│   ├── config/                       # 設定読み込み・バリデーション
│   ├── generator/                    # メタデータ・プロンプト組み立て
│   ├── publisher/hugo.py             # Hugo Markdown出力
│   ├── seo/                          # 構造化データ・内部リンク
│   ├── analytics/
│   │   ├── google_auth.py            # Google OAuth共通処理（AdSense・Search Console）
│   │   ├── adsense.py                # AdSense Management API連携
│   │   └── search_console.py         # Search Console API連携
│   └── database/                     # SQLite進捗・重複管理・広告収益・検索指標
├── docs/google-api-setup.md          # Google API（AdSense・Search Console）認証セットアップ手順
├── .github/workflows/sync-metrics.yml # AdSense広告収益・Search Console検索指標の定期同期
├── output/
│   ├── portal/                       # kenjatimejp.com の実体（Hugoプロジェクト本体・Netlifyデプロイ対象）
│   │   └── content/{site_id}/        # sync-portal で各テーマから取り込まれたコンテンツ
│   └── {site_id}/                    # テーマごとの生成ステージング場所（content/のみ。sync-portal前）
└── data/db/sites.db                  # SQLiteデータベース
```

## アーキテクチャ原則

- **YAML駆動**: コードを変えずに `config/sites/` にYAMLを追加するだけで新サイトを追加できる
- **スキルベース生成**: 記事生成はClaude Codeスキル（`SKILL.md`）が担当。APIキー不要
- **Publisher切り替え**: `publisher: hugo` または `publisher: wordpress` を設定で切り替え可能
- **重複防止**: 生成コンテンツのSHA256ハッシュをDBに保存し、重複生成を防ぐ
- **Two-pass生成**: アウトライン生成 → 本文生成の2段階でハルシネーション低減（SKILL.md内で実施）
- **ポータル統合**: 全テーマ（`ai-tools`含む）は `output/{site_id}/content/` に生成後、`sync-portal --site {site_id}` で `output/portal/`（kenjatimejp.com実体）に集約される。特別扱いされるサイトは存在しない

## 記事生成フロー

```
/generate-article スキル起動
→ YAML設定読み込み
→ キーワード展開
→ アウトライン生成 (Claude Code)
→ 本文生成 (Claude Code)
→ Hugo Markdown出力（output/{site}/content/）
→ python -m src.cli.main seo   → SEO処理（構造化データ・内部リンク付加）
→ python -m src.cli.main record → 重複チェック (content_hash) + DB記録
→ python -m src.cli.main sync-portal → output/portal/ へ取り込み（kenjatimejp.comのテーマ一覧に反映）
```

## 記事タイプ

| タイプ | 文字数 | 説明 |
|---|---|---|
| `top` | 3,000字 | トップページ |
| `ranking` | 5,000〜8,000字 | ○○ランキング記事 |
| `individual` | 3,000〜5,000字 | 個別紹介記事 |
| `faq` | 2,000〜3,000字 | FAQ記事 |
| `related` | 2,000〜3,000字 | 関連記事 |

## Phase別ロードマップ

- **Phase1（現在）**: Claude Codeスキルによる記事生成・SQLiteでの進捗/重複/広告収益/検索指標管理・Hugo静的サイト生成・**Netlify**へのデプロイ・AdSense自動広告タグ埋め込み・AdSense広告収益/Search Console検索指標データ同期（`sync-adsense`/`sync-search-console` CLI、手動実行）
- **Phase2**: Gitリポジトリ化とGitHub Actions CI/CD整備（`.github/workflows/sync-metrics.yml` の自動実行有効化、Hugoビルド〜Netlifyデプロイの自動化）・WordPress連携オプション・GA4トラフィック計測の追加
- **Phase3**: PostgreSQL・Celery非同期・マルチサイト一括生成・Streamlit管理画面（記事生成状況と広告収益をまとめたダッシュボード）
