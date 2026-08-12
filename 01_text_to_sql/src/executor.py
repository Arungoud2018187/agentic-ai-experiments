from .database import get_connection


FORBIDDEN_KEYWORDS = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "REPLACE",
    "TRUNCATE",
    "ATTACH",
    "DETACH"
]


def validate_sql(sql: str):

    sql_upper = sql.upper().strip()

    if not sql_upper.startswith("SELECT"):
        raise ValueError(
            "Only SELECT queries are allowed."
        )

    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in sql_upper:
            raise ValueError(
                f"Unsafe SQL detected: {keyword}"
            )


def execute_sql(sql: str):

    validate_sql(sql)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(sql)

        columns = [
            description[0]
            for description in cursor.description
        ]

        rows = cursor.fetchall()

        results = [
            dict(zip(columns, row))
            for row in rows
        ]

        return results

    finally:
        conn.close()