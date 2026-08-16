import pytest
from src.analytics.google_auth import load_credentials, GoogleCredentialsError


def test_load_credentials_raises_when_env_missing(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET_PATH", raising=False)
    monkeypatch.delenv("GOOGLE_TOKEN_PATH", raising=False)
    with pytest.raises(GoogleCredentialsError):
        load_credentials()


def test_load_credentials_raises_when_token_file_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET_PATH", str(tmp_path / "client_secret.json"))
    monkeypatch.setenv("GOOGLE_TOKEN_PATH", str(tmp_path / "does-not-exist.json"))
    with pytest.raises(GoogleCredentialsError):
        load_credentials()
