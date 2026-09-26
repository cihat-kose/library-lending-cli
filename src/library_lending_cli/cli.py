"""Command-line entry point."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from typing import Any

import mysql.connector
from mysql.connector import Error as DatabaseError

from .service import (
    LendingError,
    LoanRequest,
    borrower_history,
    list_books,
    register_loan,
    return_loan,
    search_books,
)


def database_config() -> dict[str, Any]:
    try:
        port = int(os.getenv("DB_PORT", "3306"))
    except ValueError as exc:
        raise ValueError("DB_PORT must be an integer") from exc
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": port,
        "user": os.getenv("DB_USER", "library_app"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "library_lending"),
    }


def _table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    values = [["" if value is None else str(value) for value in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in values:
        widths = [max(width, len(value)) for width, value in zip(widths, row, strict=True)]
    formatted = [" | ".join(header.ljust(widths[i]) for i, header in enumerate(headers))]
    formatted.append("-+-".join("-" * width for width in widths))
    formatted.extend(
        " | ".join(value.ljust(widths[i]) for i, value in enumerate(row)) for row in values
    )
    return "\n".join(formatted)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage a small library lending database.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("books", help="list books")
    search = commands.add_parser("search", help="search by title or author")
    search.add_argument("query")
    lend = commands.add_parser("lend", help="lend a copy to a borrower")
    lend.add_argument("--borrower", type=int, required=True)
    lend.add_argument("--isbn", required=True)
    lend.add_argument("--copy", type=int, required=True)
    lend.add_argument("--date", help="loan date in YYYY-MM-DD format")
    returned = commands.add_parser("return", help="return an open loan")
    returned.add_argument("loan_id", type=int)
    history = commands.add_parser("history", help="show a borrower's loan history")
    history.add_argument("borrower_id", type=int)
    return parser


def run(args: argparse.Namespace, connection: Any) -> None:
    if args.command == "books":
        print(
            _table(
                ("ISBN", "Title", "Author", "Publisher", "Year", "Pages"), list_books(connection)
            )
        )
    elif args.command == "search":
        print(_table(("ISBN", "Title", "Author", "Year"), search_books(connection, args.query)))
    elif args.command == "lend":
        request = LoanRequest.create(args.borrower, args.isbn, args.copy, args.date)
        print(f"Loan {register_loan(connection, request)} created.")
    elif args.command == "return":
        return_loan(connection, args.loan_id)
        print(f"Loan {args.loan_id} returned.")
    elif args.command == "history":
        print(
            _table(
                ("Loan", "Title", "Author", "Loan date", "Returned"),
                borrower_history(connection, args.borrower_id),
            )
        )


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    connection = None
    try:
        connection = mysql.connector.connect(**database_config())
        run(args, connection)
        return 0
    except (ValueError, LendingError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except DatabaseError as exc:
        print(f"Database error: {exc}", file=sys.stderr)
        return 3
    finally:
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
