# generate-article

ランキングサイトの記事を生成し、Hugo Markdown形式で出力するスキル。
`config/sites/` の設定と `config/prompts/` のテンプレートを読み込み、Claude Code 自身が記事を生成する。**Anthropic APIキーは不要**。

## 使い方

```
/generate-article --site <site_id> [--type ranking|individual|faq|all] [--dry-run]
```

| オプション | 説明 | デフォルト |
|---|---|---|
| `--site` | サイトID（`config/sites/*.yaml` のファイル名） | 必須 |
| `--type` | 記事タイプ | `all` |
| `--dry-run` | 生成のみ・ファイル書き込みなし | false |

---

## 実行手順

### Step 1: 引数解析

ユーザーのメッセージから `--site`・`--type`・`--dry-run` を読み取る。
`--type` が省略されていれば `all` とみなす。

### Step 2: 設定・テンプレート読み込み

Readツールで以下を読み込む:
- `config/sites/{site_id}.yaml`
- `config/prompts/system_base.md`
- `--type` に対応する `config/prompts/{type}_article.md`
  - `all` の場合: `ranking_article.md`・`individual_article.md`・`faq_article.md` の3ファイル

### Step 3: 記事生成（Two-pass方式）

各記事タイプについて以下を実施する。

---

#### ranking（ランキング記事 / 目標5,000〜8,000字）

- タイトル: `{theme}おすすめランキング{item_count}選【比較】`
- スラッグ: `{site_id}-ranking-top{item_count}`
- メインキーワード: YAML の `main_keyword`
- LSIキーワード: `{theme} 比較`・`{theme} おすすめ`・`{theme} 選び方` など

**1回目（アウトライン生成）**:
プロンプトテンプレートの `{変数}` をYAML値で置換し、末尾に以下を付加して生成:
```
## 指示
アウトラインのみ出力してください。本文は書かないでください。
```

**2回目（本文生成）**:
```
## 承認済みアウトライン

{1回目で生成したアウトライン}
```
を付加したプロンプトで本文を生成する。目標文字数を厳守すること。

---

#### individual（個別紹介記事 / 目標3,000〜5,000字）

YAML の `ranking_targets` を `article_plan.individual_articles` 件分ループし、各ツールの記事を生成する。

- タイトル: `{tool_name}の評判・口コミ・使い方を徹底解説【{theme}】`
- スラッグ: `{site_id}-{tool_name_slug}-review`

---

#### faq（FAQ記事 / 目標2,000〜3,000字）

- タイトル: `{theme}に関するよくある質問10選【Q&A】`
- スラッグ: `{site_id}-faq`
- `ranking_targets` 全体を参照して10問のQ&Aを生成する

---

### Step 4: Hugo Markdownファイルの書き出し

`--dry-run` の場合は生成内容を表示して終了。

そうでない場合、Bashツールで出力ディレクトリを作成してからWriteツールで書き出す:

```bash
mkdir -p output/{site_id}/content/{article_type}
```

**出力パス**:
```
output/{site_id}/content/{article_type}/{slug}.md
```

**ファイル形式**（Frontmatter + 本文）:
```
---
title: "記事タイトル"
date: YYYY-MM-DD
draft: false
description: "メタディスクリプション（本文冒頭から120字以内で抽出）"
keywords: ["メインキーワード", "LSIキーワード1", "LSIキーワード2"]
article_type: "ranking"
slug: "スラッグ"
---

（生成した記事本文をここに続ける）
```

既存ファイルがある場合（同一スラッグ）はスキップし、ユーザーに通知する。

### Step 5: SEO後処理

全ファイルの書き出し後にBashツールで実行する:

```bash
python -m src.cli.main seo --site {site_id}
```

これにより構造化データ（JSON-LD）と内部リンクが各ファイルに追記される。

### Step 6: DB記録

`--dry-run` でない場合にBashツールで実行:

```bash
python -m src.cli.main record --site {site_id} --scan output/{site_id}/content/
```

### Step 7: ポータルへの取り込み

`kenjatimejp.com`（実体は `output/portal/`）は複数テーマを1ドメインで運用するポータルサイト。`site_id` によらず、生成・DB記録後は必ずBashツールで以下を実行し、ポータルのホームに表示されるテーマ一覧へ取り込む:

```bash
python -m src.cli.main sync-portal --site {site_id}
```

これにより `output/{site_id}/content/` の内容が `output/portal/content/{site_id}/` にコピーされ、`output/portal/data/themes.yaml` にテーマが登録される（ホームのカード一覧に自動で反映される）。

### Step 8: 完了報告

以下を出力する:
- 生成した記事の一覧（タイトル・出力パス・文字数）
- スキップした記事（重複）
- プレビュー手順:
  ```bash
  cd output/portal && hugo server
  ```
