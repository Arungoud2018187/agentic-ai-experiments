import sqlite3

from .database_tool import DB_PATH


def get_schema():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    tables = cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name NOT LIKE 'sqlite_%'
    """).fetchall()

    output = []

    for (table,) in tables:

        columns = cursor.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()

        output.append(
            f"TABLE: {table}"
        )

        for column in columns:

            output.append(
                f"  {column[1]} {column[2]}"
            )

    conn.close()

    return "\n".join(output)