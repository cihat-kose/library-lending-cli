"""Unit tests never read a developer's .env or connection environment."""

import pytest

from library_lending_cli import config


@pytest.fixture(autouse=True)
def isolate_app_settings(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "ENV_FILE", tmp_path / ".env")
    for key in config.KEYS:
        monkeypatch.delenv(key, raising=False)
