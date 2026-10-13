"""Approved salary precision only; no currency conversion or data import."""

from alembic import op
from sqlalchemy.dialects import mysql

revision = "t1_salary_precision"
down_revision = "b0_company_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "employees", "salary",
        existing_type=mysql.DECIMAL(10, 0, asdecimal=True),
        type_=mysql.DECIMAL(12, 2, asdecimal=True),
        existing_nullable=False, existing_server_default=None,
    )


def downgrade():
    # Fractional values cannot safely be represented by the historical type.
    raise RuntimeError("T1 downgrade is disabled; reviewed data-safe recovery requires separate approval")
