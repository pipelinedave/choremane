import os
import psycopg2

# Environment-based configuration
DB_HOST = os.getenv("POSTGRES_HOST", "postgres-service")
DB_NAME = os.getenv("POSTGRES_DB", "choresdb")
DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn
