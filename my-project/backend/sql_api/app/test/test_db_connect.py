import os
import psycopg2

POSTGRES_USER = os.getenv("POSTGRES_USER", "myuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "mypassword")
POSTGRES_DB = os.getenv("POSTGRES_DB", "myapp")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")  # Docker環境なら"db"
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

try:
    conn = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
    )
    print("✅ PostgreSQLに接続成功！")
    conn.close()
except Exception as e:
    print("❌ PostgreSQL接続エラー:", e)
