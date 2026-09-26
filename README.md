# Library Lending CLI

This portfolio application grew from Gokstad Akademiet backend coursework. It demonstrates tested Python services, parameterized MySQL queries, transaction handling, and a command-line workflow for books, copies, borrowers, loans, returns, and history. The coursework origin remains documented under `docs/coursework/`.

## Quick start

Requirements: Python 3.11 or newer, MySQL Server 8.0 or newer, and a local MySQL account. Docker and cloud services are not required.

```powershell
git clone https://github.com/cihat-kose/gokstadakademiet-arbeidskrav3.git
cd gokstadakademiet-arbeidskrav3
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with local MySQL settings. It contains placeholders only and must not be committed. The program reads `.env` from the project root; real environment variables override it.

Prepare the database without deleting existing rows:

```powershell
.venv\Scripts\python -m library_lending_cli setup
```

Setup uses the reviewed files in `database/`, creates missing schema objects, and never runs `DROP DATABASE`. If application tables already contain data, sample inserts are skipped. An empty database receives the bundled demonstration books, copies, and borrowers.

Start the interactive menu from the project root:

```powershell
.venv\Scripts\python -m library_lending_cli
```

The menu supports listing/searching books, viewing copies and borrowers, lending/returning copies, and borrower history. Script commands are also available, for example `python -m library_lending_cli search Austen`.

In PyCharm, select the `.venv` interpreter, set the project root as Working directory, and run the module `library_lending_cli` with no parameters. The checked-in `.run/` configuration uses the same entry point.

## Database and configuration

Runtime uses MySQL with InnoDB. `database/schema.sql` defines normalized books, copies, borrowers, and loans tables. Foreign keys, checks, row locks, and a unique open-copy key protect integrity. `database/sample_data.sql` contains non-personal demonstration data. Application queries pass values as parameters.

Connection settings are `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME`. Setup needs permission to create the schema; normal use can use a least-privilege account with `SELECT`, `INSERT`, and `UPDATE`.

## Tests and QA

Install development tools when contributing:

```powershell
.venv\Scripts\python -m pip install -c requirements-ci.txt -e ".[dev]"
```

```powershell
.venv\Scripts\python -m pytest
.venv\Scripts\ruff check .
.venv\Scripts\ruff format --check .
```

Unit and CLI tests use mocks. MySQL integration tests are marked separately and skipped unless `RUN_MYSQL_INTEGRATION=1` is explicitly set. They require `MYSQL_TEST_DATABASE` to end in `_test` (default `library_lending_test`) and may create/drop only that test database. They never target the development database. When explicitly enabled without a reachable server, the connection error is reported as a failure, not silently skipped.

Coverage is enabled by pytest configuration and is reported only when the command is run.

## Project structure

- `library_lending_cli/`: importable package and module entry point.
- `database/`: MySQL schema and demonstration data.
- `tests/`: unit, CLI, setup, configuration, and opt-in integration tests.
- `docs/coursework/`: original assignment PDFs, SQL exercises, calculator, schema image, and notes.

## Coursework background and limitations

The original assignments explicitly required Python with MySQL Connector and the `bok`, `eksemplar`, `utlån`, and `låner` model. Those materials and the AI-use disclosure remain preserved. The refactor keeps MySQL while adding English documentation, validation, transaction-safe state changes, and QA coverage.

This is a single-operator CLI. It has no authentication, migrations, reservations, due dates, fines, or borrower administration. MySQL Server and local credentials are required at runtime.
