import sqlite3

from .database_tool import DB_PATH


FORBIDDEN = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "REPLACE",
    "TRUNCATE"
]


def execute_query(sql):

    sql_clean = sql.strip()

    sql_upper = sql_clean.upper()

    if not sql_upper.startswith("SELECT"):

        raise ValueError(
            "Only SELECT queries are allowed."
        )

    for keyword in FORBIDDEN:

        if keyword in sql_upper:

            raise ValueError(
                f"Unsafe SQL detected: {keyword}"
            )

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    try:

        cursor.execute(sql_clean)

        columns = [
            description[0]
            for description in cursor.description
        ]

        rows = cursor.fetchall()

        return [
            dict(zip(columns, row))
            for row in rows
        ]

    finally:

        conn.close()