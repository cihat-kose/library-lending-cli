import datetime as dt
from unittest.mock import MagicMock, call

import pytest

from library_lending_cli.service import (
    ConflictError,
    LoanRequest,
    NotFoundError,
    borrower_history,
    list_books,
    register_loan,
    return_loan,
    search_books,
)


def connection_with_cursor(*fetches):
    connection = MagicMock()
    cursor = MagicMock()
    cursor.__enter__.return_value = cursor
    cursor.fetchone.side_effect = fetches
    connection.cursor.return_value = cursor
    return connection, cursor


@pytest.mark.parametrize(
    ("borrower", "isbn", "copy", "date", "message"),
    [
        (0, "9780141439518", 1, None, "positive"),
        (1, "not-an-isbn", 1, None, "13 digits"),
        (1, "9780141439518", 1, "26-09-2026", "YYYY-MM-DD"),
    ],
)
def test_loan_request_rejects_invalid_values(borrower, isbn, copy, date, message):
    with pytest.raises(ValueError, match=message):
        LoanRequest.create(borrower, isbn, copy, date)


def test_register_loan_commits_and_returns_generated_id():
    connection, cursor = connection_with_cursor((1,), (1,), (1,), None)
    cursor.lastrowid = 42
    request = LoanRequest.create(7, "9780141439518", 2, "2026-09-26")

    assert register_loan(connection, request) == 42

    connection.commit.assert_called_once_with()
    connection.rollback.assert_not_called()
    assert (
        call(
            "INSERT INTO loans (isbn, copy_number, borrower_id, loan_date) VALUES (%s, %s, %s, %s)",
            ("9780141439518", 2, 7, dt.date(2026, 9, 26)),
        )
        in cursor.execute.call_args_list
    )


def test_register_loan_rolls_back_when_copy_is_already_lent():
    connection, _ = connection_with_cursor((1,), (1,), (1,), (1,))

    with pytest.raises(ConflictError, match="already on loan"):
        register_loan(connection, LoanRequest.create(1, "9780141439518", 1))

    connection.rollback.assert_called_once_with()
    connection.commit.assert_not_called()


def test_register_loan_rejects_unknown_borrower_and_rolls_back():
    connection, _ = connection_with_cursor(None)

    with pytest.raises(NotFoundError, match="borrower 99"):
        register_loan(connection, LoanRequest.create(99, "9780141439518", 1))

    connection.rollback.assert_called_once_with()


def test_return_loan_updates_open_loan():
    connection, cursor = connection_with_cursor((None, dt.date(2026, 1, 1)))
    returned = dt.date(2026, 9, 26)

    return_loan(connection, 8, returned)

    cursor.execute.assert_called_with(
        "UPDATE loans SET returned_at = %s WHERE id = %s", (returned, 8)
    )
    connection.commit.assert_called_once_with()


def test_return_loan_rejects_already_returned_loan():
    connection, _ = connection_with_cursor((dt.date(2026, 1, 1),))

    with pytest.raises(ConflictError, match="already returned"):
        return_loan(connection, 8)

    connection.rollback.assert_called_once_with()


def test_search_rejects_whitespace_only_query():
    with pytest.raises(ValueError, match="must not be empty"):
        search_books(MagicMock(), "  ")


def test_list_books_returns_cursor_rows_and_closes_cursor():
    connection, cursor = connection_with_cursor()
    cursor.fetchall.return_value = [("isbn", "A title")]

    assert list_books(connection) == [("isbn", "A title")]
    cursor.close.assert_called_once_with()


def test_search_uses_the_same_parameterized_pattern_for_title_and_author():
    connection, cursor = connection_with_cursor()
    cursor.fetchall.return_value = []

    assert search_books(connection, "  Austen ") == []
    assert cursor.execute.call_args.args[1] == ("%Austen%", "%Austen%")


def test_register_loan_rejects_unknown_copy():
    connection, _ = connection_with_cursor((1,), (1,), None)

    with pytest.raises(NotFoundError, match="copy .* does not exist"):
        register_loan(connection, LoanRequest.create(1, "9780141439518", 99))

    connection.rollback.assert_called_once_with()


def test_return_loan_rejects_unknown_and_invalid_ids():
    connection, _ = connection_with_cursor(None)
    with pytest.raises(NotFoundError, match="loan 404"):
        return_loan(connection, 404)
    connection.rollback.assert_called_once_with()

    with pytest.raises(ValueError, match="positive"):
        return_loan(connection, 0)


def test_borrower_history_returns_rows():
    connection, cursor = connection_with_cursor((1,))
    cursor.fetchall.return_value = [(1, "Pride", "Austen", dt.date(2026, 1, 1), None)]

    assert borrower_history(connection, 1) == [(1, "Pride", "Austen", dt.date(2026, 1, 1), None)]


def test_borrower_history_rejects_invalid_or_unknown_borrower():
    with pytest.raises(ValueError, match="positive"):
        borrower_history(MagicMock(), 0)

    connection, _ = connection_with_cursor(None)
    with pytest.raises(NotFoundError, match="borrower 5"):
        borrower_history(connection, 5)


@pytest.mark.parametrize("value", [True, 0, -1, 1.5, "1", None, 4294967296])
def test_id_validation(value):
    with pytest.raises(ValueError, match="positive integer"):
        LoanRequest.create(value, "9780141439518", 1)


@pytest.mark.parametrize("date", ["20260101", "2026-W01-1", "", "2026-02-30"])
def test_date_format_is_strict(date):
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        LoanRequest.create(1, "9780141439518", 1, date)


def test_unknown_book():
    connection, _ = connection_with_cursor((1,), None)
    with pytest.raises(NotFoundError, match="book .* does not exist"):
        register_loan(connection, LoanRequest.create(1, "9780141439518", 1))
    connection.rollback.assert_called_once()


@pytest.mark.parametrize("operation", ["lend", "return"])
def test_write_failure_rolls_back_and_closes_cursor(operation):
    connection, cursor = connection_with_cursor(
        *((1,), (1,), (1,), None) if operation == "lend" else ((None, dt.date(2026, 1, 1)),)
    )

    def fail_write(sql, params=None):
        if sql.startswith(("INSERT", "UPDATE")):
            raise RuntimeError("injected write failure")

    cursor.execute.side_effect = fail_write
    with pytest.raises(RuntimeError, match="injected"):
        if operation == "lend":
            register_loan(connection, LoanRequest.create(1, "9780141439518", 1))
        else:
            return_loan(connection, 1)
    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()
    cursor.close.assert_called_once()


def test_return_before_loan_is_rejected():
    connection, _ = connection_with_cursor((None, dt.date(2026, 5, 1)))
    with pytest.raises(ValueError, match="precede"):
        return_loan(connection, 1, dt.date(2026, 4, 1))
    connection.rollback.assert_called_once()


def test_search_treats_sql_and_wildcards_as_text():
    connection, cursor = connection_with_cursor()
    search_books(connection, "%_! ' OR 1=1 --")
    assert cursor.execute.call_args.args[1] == ("%!%!_!! ' OR 1=1 --%",) * 2


def test_commit_failure_rolls_back():
    connection, _ = connection_with_cursor((1,), (1,), (1,), None)
    connection.commit.side_effect = RuntimeError("commit failed")
    with pytest.raises(RuntimeError, match="commit failed"):
        register_loan(connection, LoanRequest.create(1, "9780141439518", 1))
    connection.rollback.assert_called_once()
