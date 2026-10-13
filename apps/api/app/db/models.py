"""Four ORM mappings for the approved T2 target; no migrations run on import."""

from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index, UniqueConstraint, text
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Department(Base):
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("department_name", name="department_name"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_0900_ai_ci"},
    )

    department_id: Mapped[int] = mapped_column(mysql.INTEGER(unsigned=False), primary_key=True, nullable=False, autoincrement=True)
    department_name: Mapped[str] = mapped_column(mysql.VARCHAR(100), nullable=False)
    employees: Mapped[list["Employee"]] = relationship(
        back_populates="department", cascade="save-update, merge", passive_deletes="all"
    )


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("project_name", name="project_name"),
        CheckConstraint("(`budget` >= 0)", name="projects_chk_1"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_0900_ai_ci"},
    )

    project_id: Mapped[int] = mapped_column(mysql.INTEGER(unsigned=False), primary_key=True, nullable=False, autoincrement=True)
    project_name: Mapped[str] = mapped_column(mysql.VARCHAR(150), nullable=False)
    start_date: Mapped[date] = mapped_column(mysql.DATE(), nullable=False)
    budget: Mapped[Decimal | None] = mapped_column(mysql.DECIMAL(12, 2, asdecimal=True), nullable=True, server_default=text("NULL"))
    assignments: Mapped[list["EmployeeProject"]] = relationship(
        back_populates="project", cascade="save-update, merge", passive_deletes="all"
    )


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("email", name="email"),
        Index("department_id", "department_id"),
        ForeignKeyConstraint(["department_id"], ["departments.department_id"], name="employees_ibfk_1"),
        CheckConstraint("(`salary` >= 0)", name="chk_salary_positive"),
        CheckConstraint(
            "(`employee_status` in (_utf8mb4'Active',_utf8mb4'Inactive',_utf8mb4'On Leave'))",
            name="chk_employment_status",
        ),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_0900_ai_ci"},
    )

    employee_id: Mapped[int] = mapped_column(mysql.INTEGER(unsigned=False), primary_key=True, nullable=False, autoincrement=True)
    full_name: Mapped[str] = mapped_column(mysql.VARCHAR(100), nullable=False)
    salary: Mapped[Decimal] = mapped_column(mysql.DECIMAL(12, 2, asdecimal=True), nullable=False)
    department_id: Mapped[int | None] = mapped_column(mysql.INTEGER(unsigned=False), nullable=True, server_default=text("NULL"))
    email: Mapped[str | None] = mapped_column(mysql.VARCHAR(150), nullable=True, server_default=text("NULL"))
    employee_status: Mapped[str] = mapped_column(mysql.VARCHAR(20), nullable=False, server_default=text("'Active'"))
    hire_date: Mapped[date | None] = mapped_column(mysql.DATE(), nullable=True)
    department: Mapped[Department | None] = relationship(back_populates="employees")
    assignments: Mapped[list["EmployeeProject"]] = relationship(
        back_populates="employee", cascade="save-update, merge", passive_deletes="all"
    )


class EmployeeProject(Base):
    __tablename__ = "employee_projects"
    __table_args__ = (
        Index("project_id", "project_id"),
        ForeignKeyConstraint(["employee_id"], ["employees.employee_id"], name="employee_projects_ibfk_1"),
        ForeignKeyConstraint(["project_id"], ["projects.project_id"], name="employee_projects_ibfk_2"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_0900_ai_ci"},
    )

    employee_id: Mapped[int] = mapped_column(mysql.INTEGER(unsigned=False), primary_key=True, nullable=False, autoincrement=False)
    project_id: Mapped[int] = mapped_column(mysql.INTEGER(unsigned=False), primary_key=True, nullable=False, autoincrement=False)
    role: Mapped[str] = mapped_column(mysql.VARCHAR(50), nullable=False)
    employee: Mapped[Employee] = relationship(back_populates="assignments")
    project: Mapped[Project] = relationship(back_populates="assignments")
