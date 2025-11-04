"""
ref_baseline_tables (deprecated / no-op)

This revision used to create ref.* tables from external SQL files.
It is now a NO-OP. The canonical creation is implemented in:
  - 20251104_210000000_ref_tables_py_baseline_safe.py

Keeping the same revision id preserves history while removing the dependency
on sql/ref/tables/*.sql for clean bootstraps.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251104_164629413"
down_revision = "20251104_163649629"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # keep schema existence for compatibility
    op.execute("CREATE SCHEMA IF NOT EXISTS ref;")


def downgrade() -> None:
    # no-op (tables are created/dropped by 20251104_210000000)
    pass