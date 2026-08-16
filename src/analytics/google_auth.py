from __future__ import annotations
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/adsense.readonly",
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/analytics.readonly",
]


class GoogleCredentialsError(RuntimeError):
    pass


def load_credentials() -> Credentials:
    client_secret_path = os.getenv("GOOGLE_CLIENT_SECRET_PATH")
    token_path = os.getenv("GOOGLE_TOKEN_PATH")
    if not client_secret_path or not token_path:
        raise GoogleCredentialsError(
            "GOOGLE_CLIENT_SECRET_PATH / GOOGLE_TOKEN_PATH が未設定です。"
            "docs/google-api-setup.md を参照してください。"
        )
    if not os.path.exists(token_path):
        raise GoogleCredentialsError(
            f"トークンファイルが見つかりません: {token_path} "
            "`python -m src.cli.main google-auth` を実行して発行してください。"
            "詳細は docs/google-api-setup.md を参照してください。"
        )
    credentials = Credentials.from_authorized_user_file(token_path, SCOPES)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(credentials.to_json())
    return credentials


def run_oauth_flow(client_secret_path: str, token_out_path: str) -> None:
    """ローカルでブラウザ同意フローを実行し、AdSense・Search Console共通のトークンファイルを発行する（CI非対応・手動実行専用）"""
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
    credentials = flow.run_local_server(port=0)
    out_dir = os.path.dirname(token_out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(token_out_path, "w", encoding="utf-8") as f:
        f.write(credentials.to_json())
