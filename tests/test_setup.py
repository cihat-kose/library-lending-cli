from unittest.mock import patch

import pytest

from library_lending_cli.setup_database import initialize


@patch("library_lending_cli.setup_database.mysql.connector.connect")
def test_existing_data_is_preserved(connect, capsys):
    cursor = connect.return_value.cursor.return_value
    cursor.fetchone.side_effect = [(1,), (1,)]
    initialize()
    sql = " ".join(c.args[0] for c in cursor.execute.call_args_list)
    assert "DROP" not in sql
    assert "INSERT" not in sql
    assert "Existing data preserved" in capsys.readouterr().out
    connect.return_value.close.assert_called_once()


@patch("library_lending_cli.setup_database.mysql.connector.connect")
def test_empty_database_is_seeded(connect):
    cursor = connect.return_value.cursor.return_value
    cursor.fetchone.side_effect = [(1,), None, None, None, None]
    initialize()
    connect.return_value.start_transaction.assert_called_once()
    connect.return_value.commit.assert_called_once()
    assert any("INSERT INTO books" in c.args[0] for c in cursor.execute.call_args_list)


@patch("library_lending_cli.setup_database.mysql.connector.connect")
def test_seed_failure_rolls_back(connect):
    cursor = connect.return_value.cursor.return_value
    cursor.fetchone.side_effect = [(1,), None, None, None, None]

    def fail_seed(sql, params=None):
        if "INSERT INTO copies" in sql:
            raise RuntimeError("injected failure")

    cursor.execute.side_effect = fail_seed
    with pytest.raises(RuntimeError):
        initialize()
    connect.return_value.rollback.assert_called_once()
    connect.return_value.commit.assert_not_called()
    cursor.close.assert_called_once()
    connect.return_value.close.assert_called_once()


@patch("library_lending_cli.setup_database.mysql.connector.connect")
def test_setup_lock_failure(connect):
    connect.return_value.cursor.return_value.fetchone.return_value = (0,)
    with pytest.raises(ValueError, match="Another setup"):
        initialize()
    connect.return_value.close.assert_called_once()
