# Google API連携（AdSense・Search Console・GA4）セットアップ

`sync-adsense` / `sync-search-console` / `sync-ga4` コマンド（および `.github/workflows/sync-metrics.yml`）がAdSense Management API・Search Console API・GA4 Data APIからデータを取得できるようにするための、初回のみ必要な手順。認証はAdSense・Search Console・GA4共通の1つのOAuthクライアント・トークンで行う。

## 1. Google Cloudプロジェクトの準備

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成（または既存のものを使用）
2. 「APIとサービス」→「ライブラリ」から以下の3つを有効化
   - **AdSense Management API**
   - **Search Console API**（旧称 Webmasters API）
   - **Google Analytics Data API**

## 2. OAuth同意画面の設定

1. 「APIとサービス」→「OAuth同意画面」でアプリを設定
2. スコープに以下の3つを追加
   - `https://www.googleapis.com/auth/adsense.readonly`
   - `https://www.googleapis.com/auth/webmasters.readonly`
   - `https://www.googleapis.com/auth/analytics.readonly`
3. **まずは公開ステータスを「テスト」のままにし、「テストユーザー」に自分のGoogleアカウント（AdSense・Search Console・GA4にログインするアカウント）を追加する**
   - 上記のうちAdSense・Search Consoleのスコープは Google の「制限付きスコープ（restricted scope）」に該当し、公開ステータスを「本番環境」にするとGoogleによる**アプリ審査（verification）**が完了するまで認証時に「アクセスをブロック: 認証エラーです」と表示され使えない
   - 審査には数日〜数週間かかるため、最初はテストユーザーとして自分のアカウントを追加し、審査が完了してから本番環境に切り替えるのが実用的
   - ただし「テスト」ステータスのリフレッシュトークンは**7日で失効**するため、GitHub Actionsでの自動同期を長期運用する場合は、いずれ審査を通して本番環境にする必要がある（それまでは7日ごとに手順5を再実行してトークンを再発行する）

## 3. OAuthクライアントIDの作成

1. 「APIとサービス」→「認証情報」→「認証情報を作成」→「OAuthクライアントID」
2. アプリケーションの種類は **デスクトップアプリ** を選択
3. 作成後、JSONをダウンロードし `credentials/adsense_client_secret.json` として保存
   （このファイルは `.gitignore` により除外される。AdSense専用の名前だが、Search Console用も含む共通のクライアントシークレットとして使う）

## 4. AdSenseアカウントIDの確認

[AdSense管理画面](https://www.google.com/adsense/) にログインし、`pub-` から始まるアカウントID（例: `pub-1234567890123456`）を控える。

## 5. Search Consoleへのサイト登録

[Search Console](https://search.google.com/search-console) にログインし、対象ドメイン（例: `kenjatimejp.com`）を **ドメイン プロパティ** として追加する。

1. 「プロパティを追加」→「ドメイン」を選択し `kenjatimejp.com` を入力
2. 指示されたDNS TXTレコードをドメインのDNS設定に追加し、所有権を確認する
3. 確認が完了するまでAPI経由でもデータは取得できない（新規登録の場合、検索データが蓄積されるまで数日かかることもある）

コード側では `sc-domain:kenjatimejp.com` の形式でこのドメインプロパティを参照する（`config/sites/*.yaml` の `base_url` から自動生成されるため、追加設定は不要）。

## 6. GA4プロパティの準備

1. [Google Analytics](https://analytics.google.com/) で対象ドメイン（`kenjatimejp.com`）のGA4プロパティを作成（未作成の場合）
2. 「管理」→「データストリーム」→対象のウェブストリームを開き、**測定ID**（`G-` から始まるID）を控える
   → `output/portal/hugo.toml` の `[services.googleAnalytics] ID` をこの値に置き換える（このIDは公開ページに埋め込まれる非秘匿情報のため `.env`/Secretsではなくコード側に直接記載する）
3. 「管理」→「プロパティ設定」で**プロパティID**（数字のみ、例: `123456789`）を控える
   → `.env` の `GA4_PROPERTY_ID` およびGitHub Secretsの `GA4_PROPERTY_ID` にこの値を設定する（`sync-ga4` がAPI経由でデータ取得する際に使う識別子で、測定IDとは別物）
4. 「管理」→「プロパティのアクセス管理」で、手順7のトークンを発行するGoogleアカウントに閲覧権限が付与されていることを確認する

## 7. ローカルでトークンを発行

ブラウザが開ける環境（開発者のPC）で一度だけ実行する。CI環境では実行できない。

```bash
python -m src.cli.main google-auth \
  --client-secret credentials/adsense_client_secret.json \
  --token-out credentials/adsense_token.json
```

ブラウザが開き、Googleアカウントでの同意後 `credentials/adsense_token.json` が生成される（AdSense・Search Console・GA4すべてのスコープを含む）。

## 8. ローカルでの動作確認

`.env` に以下を設定して動作確認する（`.env.example` を参照）:

```
ADSENSE_ACCOUNT_ID=pub-xxxxxxxxxxxxxxxx
GOOGLE_CLIENT_SECRET_PATH=credentials/adsense_client_secret.json
GOOGLE_TOKEN_PATH=credentials/adsense_token.json
GA4_PROPERTY_ID=123456789
```

```bash
python -m src.cli.main sync-adsense --site ai-tools --days 3
python -m src.cli.main sync-search-console --site ai-tools --days 3
python -m src.cli.main sync-ga4 --site ai-tools --days 3
python -m src.cli.main report --site ai-tools
```

## 9. GitHub Secretsの登録（自動同期用）

リポジトリの Settings → Secrets and variables → Actions に以下を登録する:

| Secret名 | 値 |
|---|---|
| `GOOGLE_CLIENT_SECRET_JSON` | `credentials/adsense_client_secret.json` の中身（JSON全体） |
| `GOOGLE_TOKEN_JSON` | `credentials/adsense_token.json` の中身（JSON全体） |
| `ADSENSE_ACCOUNT_ID` | `pub-` から始まるAdSenseアカウントID |
| `GA4_PROPERTY_ID` | GA4のプロパティID（数字のみ） |

登録後は `.github/workflows/sync-metrics.yml` が毎日自動実行され、`data/db/sites.db` の広告収益・検索指標・GA4トラフィックデータが更新・コミットされる。手動実行は GitHub の Actions タブから「Run workflow」でも可能。

デプロイ自動化（`.github/workflows/deploy.yml`）を使う場合は、別途 `NETLIFY_AUTH_TOKEN`（netlify.com の User settings → Applications → Personal access tokens で発行）・`NETLIFY_SITE_ID`（`output/portal/.netlify/state.json` の `siteId`）もSecretsに登録する。

## 注意点

- AdSenseの推定収益・Search Console/GA4の指標はいずれも当日〜数日は確定しておらず変動する。`sync-adsense` / `sync-search-console` / `sync-ga4` は直近3日分を再取得して上書き（upsert）することでこのラグを吸収している
- レポートはドメイン単位（`config/sites/*.yaml` の `base_url`）で絞り込んでいるため、実際にAdSense広告が配信・Search Console/GA4に登録されているドメインでないと0件になる
- **同じドメインを複数の `site_id` で共有している場合の注意**: 例えば `ai-tools` と `drama-2026-summer` はどちらも `base_url` が `kenjatimejp.com` のため、`sync-adsense`/`sync-search-console`/`sync-ga4` を両方の site_id に対して実行すると、**同じドメイン全体の数値がそれぞれに記録される**（パスごとの内訳は取得できない）。合算するとダブルカウントになるので注意
- リフレッシュトークンが失効した場合はエラーになるため、手順7を再実行してトークンを再発行し、GitHub Secretsも更新する（**GA4スコープを既存トークンに追加した場合も再発行が必須**。古いトークンには新スコープの権限が含まれないため）
- 認証時に「アクセスをブロック: 認証エラーです」と表示される場合は、OAuth同意画面が「本番環境」になっていて未審査であることが原因であることが多い。手順2の通り「テスト」ステータスに戻し、自分のアカウントをテストユーザーに追加してから再実行する
