import pytest

from library_lending_cli.config import database_config


def test_env_file_and_environment_precedence(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text(
        "# Local settings\nDB_USER=demo\nDB_PASSWORD='spaces # and = signs'\nDB_PORT=3307\n"
    )
    monkeypatch.setenv("DB_USER", "override")
    config = database_config(env)
    assert config["user"] == "override"
    assert config["password"] == "spaces # and = signs"
    assert config["port"] == 3307


@pytest.mark.parametrize(
    "content",
    [
        "DB_PORT=0",
        "DB_PORT=65536",
        "DB_NAME=x;DROP",
        "oops",
        "OTHER=value",
        "DB_PASSWORD='unclosed",
    ],
)
def test_invalid_configuration(tmp_path, content):
    env = tmp_path / ".env"
    env.write_text(content)
    with pytest.raises(ValueError):
        database_config(env)
