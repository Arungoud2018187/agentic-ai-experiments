from .database import get_connection


def get_database_schema():
    conn = get_connection()
    cursor = conn.cursor()

    tables = cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name NOT LIKE 'sqlite_%'
    """).fetchall()

    schema = []

    for (table_name,) in tables:
        columns = cursor.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()

        schema.append(f"Table: {table_name}")

        for column in columns:
            column_name = column[1]
            column_type = column[2]
            schema.append(
                f"  - {column_name}: {column_type}"
            )

    conn.close()

    return "\n".join(schema)