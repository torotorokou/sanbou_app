import os
import psycopg2
from sqlalchemy import create_engine


def get_pg_connection():
    """
    環境変数からPostgreSQL接続情報を取得し、接続オブジェクトを返す。
    """
    user = os.getenv("POSTGRES_USER", "myuser")
    password = os.getenv("POSTGRES_PASSWORD", "mypassword")
    db = os.getenv("POSTGRES_DB", "myapp")
    host = os.getenv("POSTGRES_HOST", "localhost")  # Dockerなら"db"
    port = os.getenv("POSTGRES_PORT", "5432")
    return psycopg2.connect(
        dbname=db, user=user, password=password, host=host, port=port
    )


def get_engine():
    # 環境変数またはデフォルト値で作成
    user = os.getenv("POSTGRES_USER", "myuser")
    password = os.getenv("POSTGRES_PASSWORD", "mypassword")
    host = os.getenv("POSTGRES_HOST", "postgres_db")  # Dockerならpostgres_db
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "myapp")
    url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return create_engine(url)
