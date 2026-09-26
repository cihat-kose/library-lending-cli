from unittest.mock import MagicMock, patch

import pytest
from mysql.connector import Error as DatabaseError

from library_lending_cli.cli import (
    _database_error_message,
    _table,
    build_parser,
    database_config,
    main,
    run,
)


def test_table_formats_empty_result():
    assert _table(("A", "Long"), []) == "No records found."


def test_parser_defaults_to_menu():
    assert build_parser().parse_args([]).command is None


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
        "autocommit": True,
        "connection_timeout": 5,
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
    ("errno", "expected"),
    [
        (2003, "Cannot reach MySQL"),
        (1045, "rejected the credentials"),
        (1049, "database was not found"),
        (1146, "schema is missing"),
    ],
)
def test_database_error_message_is_actionable_without_exposing_details(errno, expected):
    error = DatabaseError("password=do-not-print")
    error.errno = errno

    message = _database_error_message(error)

    assert expected in message
    assert "do-not-print" not in message


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


@patch("library_lending_cli.cli.mysql.connector.connect")
def test_menu_flows(connect, monkeypatch, capsys):
    answers = iter(
        ["9", "1", "2", "Austen", "3", "1", "9780141439518", "1", "4", "1", "5", "1", "6", "7", "0"]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    with patch("library_lending_cli.cli.run") as run_command:
        assert main([]) == 0
    assert [c.args[0].command for c in run_command.call_args_list] == [
        "books",
        "search",
        "lend",
        "return",
        "history",
        "borrowers",
        "copies",
    ]
    assert "Please choose" in capsys.readouterr().out
    connect.return_value.close.assert_called_once()


@patch("library_lending_cli.cli.mysql.connector.connect")
def test_menu_recovers_from_invalid_id(connect, monkeypatch, capsys):
    answers = iter(["4", "bad", "0"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert main([]) == 0
    assert "positive integer" in capsys.readouterr().out


@pytest.mark.parametrize("error", [EOFError, KeyboardInterrupt])
@patch("library_lending_cli.cli.mysql.connector.connect")
def test_menu_exit_on_interruption(connect, error, monkeypatch, capsys):
    def stop(_):
        raise error

    monkeypatch.setattr("builtins.input", stop)
    assert main([]) == 0
    connect.return_value.close.assert_called_once()
    assert "Goodbye" in capsys.readouterr().out


@patch("library_lending_cli.cli.mysql.connector.connect")
def test_menu_recovers_from_database_error(connect, monkeypatch, capsys):
    answers = iter(["1", "0"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    with patch("library_lending_cli.cli.run", side_effect=DatabaseError("injected failure")):
        assert main([]) == 0
    assert "Database error" in capsys.readouterr().out


@patch("library_lending_cli.setup_database.initialize")
def test_setup_command(initialize):
    assert main(["setup"]) == 0
    initialize.assert_called_once()
