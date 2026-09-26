"""Database contract tests; enabled by RUN_MYSQL_INTEGRATION=1."""

import os
from pathlib import Path

import mysql.connector
import pytest

from library_lending_cli.service import ConflictError, LoanRequest, register_loan, return_loan

pytestmark = pytest.mark.integration


@pytest.fixture()
def database():
    if os.getenv("RUN_MYSQL_INTEGRATION") != "1":
        pytest.skip("set RUN_MYSQL_INTEGRATION=1 to run MySQL integration tests")
    root = mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("MYSQL_ROOT_USER", "root"),
        password=os.getenv("MYSQL_ROOT_PASSWORD", "test-root-password"),
    )
    cursor = root.cursor()
    cursor.execute("DROP DATABASE IF EXISTS library_lending")
    for statement in Path("database/schema.sql").read_text(encoding="utf-8").split(";"):
        if statement.strip():
            cursor.execute(statement)
    for statement in Path("database/sample_data.sql").read_text(encoding="utf-8").split(";"):
        if statement.strip():
            cursor.execute(statement)
    root.commit()
    cursor.close()
    root.close()

    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("MYSQL_ROOT_USER", "root"),
        password=os.getenv("MYSQL_ROOT_PASSWORD", "test-root-password"),
        database="library_lending",
    )
    yield connection
    connection.close()


def test_loan_lifecycle_and_duplicate_protection(database):
    request = LoanRequest.create(1, "9780141439518", 1, "2026-09-26")
    loan_id = register_loan(database, request)

    with pytest.raises(ConflictError, match="already on loan"):
        register_loan(database, request)

    return_loan(database, loan_id)
    second_loan_id = register_loan(database, request)
    assert second_loan_id > loan_id
