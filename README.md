# Library Lending CLI

[![CI Tests](https://img.shields.io/github/actions/workflow/status/cihat-kose/library-lending-cli/ci.yml?branch=master&style=for-the-badge&label=CI%20Tests&logo=github)](https://github.com/cihat-kose/library-lending-cli/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Interface](https://img.shields.io/badge/Interface-CLI-222222?style=for-the-badge&logo=gnubash&logoColor=white)](https://docs.python.org/3/library/argparse.html)
[![Tests](https://img.shields.io/badge/Tests-pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-F7DF1E?style=for-the-badge&logo=open-source-initiative&logoColor=black)](LICENSE)

A small, tested Python/MySQL command-line application for browsing books, lending and returning copies, and viewing borrower history. The original coursework and AI-use statement remain preserved under `docs/coursework/`.

This is a demo and coursework application, not a live library system. Its database, users, seed records, and example connection settings are fictional; no production database or valid real-user password is included.

## Related implementation

[`library-loan-management`](https://github.com/cihat-kose/library-loan-management) is a separate, server-free SQLite implementation. This repository is the MySQL implementation; their setup instructions and dependencies are intentionally different and should not be mixed.

## Quick start

Requirements: Python 3.11 or newer, MySQL Server 8.0 or newer, and a local MySQL account. MySQL Server must be installed and running; MySQL Workbench alone is only a client and is not enough. Docker and cloud services are not required.

```powershell
git clone https://github.com/cihat-kose/library-lending-cli.git
cd library-lending-cli
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

The conditional copy creates `.env` only when it does not exist. After editing it, do not run the copy command again: it would reset your local settings. Set `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` to match your own MySQL account and database. Keep the real `.env` local and never commit it; environment variables with the same names override values from `.env`.

### Windows MySQL service check

Check installed MySQL services from PowerShell:

```powershell
Get-Service *MySQL*
```

If the installed service is named `MySQL80` and its status is `Disabled` or `Stopped`, open PowerShell as Administrator and run:

```powershell
Set-Service -Name MySQL80 -StartupType Automatic
Start-Service -Name MySQL80
```

If your installation uses another service name, use the exact name returned by `Get-Service *MySQL*`. Do not use these commands for a service that is already running.

From the project root, run setup once with the same interpreter used for the project:

```powershell
.venv\Scripts\python.exe -m library_lending_cli setup
```

Setup uses the reviewed files in `database/`, creates missing schema objects, and never runs `DROP DATABASE`. If all application tables already exist, setup preserves the existing data and skips the demo seed; otherwise it prepares the schema and bundled demonstration records. Setup is explicit and does not run automatically when the CLI starts.

Start the interactive menu from the project root:

```powershell
.venv\Scripts\python -m library_lending_cli
```

The menu supports listing/searching books, viewing copies and borrowers, lending/returning copies, and borrower history. Script commands are also available, for example `python -m library_lending_cli search Austen`. If the package is installed with `python -m pip install .`, the equivalent console command is `library-lending-cli`.

In PyCharm:

1. Select the project `.venv` interpreter.
2. Set `C:\Users\<you>\...\library-lending-cli` as the Working directory.
3. Select the `Library Lending CLI` run configuration and run the `library_lending_cli` module with no parameters.

The checked-in `.run/Library Lending CLI.run.xml` configuration uses the same entry point. The equivalent terminal command is `.venv\Scripts\python.exe -m library_lending_cli`.

## Database and configuration

Runtime uses MySQL with InnoDB. `database/schema.sql` defines normalized books, copies, borrowers, and loans tables. Foreign keys, checks, row locks, and a unique open-copy key protect integrity. `database/sample_data.sql` contains non-personal demonstration data. Application queries pass values as parameters.

Connection settings are `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME`. Setup needs permission to create the schema; normal use can use a least-privilege account with `SELECT`, `INSERT`, and `UPDATE`.

## Troubleshooting

- **MySQL is unavailable:** confirm that the MySQL Server service is installed and running; Workbench by itself cannot provide the database server.
- **Authentication is rejected:** check the account name and password in `.env`, and remember that matching environment variables take precedence over `.env`.
- **The database or tables are missing:** confirm `DB_NAME`, then run the explicit setup command from the project root with `.venv\Scripts\python.exe`.
- **PyCharm behaves differently from the terminal:** verify that PyCharm uses the project `.venv`, the project root as Working directory, the `library_lending_cli` module, and the same environment variables as the terminal.

## Tests and QA

Install the pinned quality and build tools when contributing:

```powershell
.venv\Scripts\python -m pip install -r requirements-ci.txt
```

```powershell
.venv\Scripts\python -m pytest
.venv\Scripts\ruff check .
.venv\Scripts\ruff format --check .
```

Unit and CLI tests use mocks. MySQL integration tests are marked separately and skipped unless `RUN_MYSQL_INTEGRATION=1` is explicitly set. They require `MYSQL_TEST_DATABASE` to end in `_test` (default `library_lending_test`) and may create/drop only that test database. They never target the development database. When explicitly enabled without a reachable server, the connection error is reported as a failure, not silently skipped. GitHub Actions runs the same test suite with a CI-only MySQL service; Docker is not required for local use.

Coverage is enabled by pytest configuration and is reported only when the command is run.

## Project structure

- `library_lending_cli/`: importable package and module entry point.
- `database/`: MySQL schema and demonstration data.
- `tests/`: unit, CLI, setup, configuration, and opt-in integration tests.
- `docs/coursework/`: original assignment PDFs, SQL exercises, calculator, schema image, and notes.

## Coursework background and limitations

The original assignments explicitly required Python with MySQL Connector and the `bok`, `eksemplar`, `utlån`, and `låner` model. Those materials and the AI-use disclosure remain preserved. The refactor keeps MySQL while adding English documentation, validation, transaction-safe state changes, and QA coverage.

This is a single-operator CLI. It has no authentication, migrations, reservations, due dates, fines, or borrower administration. MySQL Server and local credentials are required at runtime.
