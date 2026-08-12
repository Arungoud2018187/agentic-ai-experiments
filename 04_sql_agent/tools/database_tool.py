import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "company.db"


def initialize_database():

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.executescript("""
    DROP TABLE IF EXISTS employees;
    DROP TABLE IF EXISTS departments;
    DROP TABLE IF EXISTS projects;

    CREATE TABLE departments (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        location TEXT
    );

    CREATE TABLE employees (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER,
        department_id INTEGER,
        position TEXT,
        salary REAL,
        experience INTEGER
    );

    CREATE TABLE projects (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        department_id INTEGER,
        budget REAL,
        status TEXT
    );

    INSERT INTO departments VALUES
    (1, 'Engineering', 'Hyderabad'),
    (2, 'Security', 'Bangalore'),
    (3, 'Marketing', 'Mumbai'),
    (4, 'Finance', 'Delhi');

    INSERT INTO employees VALUES
    (1, 'Arun', 22, 1, 'Software Engineer', 85000, 2),
    (2, 'Rahul', 25, 1, 'Senior Engineer', 120000, 5),
    (3, 'Priya', 24, 2, 'Security Analyst', 95000, 3),
    (4, 'Kiran', 29, 2, 'Security Engineer', 135000, 7),
    (5, 'Sneha', 27, 3, 'Marketing Manager', 110000, 6),
    (6, 'Vikram', 31, 4, 'Financial Analyst', 105000, 8),
    (7, 'Ananya', 23, 1, 'Junior Developer', 65000, 1),
    (8, 'Rohit', 28, 2, 'SOC Analyst', 90000, 5),
    (9, 'Meena', 26, 3, 'Marketing Executive', 70000, 4),
    (10, 'Sanjay', 35, 4, 'Finance Manager', 150000, 12);

    INSERT INTO projects VALUES
    (1, 'AI Platform', 1, 500000, 'Active'),
    (2, 'SOC Automation', 2, 350000, 'Active'),
    (3, 'Marketing Campaign', 3, 150000, 'Completed'),
    (4, 'Financial Audit', 4, 200000, 'Pending');
    """)

    conn.commit()
    conn.close()