from unittest.mock import MagicMock, patch

import pytest

from library_lending_cli.cli import _table, build_parser, database_config, main


def test_table_formats_empty_result():
    assert _table(("A", "Long"), []) == "A | Long\n--+-----"


def test_parser_requires_a_command():
    with pytest.raises(SystemExit) as error:
        build_parser().parse_args([])
    assert error.value.code == 2


def test_database_config_rejects_non_numeric_port(monkeypatch):
    monkeypatch.setenv("DB_PORT", "wrong")
    with pytest.raises(ValueError, match="DB_PORT"):
        database_config()


@patch("library_lending_cli.cli.mysql.connector.connect")
def test_main_lists_books_and_closes_connection(connect, capsys):
    connection = MagicMock()
    connection.is_connected.return_value = True
    cursor = MagicMock()
    cursor.__enter__.return_value = cursor
    cursor.fetchall.return_value = [("9780141439518", "Pride", "Austen", "Penguin", 1813, 480)]
    connection.cursor.return_value = cursor
    connect.return_value = connection

    assert main(["books"]) == 0
    assert "Pride" in capsys.readouterr().out
    connection.close.assert_called_once_with()


@patch("library_lending_cli.cli.mysql.connector.connect")
def test_main_reports_domain_error_without_traceback(connect, capsys):
    connection = MagicMock()
    connection.is_connected.return_value = True
    cursor = MagicMock()
    cursor.__enter__.return_value = cursor
    cursor.fetchone.return_value = None
    connection.cursor.return_value = cursor
    connect.return_value = connection

    assert main(["return", "999"]) == 2
    assert "does not exist" in capsys.readouterr().err
