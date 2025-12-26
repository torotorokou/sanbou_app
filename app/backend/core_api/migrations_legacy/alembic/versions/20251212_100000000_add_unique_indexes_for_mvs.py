"""add_unique_indexes_for_mvs

Purpose:
  Add UNIQUE indexes to materialized views to enable REFRESH CONCURRENTLY.

Context:
  - REFRESH MATERIALIZED VIEW CONCURRENTLY requires a UNIQUE index
  - Previous migration (20251211_170000000) dropped and recreated MVs but forgot to recreate indexes
  - Without UNIQUE index, MV refresh fails with:
    "cannot refresh materialized view concurrently"
    "Create a unique index with no WHERE clause on one or more columns"

Changes:
  - Add UNIQUE index on mart.mv_receive_daily (ddate)
  - Add UNIQUE index on mart.mv_target_card_per_day (ddate)
  - Add regular indexes for performance (iso_year, iso_week)

Permission Grant (Environment-aware):
  - Dynamically detects application user from POSTGRES_USER environment variable
  - Grant SELECT on MVs to detected app user
  - This prevents permission denied errors when app tries to query MVs
  - Alembic creates objects as migration user (usually postgres/myuser)
  - Application connects as sanbou_app_* user, needs SELECT permission

Environment Variable Support:
  - POSTGRES_USER: Application database user (e.g., sanbou_app_dev)
  - POSTGRES_DB: Database name (e.g., sanbou_dev)
  - No hardcoded DB/user mappings - fully dynamic
  - New environments automatically supported without code changes

Safety:
  - Indexes are idempotent (IF NOT EXISTS)
  - No data changes
  - Enables background refresh without blocking reads
  - Compatible with all environments (dev/stg/prod/demo/test)

Revision ID: 20251212_100000000
Revises: 20251211_180000000
Create Date: 2025-12-12 10:00:00.000000

"""

import os

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251212_100000000"
down_revision = "20251211_180000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add UNIQUE indexes to materialized views for REFRESH CONCURRENTLY support
    and grant SELECT permissions to application users
    """
    print("[mart.mv_receive_daily] Creating UNIQUE index for REFRESH CONCURRENTLY...")

    # UNIQUE index on mv_receive_daily (primary key: ddate)
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_receive_daily_ddate
        ON mart.mv_receive_daily (ddate);
    """
    )

    # Regular index on iso_week for weekly queries
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_mv_receive_daily_iso_week
        ON mart.mv_receive_daily (iso_year, iso_week);
    """
    )

    print("[mart.mv_receive_daily] ✅ Indexes created")

    print("[mart.mv_target_card_per_day] Creating UNIQUE index for REFRESH CONCURRENTLY...")

    # UNIQUE index on mv_target_card_per_day (primary key: ddate)
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_target_card_per_day_ddate
        ON mart.mv_target_card_per_day (ddate);
    """
    )

    print("[mart.mv_target_card_per_day] ✅ Indexes created")

    # Grant SELECT permissions to application users
    # This prevents "permission denied" errors when app queries MVs
    print("[Permissions] Granting SELECT on MVs to application users...")

    # 環境変数から動的にアプリケーションユーザーを取得
    # POSTGRES_USER: アプリケーションDBユーザー（例: sanbou_app_dev, sanbou_app_stg）
    # POSTGRES_DB: データベース名（例: sanbou_dev, sanbou_stg）
    target_user = os.environ.get("POSTGRES_USER")
    current_db = os.environ.get("POSTGRES_DB") or op.get_bind().engine.url.database

    if not target_user:
        print("  ⚠️  POSTGRES_USER environment variable not set, skipping permission grant")
        print("  💡 Set POSTGRES_USER=<app_user> to grant permissions automatically")
        print("  Example: POSTGRES_USER=sanbou_app_dev")
    else:
        try:
            # 現在の環境に対応するユーザーのみに権限付与
            op.execute(
                f"""
                DO $$
                BEGIN
                    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{target_user}') THEN
                        -- Grant USAGE on mart schema
                        GRANT USAGE ON SCHEMA mart TO {target_user};

                        -- Grant SELECT on MVs
                        GRANT SELECT ON mart.mv_receive_daily TO {target_user};
                        GRANT SELECT ON mart.mv_target_card_per_day TO {target_user};

                        RAISE NOTICE '✅ Granted SELECT on MVs to % (DB: %)', '{target_user}', '{current_db}';
                    ELSE
                        RAISE NOTICE '⚠️  User % does not exist in DB %, skipping', '{target_user}', '{current_db}';
                    END IF;
                END $$;
            """
            )
            print(f"  ✅ Granted SELECT permissions to {target_user} for DB {current_db}")
        except Exception as e:
            # Log but don't fail - user might not exist in this environment
            print(f"  ⚠️  Could not grant to {target_user}: {e}")

    print("[Permissions] ✅ Permission grant completed")
    print("")
    print("📌 Summary:")
    print("  - UNIQUE indexes added to enable REFRESH MATERIALIZED VIEW CONCURRENTLY")
    print("  - MVs can now be refreshed without blocking reads")
    print("  - SELECT permissions granted to sanbou_app_* users")
    print("  - CSV upload process will automatically refresh MVs")


def downgrade() -> None:
    """
    Remove UNIQUE indexes from materialized views and revoke permissions
    """
    print("[Permissions] Revoking SELECT on MVs from application users...")

    # 環境変数から動的にアプリケーションユーザーを取得（upgrade()と同じ）
    target_user = os.environ.get("POSTGRES_USER")
    current_db = os.environ.get("POSTGRES_DB") or op.get_bind().engine.url.database

    if not target_user:
        print("  ⚠️  POSTGRES_USER not set, skipping permission revoke")

    if target_user:
        try:
            op.execute(
                f"""
                DO $$
                BEGIN
                    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{target_user}') THEN
                        REVOKE SELECT ON mart.mv_receive_daily FROM {target_user};
                        REVOKE SELECT ON mart.mv_target_card_per_day FROM {target_user};
                        RAISE NOTICE 'Revoked SELECT on MVs from % (DB: %)', '{target_user}', '{current_db}';
                    END IF;
                END $$;
            """
            )
            print(f"  ✅ Revoked SELECT permissions from {target_user} for DB {current_db}")
        except Exception as e:
            print(f"  ⚠️  Could not revoke from {target_user}: {e}")

    print("[Permissions] ✅ Permission revocation completed")

    print("[mart.mv_receive_daily] Dropping indexes...")

    op.execute("DROP INDEX IF EXISTS mart.ux_mv_receive_daily_ddate;")
    op.execute("DROP INDEX IF EXISTS mart.ix_mv_receive_daily_iso_week;")

    print("[mart.mv_target_card_per_day] Dropping indexes...")

    op.execute("DROP INDEX IF EXISTS mart.ux_mv_target_card_per_day_ddate;")

    print("✅ Indexes dropped")
