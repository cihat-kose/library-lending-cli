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
    connection, cursor = connection_with_cursor((1,), (1,), None)
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
    connection, _ = connection_with_cursor((1,), (1,), (1,))

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
    connection, cursor = connection_with_cursor((None,))
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
    connection, _ = connection_with_cursor((1,), None)

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
