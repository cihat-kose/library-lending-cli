from unittest.mock import MagicMock, patch

import pytest
from mysql.connector import Error as DatabaseError

from library_lending_cli.cli import _table, build_parser, database_config, main, run


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


def test_database_config_reads_environment(monkeypatch):
    values = {
        "DB_HOST": "database.example.test",
        "DB_PORT": "3307",
        "DB_USER": "operator",
        "DB_PASSWORD": "secret",
        "DB_NAME": "catalogue",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)

    assert database_config() == {
        "host": "database.example.test",
        "port": 3307,
        "user": "operator",
        "password": "secret",
        "database": "catalogue",
    }


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


@patch("library_lending_cli.cli.mysql.connector.connect")
def test_main_reports_connection_error(connect, capsys):
    connect.side_effect = DatabaseError("unavailable")

    assert main(["books"]) == 3
    assert "Database error" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("arguments", "service_name", "expected"),
    [
        (["search", "Austen"], "search_books", "Pride"),
        (
            ["lend", "--borrower", "1", "--isbn", "9780141439518", "--copy", "1"],
            "register_loan",
            "Loan 17 created.",
        ),
        (["return", "17"], "return_loan", "Loan 17 returned."),
        (["history", "1"], "borrower_history", "Pride"),
    ],
)
def test_run_dispatches_commands(arguments, service_name, expected, capsys):
    parser = build_parser()
    return_value = {
        "search_books": [("9780141439518", "Pride", "Austen", 1813)],
        "register_loan": 17,
        "return_loan": None,
        "borrower_history": [(17, "Pride", "Austen", "2026-01-01", None)],
    }[service_name]
    with patch(f"library_lending_cli.cli.{service_name}", return_value=return_value) as service:
        run(parser.parse_args(arguments), MagicMock())

    service.assert_called_once()
    assert expected in capsys.readouterr().out
