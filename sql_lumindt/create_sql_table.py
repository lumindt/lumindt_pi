import psycopg2
import os

DB_CONFIG = {
    "dbname": "test_data",
    "user": "postgres",
    "password": "Lumindt2themoon",
    "host": "10.1.10.12",
    "port": "5432",
}

SQL_FILE = "schema.sql"

def connect_db():
    return psycopg2.connect(**DB_CONFIG)

def create_table_from_file():
    if not os.path.exists(SQL_FILE):
        raise FileNotFoundError(f"SQL file not found: {SQL_FILE}")

    with open(SQL_FILE, "r") as f:
        sql_script = f.read()

    conn = connect_db()
    conn.autocommit = True
    cur = conn.cursor()

    try:
        cur.execute(sql_script)
        print(f"Table created or verified successfully from {SQL_FILE}")
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    create_table_from_file()
