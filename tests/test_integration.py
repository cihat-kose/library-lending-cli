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
    test_user = os.getenv("MYSQL_TEST_USER", "library_test_app")
    test_password = os.getenv("MYSQL_TEST_PASSWORD", "test-app-password")
    database_token = database_name.replace("_", "")
    if (
        not database_name.endswith("_test")
        or not database_token.isascii()
        or not database_token.isalnum()
    ):
        pytest.fail("MYSQL_TEST_DATABASE must be an alphanumeric name ending in _test")
    user_token = test_user.replace("_", "")
    if not user_token.isascii() or not user_token.isalnum():
        pytest.fail("MYSQL_TEST_USER must contain only letters, numbers, and underscores")
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
    cursor.execute(f"DROP USER IF EXISTS `{test_user}`@'%' ")
    cursor.execute(f"CREATE USER `{test_user}`@'%' IDENTIFIED BY %s", (test_password,))
    cursor.execute(f"GRANT SELECT, INSERT, UPDATE ON `{database_name}`.* TO `{test_user}`@'%'")
    root.commit()
    cursor.close()
    root.close()

    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=test_user,
        password=test_password,
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


def test_application_user_has_no_schema_or_user_administration_privileges(database):
    cursor = database.cursor()
    cursor.execute("SELECT CURRENT_USER()")
    expected_user = os.getenv("MYSQL_TEST_USER", "library_test_app")
    assert cursor.fetchone()[0].startswith(f"{expected_user}@")
    cursor.execute("SHOW GRANTS FOR CURRENT_USER")
    grants = " ".join(row[0] for row in cursor.fetchall()).upper()
    assert "SELECT, INSERT, UPDATE" in grants
    assert "DROP" not in grants
    assert "CREATE USER" not in grants
    cursor.close()
