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
    database_name = os.getenv("MYSQL_TEST_DATABASE", "library_lending_test")
    if not database_name.endswith("_test") or not database_name.replace("_", "").isalnum():
        pytest.fail("MYSQL_TEST_DATABASE must be an alphanumeric name ending in _test")
    root = mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("MYSQL_ROOT_USER", "root"),
        password=os.getenv("MYSQL_ROOT_PASSWORD", "test-root-password"),
    )
    cursor = root.cursor()
    cursor.execute(f"DROP DATABASE IF EXISTS `{database_name}`")
    schema = Path("database/schema.sql").read_text(encoding="utf-8")
    schema = schema.replace("library_lending", database_name)
    for statement in schema.split(";"):
        if statement.strip():
            cursor.execute(statement)
    samples = Path("database/sample_data.sql").read_text(encoding="utf-8")
    samples = samples.replace("library_lending", database_name)
    for statement in samples.split(";"):
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
        database=database_name,
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
