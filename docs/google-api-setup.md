# Google API連携（AdSense・Search Console）セットアップ

`sync-adsense` / `sync-search-console` コマンド（および `.github/workflows/sync-metrics.yml`）がAdSense Management API・Search Console APIからデータを取得できるようにするための、初回のみ必要な手順。認証はAdSense・Search Console共通の1つのOAuthクライアント・トークンで行う。

## 1. Google Cloudプロジェクトの準備

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成（または既存のものを使用）
2. 「APIとサービス」→「ライブラリ」から以下の2つを有効化
   - **AdSense Management API**
   - **Search Console API**（旧称 Webmasters API）

## 2. OAuth同意画面の設定

1. 「APIとサービス」→「OAuth同意画面」でアプリを設定
2. スコープに以下の2つを追加
   - `https://www.googleapis.com/auth/adsense.readonly`
   - `https://www.googleapis.com/auth/webmasters.readonly`
3. **まずは公開ステータスを「テスト」のままにし、「テストユーザー」に自分のGoogleアカウント（AdSense・Search Consoleにログインするアカウント）を追加する**
   - 上記2つはいずれもGoogleの「制限付きスコープ（restricted scope）」に該当し、公開ステータスを「本番環境」にするとGoogleによる**アプリ審査（verification）**が完了するまで認証時に「アクセスをブロック: 認証エラーです」と表示され使えない
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

## 6. ローカルでトークンを発行

ブラウザが開ける環境（開発者のPC）で一度だけ実行する。CI環境では実行できない。

```bash
python -m src.cli.main google-auth \
  --client-secret credentials/adsense_client_secret.json \
  --token-out credentials/adsense_token.json
```

ブラウザが開き、Googleアカウントでの同意後 `credentials/adsense_token.json` が生成される（AdSense・Search Console両方のスコープを含む）。

## 7. ローカルでの動作確認

`.env` に以下を設定して動作確認する（`.env.example` を参照）:

```
ADSENSE_ACCOUNT_ID=pub-xxxxxxxxxxxxxxxx
GOOGLE_CLIENT_SECRET_PATH=credentials/adsense_client_secret.json
GOOGLE_TOKEN_PATH=credentials/adsense_token.json
```

```bash
python -m src.cli.main sync-adsense --site ai-tools --days 3
python -m src.cli.main sync-search-console --site ai-tools --days 3
python -m src.cli.main report --site ai-tools
```

## 8. GitHub Secretsの登録（自動同期用）

リポジトリの Settings → Secrets and variables → Actions に以下を登録する:

| Secret名 | 値 |
|---|---|
| `GOOGLE_CLIENT_SECRET_JSON` | `credentials/adsense_client_secret.json` の中身（JSON全体） |
| `GOOGLE_TOKEN_JSON` | `credentials/adsense_token.json` の中身（JSON全体） |
| `ADSENSE_ACCOUNT_ID` | `pub-` から始まるAdSenseアカウントID |

登録後は `.github/workflows/sync-metrics.yml` が毎日自動実行され、`data/db/sites.db` の広告収益・検索指標データが更新・コミットされる。手動実行は GitHub の Actions タブから「Run workflow」でも可能。

## 注意点

- AdSenseの推定収益・Search Consoleの検索データはいずれも当日〜数日は確定しておらず変動する。`sync-adsense` / `sync-search-console` は直近3日分を再取得して上書き（upsert）することでこのラグを吸収している
- レポートはドメイン単位（`config/sites/*.yaml` の `base_url`）で絞り込んでいるため、実際にAdSense広告が配信・Search Consoleに登録されているドメインでないと0件になる
- **同じドメインを複数の `site_id` で共有している場合の注意**: 例えば `ai-tools` と `drama-2026-summer` はどちらも `base_url` が `kenjatimejp.com` のため、`sync-adsense`/`sync-search-console` を両方の site_id に対して実行すると、**同じドメイン全体の数値がそれぞれに記録される**（パスごとの内訳は取得できない）。合算するとダブルカウントになるので注意
- リフレッシュトークンが失効した場合はエラーになるため、手順6を再実行してトークンを再発行し、GitHub Secretsも更新する
- 認証時に「アクセスをブロック: 認証エラーです」と表示される場合は、OAuth同意画面が「本番環境」になっていて未審査であることが原因であることが多い。手順2の通り「テスト」ステータスに戻し、自分のアカウントをテストユーザーに追加してから再実行する
