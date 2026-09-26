"""Database operations and domain errors for the lending workflow."""

from __future__ import annotations

import datetime as dt
import re
from contextlib import closing
from dataclasses import dataclass
from typing import Any


class LendingError(Exception):
    """Base class for errors that are safe to show to a CLI user."""


class NotFoundError(LendingError):
    """Raised when a requested record does not exist."""


class ConflictError(LendingError):
    """Raised when a requested state transition is not possible."""


@dataclass(frozen=True)
class LoanRequest:
    borrower_id: int
    isbn: str
    copy_number: int
    loan_date: dt.date

    @classmethod
    def create(
        cls, borrower_id: int, isbn: str, copy_number: int, loan_date: str | None = None
    ) -> LoanRequest:
        positive_id(borrower_id, "borrower ID")
        positive_id(copy_number, "copy number")
        isbn = isbn.strip() if isinstance(isbn, str) else ""
        if len(isbn) != 13 or not isbn.isascii() or not isbn.isdigit():
            raise ValueError("ISBN must contain exactly 13 digits")
        try:
            valid_format = isinstance(loan_date, str) and re.fullmatch(
                r"[0-9]{4}-[0-9]{2}-[0-9]{2}", loan_date
            )
            if loan_date is not None and not valid_format:
                raise ValueError
            parsed_date = (
                dt.date.fromisoformat(loan_date) if loan_date is not None else dt.date.today()
            )
        except ValueError as exc:
            raise ValueError("loan date must use YYYY-MM-DD format") from exc
        return cls(borrower_id, isbn, copy_number, parsed_date)


def positive_id(value: int, label: str) -> None:
    if type(value) is not int or not 0 < value <= 4294967295:
        raise ValueError(f"{label} must be a positive integer within MySQL INT UNSIGNED range")


def list_books(connection: Any) -> list[tuple[Any, ...]]:
    with closing(connection.cursor()) as cursor:
        cursor.execute(
            "SELECT isbn, title, author, publisher, publication_year, page_count "
            "FROM books ORDER BY title"
        )
        return cursor.fetchall()


def search_books(connection: Any, query: str) -> list[tuple[Any, ...]]:
    if not isinstance(query, str):
        raise ValueError("search text must be a string")
    query = query.strip()
    if not query:
        raise ValueError("search text must not be empty")
    query = query.replace("!", "!!").replace("%", "!%").replace("_", "!_")
    with closing(connection.cursor()) as cursor:
        cursor.execute(
            "SELECT isbn, title, author, publication_year FROM books "
            "WHERE title LIKE %s ESCAPE '!' OR author LIKE %s ESCAPE '!' ORDER BY author, title",
            (f"%{query}%", f"%{query}%"),
        )
        return cursor.fetchall()


def register_loan(connection: Any, request: LoanRequest) -> int:
    """Create a loan atomically; the schema also enforces one open loan per copy."""
    request = LoanRequest.create(
        request.borrower_id, request.isbn, request.copy_number, request.loan_date.isoformat()
    )
    try:
        connection.start_transaction()
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT 1 FROM borrowers WHERE id = %s", (request.borrower_id,))
            if cursor.fetchone() is None:
                raise NotFoundError(f"borrower {request.borrower_id} does not exist")

            cursor.execute("SELECT 1 FROM books WHERE isbn = %s", (request.isbn,))
            if cursor.fetchone() is None:
                raise NotFoundError(f"book {request.isbn} does not exist")

            cursor.execute(
                "SELECT 1 FROM copies WHERE isbn = %s AND copy_number = %s FOR UPDATE",
                (request.isbn, request.copy_number),
            )
            if cursor.fetchone() is None:
                raise NotFoundError(f"copy {request.isbn}/{request.copy_number} does not exist")

            cursor.execute(
                "SELECT 1 FROM loans WHERE isbn = %s AND copy_number = %s "
                "AND returned_at IS NULL FOR UPDATE",
                (request.isbn, request.copy_number),
            )
            if cursor.fetchone() is not None:
                raise ConflictError("copy is already on loan")

            cursor.execute(
                "INSERT INTO loans (isbn, copy_number, borrower_id, loan_date) "
                "VALUES (%s, %s, %s, %s)",
                (request.isbn, request.copy_number, request.borrower_id, request.loan_date),
            )
            loan_id = cursor.lastrowid
        connection.commit()
        return loan_id
    except Exception:
        connection.rollback()
        raise


def return_loan(connection: Any, loan_id: int, returned_at: dt.date | None = None) -> None:
    positive_id(loan_id, "loan ID")
    returned_at = returned_at if returned_at is not None else dt.date.today()
    if type(returned_at) is not dt.date:
        raise ValueError("return date must be a date")
    try:
        connection.start_transaction()
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                "SELECT returned_at, loan_date FROM loans WHERE id = %s FOR UPDATE", (loan_id,)
            )
            row = cursor.fetchone()
            if row is None:
                raise NotFoundError(f"loan {loan_id} does not exist")
            if row[0] is not None:
                raise ConflictError(f"loan {loan_id} was already returned")
            if returned_at < row[1]:
                raise ValueError("return date cannot precede loan date")
            cursor.execute(
                "UPDATE loans SET returned_at = %s WHERE id = %s", (returned_at, loan_id)
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def borrower_history(connection: Any, borrower_id: int) -> list[tuple[Any, ...]]:
    positive_id(borrower_id, "borrower ID")
    with closing(connection.cursor()) as cursor:
        cursor.execute("SELECT 1 FROM borrowers WHERE id = %s", (borrower_id,))
        if cursor.fetchone() is None:
            raise NotFoundError(f"borrower {borrower_id} does not exist")
        cursor.execute(
            "SELECT l.id, b.title, b.author, l.loan_date, l.returned_at "
            "FROM loans l JOIN books b ON b.isbn = l.isbn "
            "WHERE l.borrower_id = %s ORDER BY l.loan_date DESC, l.id DESC",
            (borrower_id,),
        )
        return cursor.fetchall()


def list_borrowers(connection: Any) -> list[tuple[Any, ...]]:
    with closing(connection.cursor()) as cursor:
        cursor.execute("SELECT id, first_name, last_name FROM borrowers ORDER BY id")
        return cursor.fetchall()


def list_copies(connection: Any) -> list[tuple[Any, ...]]:
    with closing(connection.cursor()) as cursor:
        cursor.execute(
            "SELECT c.isbn, b.title, c.copy_number, CASE WHEN l.id IS NULL THEN "
            "'Available' ELSE 'On loan' END FROM copies c JOIN books b ON b.isbn = c.isbn "
            "LEFT JOIN loans l ON l.isbn = c.isbn AND l.copy_number = c.copy_number "
            "AND l.returned_at IS NULL ORDER BY b.title, c.copy_number"
        )
        return cursor.fetchall()
