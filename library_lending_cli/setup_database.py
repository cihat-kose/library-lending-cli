"""Non-destructive setup using the reviewed MySQL SQL files in database/."""

from contextlib import closing

import mysql.connector

from .config import PROJECT_ROOT, database_config


def execute_sql(cursor, filename: str, database: str) -> None:
    # Only bundled simple statements are supported, never arbitrary uploaded SQL.
    sql = (PROJECT_ROOT / "database" / filename).read_text(encoding="utf-8")
    sql = sql.replace("library_lending", f"`{database}`")
    for statement in sql.split(";"):
        if statement.strip():
            cursor.execute(statement)


def initialize() -> None:
    config = database_config()
    database = config.pop("database")
    with (
        closing(mysql.connector.connect(**config)) as connection,
        closing(connection.cursor()) as cursor,
    ):
        cursor.execute("SELECT GET_LOCK(%s, 10)", (f"library_setup_{database}"[:64],))
        if cursor.fetchone()[0] != 1:
            raise ValueError("Another setup is running; please retry")
        # Closing the connection releases the advisory lock even on failure.
        execute_sql(cursor, "schema.sql", database)
        # Existing data is never replaced or supplemented with demo records.
        for table in ("books", "copies", "borrowers", "loans"):
            cursor.execute(f"SELECT 1 FROM {table} LIMIT 1")
            if cursor.fetchone() is not None:
                print("Schema checked. Existing data preserved; demo seed skipped.")
                return
        try:
            connection.start_transaction()
            execute_sql(cursor, "sample_data.sql", database)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    print("Database ready. Two demo books, three copies and two borrowers created.")
