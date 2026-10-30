"""SQLite tool: deterministic demo database plus an offline text-to-SQL planner."""

import random
import re
import sqlite3
import time
from pathlib import Path

from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    company TEXT NOT NULL,
    country TEXT NOT NULL,
    email TEXT NOT NULL,
    signup_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    subject TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_product ON orders(product_id);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
"""

CUSTOMERS = [
    (1, "Avery Chen", "Acme Corp", "United States", "avery@acme.example", "2023-01-12"),
    (2, "Lena Fischer", "Globex", "Germany", "lena@globex.example", "2023-02-03"),
    (3, "Priya Nair", "Initech", "United States", "priya@initech.example", "2023-03-21"),
    (4, "Oliver Smith", "Umbrella Health", "United Kingdom", "oliver@umbrella.example", "2023-04-08"),
    (5, "Maya Patel", "Stark Industries", "United States", "maya@stark.example", "2023-05-17"),
    (6, "Noah Tremblay", "Wayne Enterprises", "Canada", "noah@wayne.example", "2023-06-09"),
    (7, "Yuki Tanaka", "Cyberdyne", "Japan", "yuki@cyberdyne.example", "2023-07-22"),
    (8, "Ethan Brooks", "Hooli", "United States", "ethan@hooli.example", "2023-08-14"),
    (9, "Ananya Rao", "Vandelay", "India", "ananya@vandelay.example", "2023-09-01"),
    (10, "Isla Wilson", "Soylent", "Australia", "isla@soylent.example", "2023-10-19"),
    (11, "Lucas Martin", "Massive Dynamic", "Canada", "lucas@massive.example", "2023-11-05"),
    (12, "Sofia Rossi", "Pied Piper", "United States", "sofia@piedpiper.example", "2023-12-11"),
]

PRODUCTS = [
    (1, "Analytics Pro", "Analytics", 499.0),
    (2, "CRM Suite", "Sales", 299.0),
    (3, "Support Desk", "Support", 199.0),
    (4, "Data Connector", "Data", 149.0),
    (5, "Security Shield", "Security", 399.0),
    (6, "API Gateway", "Platform", 249.0),
]

TICKETS = [
    "Unable to export dashboard report",
    "SSO login loop for admin user",
    "Billing invoice missing PO number",
    "API rate limit clarification",
    "Data connector sync delay",
    "Add two more seats to account",
    "Webhook retries failing",
    "Question about SOC 2 report",
    "Mobile app crashes on upload",
    "Request for EU data residency",
    "Refund status for annual plan",
    "Password reset email not received",
    "Dashboard latency during peak",
    "Salesforce integration mapping",
    "Enable audit log retention",
    "Unexpected charge on invoice",
    "Custom role permissions",
    "Sandbox environment access",
    "Support SLA escalation",
    "Export users to CSV",
    "SAML certificate rotation",
    "Dashboard sharing permissions",
    "Bulk delete old records",
    "API key rotation guidance",
]

PRIORITIES = ["low", "medium", "high", "urgent"]
STATUSES = ["open", "in_progress", "resolved"]


def initialize_database(force=False):
    path = Path(settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if force and path.exists():
        path.unlink()

    connection = sqlite3.connect(path)
    try:
        connection.executescript(SCHEMA)
        connection.commit()
        count = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        if count == 0:
            _seed(connection)
        connection.commit()
    finally:
        connection.close()
    return path


def _seed(connection):
    connection.executemany(
        "INSERT INTO customers (id, name, company, country, email, signup_date) VALUES (?, ?, ?, ?, ?, ?)",
        CUSTOMERS,
    )
    connection.executemany(
        "INSERT INTO products (id, name, category, unit_price) VALUES (?, ?, ?, ?)",
        PRODUCTS,
    )

    rng = random.Random(42)
    statuses = ["delivered", "pending", "cancelled", "refunded"]
    weights = [68, 12, 10, 10]
    orders = []
    for order_id in range(1, 121):
        customer_id = rng.randint(1, len(CUSTOMERS))
        product_id = rng.randint(1, len(PRODUCTS))
        quantity = rng.randint(1, 8)
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        status = rng.choices(statuses, weights=weights, k=1)[0]
        orders.append((order_id, customer_id, product_id, quantity, f"2025-{month:02d}-{day:02d}", status))
    connection.executemany(
        "INSERT INTO orders (id, customer_id, product_id, quantity, order_date, status) VALUES (?, ?, ?, ?, ?, ?)",
        orders,
    )

    tickets = []
    for ticket_id, subject in enumerate(TICKETS, start=1):
        customer_id = rng.randint(1, len(CUSTOMERS))
        priority = rng.choices(PRIORITIES, weights=[30, 45, 20, 5], k=1)[0]
        status = rng.choices(STATUSES, weights=[25, 20, 55], k=1)[0]
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        tickets.append((ticket_id, customer_id, subject, priority, status, f"2025-{month:02d}-{day:02d}"))
    connection.executemany(
        "INSERT INTO tickets (id, customer_id, subject, priority, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        tickets,
    )


def get_connection():
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    return connection


def get_schema():
    return {
        "customers": ["id", "name", "company", "country", "email", "signup_date"],
        "products": ["id", "name", "category", "unit_price"],
        "orders": ["id", "customer_id", "product_id", "quantity", "order_date", "status"],
        "tickets": ["id", "customer_id", "subject", "priority", "status", "created_at"],
    }


def run_query(sql, params=(), limit=100):
    started = time.perf_counter()
    statement = sql.strip().rstrip(";").strip()
    lowered = statement.lower()

    if not lowered.startswith(("select", "with")):
        return {
            "sql": statement,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "error": "Only read-only SELECT queries are allowed.",
            "duration_ms": 0.0,
        }
    if ";" in statement:
        return {
            "sql": statement,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "error": "Multiple SQL statements are not allowed.",
            "duration_ms": 0.0,
        }

    try:
        with get_connection() as connection:
            cursor = connection.execute(statement, params)
            rows = cursor.fetchmany(limit)
            columns = [item[0] for item in cursor.description] if cursor.description else []
            data = [
                {column: _json_value(row[column]) for column in columns}
                for row in rows
            ]
        return {
            "sql": statement,
            "columns": columns,
            "rows": data,
            "row_count": len(data),
            "error": None,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        }
    except sqlite3.Error as exc:
        return {
            "sql": statement,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "error": str(exc),
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        }


def _json_value(value):
    if isinstance(value, (int, float, str)) or value is None:
        return value
    return str(value)


def _status_in_question(question):
    for status in ("cancelled", "refunded", "pending", "delivered"):
        if status in question:
            return status
    return None


def _find_country(question):
    for _, _, company, country, _, _ in CUSTOMERS:
        if country.lower() in question:
            return country
    return None


def _find_product(question):
    for product_id, name, category, price in PRODUCTS:
        if name.lower() in question:
            return product_id, name, category, price
    return None


def _plan(question):
    q = question.lower()
    year_match = re.search(r"\b(20\d{2})\b", q)
    year = year_match.group(1) if year_match else None

    if ("refund" in q or "cancelled" in q or "pending" in q or "delivered" in q) and "order" in q:
        status = _status_in_question(q) or "cancelled"
        return {
            "intent": "status_count",
            "status": status,
            "sql": "SELECT COUNT(*) AS order_count FROM orders WHERE status = ?",
            "params": (status,),
        }

    if "ticket" in q or "support issue" in q:
        if "open" in q or "unresolved" in q:
            return {
                "intent": "open_tickets",
                "sql": (
                    "SELECT priority, COUNT(*) AS tickets FROM tickets "
                    "WHERE status != 'resolved' GROUP BY priority ORDER BY tickets DESC"
                ),
                "params": (),
            }
        return {
            "intent": "ticket_status",
            "sql": "SELECT status, COUNT(*) AS tickets FROM tickets GROUP BY status ORDER BY tickets DESC",
            "params": (),
        }

    revenue_words = ("revenue", "sales", "spend", "spent", "booked")
    if any(word in q for word in revenue_words):
        if "month" in q:
            sql = (
                "SELECT strftime('%Y-%m', o.order_date) AS month, "
                "ROUND(SUM(o.quantity * p.unit_price), 2) AS revenue "
                "FROM orders o JOIN products p ON p.id = o.product_id "
                "WHERE o.status NOT IN ('cancelled', 'refunded') "
            )
            params = []
            if year:
                sql += "AND strftime('%Y', o.order_date) = ? "
                params.append(year)
            sql += "GROUP BY month ORDER BY month"
            return {"intent": "monthly_revenue", "sql": sql, "params": tuple(params)}
        if "country" in q:
            return {
                "intent": "revenue_by_country",
                "sql": (
                    "SELECT c.country, ROUND(SUM(o.quantity * p.unit_price), 2) AS revenue "
                    "FROM orders o JOIN customers c ON c.id = o.customer_id "
                    "JOIN products p ON p.id = o.product_id "
                    "WHERE o.status NOT IN ('cancelled', 'refunded') "
                    "GROUP BY c.country ORDER BY revenue DESC"
                ),
                "params": (),
            }
        if "product" in q or "plan" in q:
            return {
                "intent": "product_performance",
                "sql": (
                    "SELECT p.name, SUM(o.quantity) AS units_sold, "
                    "ROUND(SUM(o.quantity * p.unit_price), 2) AS revenue "
                    "FROM orders o JOIN products p ON p.id = o.product_id "
                    "WHERE o.status NOT IN ('cancelled', 'refunded') "
                    "GROUP BY p.id ORDER BY revenue DESC"
                ),
                "params": (),
            }
        if "customer" in q and ("top" in q or "most" in q or "highest" in q or "best" in q):
            return {
                "intent": "top_customers",
                "sql": (
                    "SELECT c.company, ROUND(SUM(o.quantity * p.unit_price), 2) AS revenue, "
                    "COUNT(o.id) AS orders "
                    "FROM orders o JOIN customers c ON c.id = o.customer_id "
                    "JOIN products p ON p.id = o.product_id "
                    "WHERE o.status NOT IN ('cancelled', 'refunded') "
                    "GROUP BY c.id ORDER BY revenue DESC LIMIT 5"
                ),
                "params": (),
            }
        sql = (
            "SELECT ROUND(SUM(o.quantity * p.unit_price), 2) AS total_revenue "
            "FROM orders o JOIN products p ON p.id = o.product_id "
            "WHERE o.status NOT IN ('cancelled', 'refunded') "
        )
        params = []
        if year:
            sql += "AND strftime('%Y', o.order_date) = ?"
            params.append(year)
        return {"intent": "total_revenue", "sql": sql, "params": tuple(params)}

    if "average order" in q or "avg order" in q or ("average" in q and "order" in q):
        return {
            "intent": "average_order_value",
            "sql": (
                "SELECT ROUND(AVG(order_total), 2) AS average_order_value FROM ("
                "SELECT o.id, SUM(o.quantity * p.unit_price) AS order_total "
                "FROM orders o JOIN products p ON p.id = o.product_id "
                "WHERE o.status NOT IN ('cancelled', 'refunded') GROUP BY o.id)"
            ),
            "params": (),
        }

    if ("product" in q or "products" in q) and ("top" in q or "best" in q or "most" in q):
        return {
            "intent": "product_performance",
            "sql": (
                "SELECT p.name, SUM(o.quantity) AS units_sold, "
                "ROUND(SUM(o.quantity * p.unit_price), 2) AS revenue "
                "FROM orders o JOIN products p ON p.id = o.product_id "
                "WHERE o.status NOT IN ('cancelled', 'refunded') "
                "GROUP BY p.id ORDER BY revenue DESC"
            ),
            "params": (),
        }

    if "how many" in q and "customer" in q:
        return {"intent": "customer_count", "sql": "SELECT COUNT(*) AS customers FROM customers", "params": ()}

    country = _find_country(q)
    if country:
        return {
            "intent": "customers_in_country",
            "country": country,
            "sql": "SELECT company, name, country FROM customers WHERE country = ? ORDER BY company",
            "params": (country,),
        }

    if "customer" in q and ("list" in q or "show" in q or "which" in q):
        return {
            "intent": "customer_list",
            "sql": "SELECT company, country, signup_date FROM customers ORDER BY company",
            "params": (),
        }

    product = _find_product(q)
    if product:
        _, name, category, price = product
        return {
            "intent": "product_price",
            "product_name": name,
            "sql": "SELECT name, category, unit_price FROM products WHERE name = ?",
            "params": (name,),
        }

    if "how many" in q and "order" in q:
        return {"intent": "order_count", "sql": "SELECT COUNT(*) AS orders FROM orders", "params": ()}

    if ("recent" in q or "latest" in q) and "order" in q:
        return {
            "intent": "recent_orders",
            "sql": (
                "SELECT o.id, c.company, p.name AS product, o.quantity, o.order_date, o.status "
                "FROM orders o JOIN customers c ON c.id = o.customer_id "
                "JOIN products p ON p.id = o.product_id "
                "ORDER BY o.order_date DESC LIMIT 8"
            ),
            "params": (),
        }

    if "order" in q:
        return {
            "intent": "status_count",
            "status": _status_in_question(q) or "cancelled",
            "sql": "SELECT COUNT(*) AS order_count FROM orders WHERE status = ?",
            "params": (_status_in_question(q) or "cancelled",),
        }

    return {
        "intent": "overview",
        "sql": (
            "SELECT c.company, p.name AS product, o.quantity, o.order_date, o.status "
            "FROM orders o JOIN customers c ON c.id = o.customer_id "
            "JOIN products p ON p.id = o.product_id ORDER BY o.order_date DESC LIMIT 5"
        ),
        "params": (),
    }


def _money(value):
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _summarize(intent, columns, rows, plan):
    if not rows:
        return "No matching records were found in the demo database."

    if intent == "total_revenue":
        return f"Total recognized revenue is {_money(rows[0]['total_revenue'])} (cancelled and refunded orders excluded)."
    if intent == "average_order_value":
        return f"The average order value is {_money(rows[0]['average_order_value'])}."
    if intent == "top_customers":
        lines = ["Top customers by recognized revenue:"]
        for index, row in enumerate(rows, start=1):
            lines.append(f"{index}. {row['company']} — {_money(row['revenue'])} ({row['orders']} orders)")
        return "\n".join(lines)
    if intent == "revenue_by_country":
        lines = ["Revenue by country:"]
        for row in rows:
            lines.append(f"- {row['country']}: {_money(row['revenue'])}")
        return "\n".join(lines)
    if intent == "monthly_revenue":
        lines = ["Monthly recognized revenue:"]
        for row in rows:
            lines.append(f"- {row['month']}: {_money(row['revenue'])}")
        return "\n".join(lines)
    if intent == "product_performance":
        lines = ["Product performance (recognized revenue):"]
        for row in rows:
            lines.append(f"- {row['name']}: {row['units_sold']} units, {_money(row['revenue'])}")
        return "\n".join(lines)
    if intent == "status_count":
        status = plan.get("status", "cancelled")
        return f"There are {rows[0]['order_count']} {status} orders."
    if intent == "open_tickets":
        total = sum(row["tickets"] for row in rows)
        detail = ", ".join(f"{row['priority']}={row['tickets']}" for row in rows)
        return f"There are {total} open or in-progress support tickets ({detail})."
    if intent == "ticket_status":
        detail = ", ".join(f"{row['status']}={row['tickets']}" for row in rows)
        return f"Support tickets by status: {detail}."
    if intent == "customer_count":
        return f"There are {rows[0]['customers']} customers in the demo database."
    if intent == "order_count":
        return f"There are {rows[0]['orders']} orders in the demo database."
    if intent == "customers_in_country":
        country = plan.get("country", "the selected country")
        companies = ", ".join(row["company"] for row in rows)
        return f"Customers in {country}: {companies}."
    if intent == "customer_list":
        return "Customers: " + ", ".join(f"{row['company']} ({row['country']})" for row in rows) + "."
    if intent == "product_price":
        row = rows[0]
        return f"{row['name']} is in the {row['category']} category and costs {_money(row['unit_price'])} per unit."
    if intent == "recent_orders":
        lines = ["Most recent orders:"]
        for row in rows:
            lines.append(
                f"- #{row['id']} {row['company']} — {row['product']} x{row['quantity']} "
                f"on {row['order_date']} ({row['status']})"
            )
        return "\n".join(lines)
    return f"Query returned {len(rows)} rows across {len(columns)} columns."


def answer_question(question):
    started = time.perf_counter()
    initialize_database()
    plan = _plan(question)
    result = run_query(plan["sql"], plan.get("params", ()))
    answer = ""
    if result["error"]:
        answer = f"I could not query the database: {result['error']}"
    else:
        answer = _summarize(plan["intent"], result["columns"], result["rows"], plan)

    return {
        "question": question,
        "intent": plan["intent"],
        "answer": answer,
        "sql": result["sql"],
        "params": list(plan.get("params", ())),
        "columns": result["columns"],
        "rows": result["rows"],
        "row_count": result["row_count"],
        "error": result["error"],
        "duration_ms": round((time.perf_counter() - started) * 1000, 2),
    }


def health():
    try:
        initialize_database()
        with get_connection() as connection:
            counts = {
                table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("customers", "products", "orders", "tickets")
            }
        return {"status": "ready", "path": str(settings.database_path), "counts": counts}
    except sqlite3.Error as exc:
        return {"status": "error", "path": str(settings.database_path), "error": str(exc)}
