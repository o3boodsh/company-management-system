"""Manually authored exported baseline; no data, T1, or T2 changes.

Revision ID: b0_company_schema
Revises: None
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "b0_company_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # This revision is intentionally independent of mutable application models.
    op.create_table(
        "departments",
        sa.Column("department_id", mysql.INTEGER(unsigned=False), nullable=False, autoincrement=True),
        sa.Column("department_name", mysql.VARCHAR(100), nullable=False),
        sa.PrimaryKeyConstraint("department_id"),
        sa.UniqueConstraint("department_name", name="department_name"),
        mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_table(
        "projects",
        sa.Column("project_id", mysql.INTEGER(unsigned=False), nullable=False, autoincrement=True),
        sa.Column("project_name", mysql.VARCHAR(150), nullable=False),
        sa.Column("start_date", mysql.DATE(), nullable=False),
        sa.Column("budget", mysql.DECIMAL(12, 2, asdecimal=True), nullable=True, server_default=sa.text("NULL")),
        sa.PrimaryKeyConstraint("project_id"),
        sa.UniqueConstraint("project_name", name="project_name"),
        sa.CheckConstraint("(`budget` >= 0)", name="projects_chk_1"),
        mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_table(
        "employees",
        sa.Column("employee_id", mysql.INTEGER(unsigned=False), nullable=False, autoincrement=True),
        sa.Column("full_name", mysql.VARCHAR(100), nullable=False),
        sa.Column("salary", mysql.DECIMAL(10, 0, asdecimal=True), nullable=False),
        sa.Column("department_id", mysql.INTEGER(unsigned=False), nullable=True, server_default=sa.text("NULL")),
        sa.Column("email", mysql.VARCHAR(150), nullable=True, server_default=sa.text("NULL")),
        sa.Column("employee_status", mysql.VARCHAR(20), nullable=False, server_default=sa.text("'Active'")),
        sa.Column("hire_date", mysql.DATE(), nullable=True, server_default=sa.text("(curdate())")),
        sa.PrimaryKeyConstraint("employee_id"),
        sa.UniqueConstraint("email", name="email"),
        sa.CheckConstraint("(`salary` >= 0)", name="chk_salary_positive"),
        sa.CheckConstraint("(`employee_status` in (_utf8mb4'Active',_utf8mb4'Inactive',_utf8mb4'On Leave'))", name="chk_employment_status"),
        mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_0900_ai_ci",
    )
    # Create explicitly named supporting indexes before FKs so MySQL need not
    # invent an automatic supporting index and later replace it.
    op.create_index("department_id", "employees", ["department_id"], unique=False)
    op.create_foreign_key("employees_ibfk_1", "employees", "departments", ["department_id"], ["department_id"])
    op.create_table(
        "employee_projects",
        sa.Column("employee_id", mysql.INTEGER(unsigned=False), nullable=False, autoincrement=False),
        sa.Column("project_id", mysql.INTEGER(unsigned=False), nullable=False, autoincrement=False),
        sa.Column("role", mysql.VARCHAR(50), nullable=False),
        sa.PrimaryKeyConstraint("employee_id", "project_id"),
        mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index("project_id", "employee_projects", ["project_id"], unique=False)
    op.create_foreign_key("employee_projects_ibfk_1", "employee_projects", "employees", ["employee_id"], ["employee_id"])
    op.create_foreign_key("employee_projects_ibfk_2", "employee_projects", "projects", ["project_id"], ["project_id"])


def downgrade():
    # Never use baseline teardown as recovery for a populated database.
    # env.py currently prohibits all online execution, including this path.
    op.drop_table("employee_projects")
    op.drop_table("employees")
    op.drop_table("projects")
    op.drop_table("departments")
