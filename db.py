import sqlite3

DB_PATH = "livora.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT,
            age INTEGER,
            weight REAL,
            diabetes_status TEXT
        )
        """)


init_db()


def signup(email, password, name, age, weight, diabetes_status):
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO users (email, password, name, age, weight, diabetes_status) VALUES (?, ?, ?, ?, ?, ?)",
                (email, password, name, age, weight, diabetes_status),
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None


def login(email, password):
    with get_connection() as conn:
        cursor = conn.execute("SELECT id, password FROM users WHERE email=?", (email,))
        row = cursor.fetchone()

    if row is None:
        return None

    user_id, stored_password = row
    if stored_password == password:
        return user_id
    return None

