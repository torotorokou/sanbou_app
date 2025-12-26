import psycopg

from app.config.settings import settings


def get_conn():
    # psycopg3: autocommit=False (withでcommit/rollback)
    return psycopg.connect(settings.database_url)
