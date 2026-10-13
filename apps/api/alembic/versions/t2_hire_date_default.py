"""Approved removal of the date default; never rewrite historical dates."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "t2_hire_date_default"
down_revision = "t1_salary_precision"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "employees", "hire_date", existing_type=mysql.DATE(),
        existing_nullable=True, existing_server_default=sa.text("(curdate())"),
        server_default=None,
    )


def downgrade():
    # Restore the default for future inserts only; no row updates.
    op.alter_column(
        "employees", "hire_date", existing_type=mysql.DATE(),
        existing_nullable=True, existing_server_default=None,
        server_default=sa.text("(curdate())"),
    )
