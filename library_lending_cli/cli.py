"""Command-line entry point."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from contextlib import closing
from typing import Any

import mysql.connector
from mysql.connector import Error as DatabaseError

from .config import database_config
from .service import (
    LendingError,
    LoanRequest,
    borrower_history,
    list_books,
    list_borrowers,
    list_copies,
    register_loan,
    return_loan,
    search_books,
)


def _table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    if not rows:
        return "No records found."
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
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("setup", help="create missing schema and seed only an empty database")
    commands.add_parser("borrowers", help="list demo borrowers")
    commands.add_parser("copies", help="list copies and availability")
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
    if args.command == "borrowers":
        print(_table(("ID", "First name", "Last name"), list_borrowers(connection)))
    elif args.command == "copies":
        print(_table(("ISBN", "Title", "Copy", "Status"), list_copies(connection)))
    elif args.command == "books":
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


def menu(connection: Any) -> None:
    while True:
        print(
            "\nLibrary Lending CLI\n1. List books\n2. Search books\n3. Borrow a copy"
            "\n4. Return a loan\n5. Borrower history\n6. List borrowers"
            "\n7. Copies and availability\n0. Exit"
        )
        try:
            choice = input("Choose an option: ").strip()
            if choice == "0":
                print("Goodbye.")
                return
            args = argparse.Namespace()
            if choice in {"1", "6", "7"}:
                args.command = {"1": "books", "6": "borrowers", "7": "copies"}[choice]
            elif choice == "2":
                args.command, args.query = "search", input("Title or author: ")
            elif choice == "3":
                args.command = "lend"
                args.borrower = read_id("Borrower ID (see option 6): ")
                args.isbn = input("ISBN (see option 7): ")
                args.copy = read_id("Copy number: ")
                args.date = None
            elif choice == "4":
                args.command, args.loan_id = "return", read_id("Loan ID (see history): ")
            elif choice == "5":
                args.command, args.borrower_id = "history", read_id("Borrower ID: ")
            else:
                print("Please choose an option from 0 to 7.")
                continue
            run(args, connection)
        except (ValueError, LendingError) as exc:
            print(f"Error: {exc}")
        except DatabaseError as exc:
            print(f"Database error: {exc}. Please retry or exit.")


def read_id(prompt: str) -> int:
    try:
        return int(input(prompt))
    except ValueError as exc:
        raise ValueError("ID must be a positive integer") from exc


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "setup":
            from .setup_database import initialize

            initialize()
            return 0
        with closing(mysql.connector.connect(**database_config())) as connection:
            if args.command is None:
                menu(connection)
            else:
                run(args, connection)
        return 0
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye.")
        return 0
    except (ValueError, LendingError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except (DatabaseError, OSError) as exc:
        print(f"Database error: {exc}. Check MySQL, .env and run setup first.", file=sys.stderr)
        return 3
