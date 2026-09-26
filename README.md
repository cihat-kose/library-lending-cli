# Library Lending CLI

A small, tested command-line application for tracking a library's books, physical copies,
borrowers, loans, and returns. It demonstrates Python service design, parameterized MySQL
queries, transactional state changes, boundary validation, and a pragmatic QA strategy.

## What it solves

A library operator can search the catalogue, lend a specific copy, prevent duplicate open
loans, return it, and inspect a borrower's history. The database—not only the Python process—
enforces that a copy can have at most one open loan.

```console
$ library-cli search Austen
ISBN         | Title               | Author      | Year
-------------+---------------------+-------------+-----
9780141439518 | Pride and Prejudice | Jane Austen | 1813

$ library-cli lend --borrower 1 --isbn 9780141439518 --copy 1
Loan 1 created.
$ library-cli return 1
Loan 1 returned.
```

## Features

- List and search books by title or author.
- Register loans only for existing borrowers and copies.
- Prevent concurrent duplicate loans through row locking and a database uniqueness constraint.
- Return an open loan and reject missing or already returned loans.
- Display complete borrower history.
- Report validation, domain, and database failures with distinct non-zero exit codes.

## Technology

- Python 3.11+ and `mysql-connector-python`
- MySQL 8.0+ with InnoDB transactions and integrity constraints
- pytest, coverage, Ruff, and GitHub Actions

## Setup

1. Create and activate a virtual environment, then install the application and development tools:

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
   python -m pip install -c requirements-ci.txt -e ".[dev]"
   ```

2. Create the schema and deterministic demonstration data with a local MySQL 8 server:

   ```bash
   mysql -u root -p < database/schema.sql
   mysql -u root -p < database/sample_data.sql
   ```

3. Create a least-privilege local application user (replace the example password):

   ```sql
   CREATE USER 'library_app'@'localhost' IDENTIFIED BY 'change-me';
   GRANT SELECT, INSERT, UPDATE ON library_lending.* TO 'library_app'@'localhost';
   ```

4. Copy `.env.example` to `.env`, replace its example values, and export them in your shell.
   The application reads environment variables directly; it intentionally does not load `.env`
   files or store credentials. For example on a POSIX shell:

   ```bash
   set -a; source .env; set +a
   library-cli books
   ```

`python -m library_lending_cli books` is equivalent and works well as an IDE run target after
selecting the project virtual environment.

## Commands

```text
library-cli books
library-cli search <title-or-author>
library-cli lend --borrower ID --isbn 13_DIGITS --copy NUMBER [--date YYYY-MM-DD]
library-cli return LOAN_ID
library-cli history BORROWER_ID
```

Run `library-cli --help` or `library-cli COMMAND --help` for details. Configuration variables are
`DB_HOST` (default `127.0.0.1`), `DB_PORT` (`3306`), `DB_USER` (`library_app`), `DB_PASSWORD`
(empty), and `DB_NAME` (`library_lending`). Do not use the empty-password default outside a
locked-down local development database.

## Quality checks

```bash
ruff check .
ruff format --check .
pytest
python -m build
```

CI resolves development tools through `requirements-ci.txt`, which pins every direct build and
test dependency. Runtime metadata retains bounded compatible ranges for library consumers. Update
the pins deliberately and verify the full workflow rather than accepting an unreviewed major
upgrade.

Unit tests isolate error paths and transaction behavior with test doubles. The integration test
recreates the disposable `library_lending_test` schema and checks the complete
lend-conflict-return-lend lifecycle against MySQL. It is skipped locally unless
`RUN_MYSQL_INTEGRATION=1`; CI runs it against a MySQL 8.4 service. The fixture refuses to drop a
database whose name does not end in `_test`. Coverage has an enforced 85% minimum for the Python
package. Schema setup uses the MySQL root account, then the lifecycle test reconnects as a dedicated
test user limited to `SELECT`, `INSERT`, and `UPDATE`; a separate contract test checks that this
account has no schema- or user-administration grants.

## Design

- `src/library_lending_cli/cli.py` owns argument parsing, configuration, presentation, exit codes,
  and connection lifetime.
- `src/library_lending_cli/service.py` contains validation and transaction-aware use cases.
- `database/` is the canonical schema plus non-personal sample data.
- `tests/` separates fast behavior tests from the real database contract test.
- `docs/coursework/` preserves the original assignments, attribution context, and AI-use statement.

The application uses a `SELECT ... FOR UPDATE` lock while lending. A generated nullable column and
unique key provide a second line of defense against two open loans for the same copy. Any failed
state change is rolled back.

## Known limitations

- This is a single-operator CLI, not an authentication or authorization system.
- Schema migrations are plain SQL and must be applied manually.
- Loan due dates, reservations, fines, and borrower administration are intentionally out of scope.
- Search uses the configured MySQL collation and does not provide full-text ranking.

## Project background

This repository began as two backend-programming coursework submissions at Gokstad Akademiet.
The original PDFs, SQL exercises, calculator, Norwegian documentation, and the original AI-support
disclosure remain in `docs/coursework/`. The portfolio application is a subsequent refactor focused
on maintainability, transactional correctness, testability, security, and reproducible CI. No new
license has been assigned because the original repository did not specify one.
