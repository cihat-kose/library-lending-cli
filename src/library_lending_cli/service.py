"""Database operations and domain errors for the lending workflow."""

from __future__ import annotations

import datetime as dt
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
        isbn = isbn.strip()
        if borrower_id <= 0 or copy_number <= 0:
            raise ValueError("borrower and copy numbers must be positive integers")
        if len(isbn) != 13 or not isbn.isdigit():
            raise ValueError("ISBN must contain exactly 13 digits")
        try:
            parsed_date = dt.date.fromisoformat(loan_date) if loan_date else dt.date.today()
        except ValueError as exc:
            raise ValueError("loan date must use YYYY-MM-DD format") from exc
        return cls(borrower_id, isbn, copy_number, parsed_date)


def list_books(connection: Any) -> list[tuple[Any, ...]]:
    with closing(connection.cursor()) as cursor:
        cursor.execute(
            "SELECT isbn, title, author, publisher, publication_year, page_count "
            "FROM books ORDER BY title"
        )
        return cursor.fetchall()


def search_books(connection: Any, query: str) -> list[tuple[Any, ...]]:
    query = query.strip()
    if not query:
        raise ValueError("search text must not be empty")
    with closing(connection.cursor()) as cursor:
        cursor.execute(
            "SELECT isbn, title, author, publication_year FROM books "
            "WHERE title LIKE %s OR author LIKE %s ORDER BY author, title",
            (f"%{query}%", f"%{query}%"),
        )
        return cursor.fetchall()


def register_loan(connection: Any, request: LoanRequest) -> int:
    """Create a loan atomically; the schema also enforces one open loan per copy."""
    try:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT 1 FROM borrowers WHERE id = %s", (request.borrower_id,))
            if cursor.fetchone() is None:
                raise NotFoundError(f"borrower {request.borrower_id} does not exist")

            cursor.execute(
                "SELECT 1 FROM copies WHERE isbn = %s AND copy_number = %s FOR UPDATE",
                (request.isbn, request.copy_number),
            )
            if cursor.fetchone() is None:
                raise NotFoundError(f"copy {request.isbn}/{request.copy_number} does not exist")

            cursor.execute(
                "SELECT 1 FROM loans WHERE isbn = %s AND copy_number = %s AND returned_at IS NULL",
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
    if loan_id <= 0:
        raise ValueError("loan ID must be a positive integer")
    returned_at = returned_at or dt.date.today()
    try:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT returned_at FROM loans WHERE id = %s FOR UPDATE", (loan_id,))
            row = cursor.fetchone()
            if row is None:
                raise NotFoundError(f"loan {loan_id} does not exist")
            if row[0] is not None:
                raise ConflictError(f"loan {loan_id} was already returned")
            cursor.execute(
                "UPDATE loans SET returned_at = %s WHERE id = %s", (returned_at, loan_id)
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def borrower_history(connection: Any, borrower_id: int) -> list[tuple[Any, ...]]:
    if borrower_id <= 0:
        raise ValueError("borrower ID must be a positive integer")
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
