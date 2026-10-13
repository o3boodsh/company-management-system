"""Compare two independent schema definitions with the unexecuted SQL export."""

import ast
from contextlib import contextmanager
import importlib.util
from io import StringIO
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import configure_mappers
from sqlalchemy.schema import CreateIndex, CreateTable

from app.db.base import Base
from app.db.models import Department, Employee, EmployeeProject, Project

API_ROOT = Path(__file__).resolve().parents[1]
ROOT = API_ROOT.parents[1]
REVISION_PATH = API_ROOT / "alembic/versions/b0_company_schema.py"
TABLE_ORDER = ["departments", "projects", "employees", "employee_projects"]


def sql_tokens(value):
    """Ignore spelling/outer-parenthesis differences, preserving quoted literals."""
    tokens = re.findall(r"'(?:''|[^'])*'|[a-zA-Z_]\w*|\d+|[^\s]", value.replace("`", ""))
    while tokens and tokens[0] == "(" and tokens[-1] == ")":
        depth = 0
        encloses_all = True
        for index, token in enumerate(tokens):
            depth += (token == "(") - (token == ")")
            if depth == 0 and index < len(tokens) - 1:
                encloses_all = False
                break
        if not encloses_all:
            break
        tokens = tokens[1:-1]
    return tuple(token if token.startswith("'") else token.lower() for token in tokens)


def column_names(value):
    return tuple(re.findall(r"`([^`]+)`", value))


def exported_schema():
    """Parse only the known dump grammar as text, never SQL/eval/reflection."""
    exported = {}
    dump = (ROOT / "database/company_schema.sql").read_text(encoding="utf-8")
    for match in re.finditer(r"CREATE TABLE `([^`]+)` \(\n(.*?)\n\) ([^;]+);", dump, re.S):
        name, body, options = match.groups()
        columns, unique, indexes, checks, fks = {}, {}, {}, {}, {}
        primary_key = None
        for line in body.splitlines():
            line = line.strip().rstrip(",")
            column = re.fullmatch(r"`([^`]+)` (int|varchar\(\d+\)|decimal\(\d+,\d+\)|date)(.*)", line)
            if column:
                column_name, kind, attributes = column.groups()
                default = re.search(r" DEFAULT (.+)$", attributes)
                columns[column_name] = {
                    "type": kind, "unsigned": " unsigned" in attributes,
                    "nullable": "NOT NULL" not in attributes,
                    "default": sql_tokens(default.group(1)) if default else None,
                    "autoincrement": "AUTO_INCREMENT" in attributes,
                }
                continue
            pk = re.fullmatch(r"PRIMARY KEY \((.*)\)", line)
            key = re.fullmatch(r"(UNIQUE KEY|KEY) `([^`]+)` \((.*)\)", line)
            fk = re.fullmatch(r"CONSTRAINT `([^`]+)` FOREIGN KEY \((.*?)\) REFERENCES `([^`]+)` \((.*?)\)", line)
            check = re.fullmatch(r"CONSTRAINT `([^`]+)` CHECK \((.*)\)", line)
            if pk:
                primary_key = column_names(pk.group(1))
            elif key:
                (unique if key.group(1) == "UNIQUE KEY" else indexes)[key.group(2)] = column_names(key.group(3))
            elif fk:
                fks[fk.group(1)] = (column_names(fk.group(2)), tuple(
                    f"{fk.group(3)}.{parent}" for parent in column_names(fk.group(4))
                ), None, None)
            elif check:
                checks[check.group(1)] = sql_tokens(check.group(2))
            else:
                raise AssertionError(f"Unrecognized exported definition for {name}")
        exported[name] = {
            "columns": columns, "pk": primary_key, "unique": unique, "indexes": indexes,
            "checks": checks, "fks": fks,
            "options": {
                "mysql_engine": re.search(r"ENGINE=(\w+)", options).group(1),
                "mysql_charset": re.search(r"DEFAULT CHARSET=(\w+)", options).group(1),
                "mysql_collate": re.search(r"COLLATE=(\w+)", options).group(1),
            },
        }
    assert len(exported) == 4
    return exported


def table_snapshot(table):
    columns = {}
    for column in table.columns:
        kind = re.sub(r"\s+", "", column.type.compile(dialect=mysql.dialect())).lower()
        if kind == "integer":
            kind = "int"
        columns[column.name] = {
            "type": kind, "unsigned": getattr(column.type, "unsigned", False),
            "nullable": column.nullable,
            "default": sql_tokens(str(column.server_default.arg)) if column.server_default is not None else None,
            "autoincrement": column.autoincrement is True,
        }
        assert column.default is None, "No invented client-side default"
    return {
        "columns": columns,
        "pk": tuple(column.name for column in table.primary_key.columns),
        "unique": {key.name: tuple(column.name for column in key.columns) for key in table.constraints if isinstance(key, sa.UniqueConstraint)},
        "indexes": {index.name: tuple(column.name for column in index.columns) for index in table.indexes},
        "checks": {check.name: sql_tokens(str(check.sqltext)) for check in table.constraints if isinstance(check, sa.CheckConstraint)},
        "fks": {fk.name: (tuple(column.name for column in fk.columns), tuple(element.target_fullname for element in fk.elements), fk.ondelete, fk.onupdate) for fk in table.foreign_key_constraints},
        "options": dict(table.kwargs),
    }


def load_revision():
    spec = importlib.util.spec_from_file_location("companyos_b0", REVISION_PATH)
    revision = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(revision)
    return revision


class RecordingOperations:
    """Capture Python schema objects without Alembic SQL execution."""
    def __init__(self):
        self.metadata = sa.MetaData()
        self.events = []

    def create_table(self, name, *definitions, **options):
        self.events.append(("table", name))
        return sa.Table(name, self.metadata, *definitions, **options)

    def create_index(self, name, table, columns, unique):
        self.events.append(("index", table, name))
        sa.Index(name, *(self.metadata.tables[table].c[column] for column in columns), unique=unique)

    def create_foreign_key(self, name, source, target, local, remote):
        self.events.append(("fk", source, name))
        self.metadata.tables[source].append_constraint(sa.ForeignKeyConstraint(
            local, [f"{target}.{column}" for column in remote], name=name
        ))


@pytest.mark.parametrize("table_name", TABLE_ORDER)
def test_model_table_matches_every_exported_definition(table_name):
    expected = exported_schema()[table_name]
    actual = table_snapshot(Base.metadata.tables[table_name])
    assert list(actual["columns"]) == list(expected["columns"])
    assert actual == expected


def test_exactly_four_business_tables_and_sixteen_columns():
    assert set(Base.metadata.tables) == set(exported_schema())
    assert sum(len(table.columns) for table in Base.metadata.tables.values()) == 16
    assert all("mysql_auto_increment" not in table.kwargs for table in Base.metadata.tables.values())


def test_orm_relationships_cannot_cascade_parent_deletes():
    configure_mappers()
    for model in (Department, Employee, Project, EmployeeProject):
        for relation in sa.inspect(model).relationships:
            assert not relation.cascade.delete
            assert not relation.cascade.delete_orphan
            if relation.uselist:
                assert relation.passive_deletes == "all"
    assert tuple(EmployeeProject.__table__.primary_key.columns.keys()) == ("employee_id", "project_id")
    assert EmployeeProject.__table__.c.role.nullable is False


def test_revision_matches_export_and_model_independently(monkeypatch):
    revision = load_revision()
    recorder = RecordingOperations()
    monkeypatch.setattr(revision, "op", recorder)
    revision.upgrade()  # A recorder only, not an Alembic upgrade command.
    assert list(recorder.metadata.tables) == TABLE_ORDER
    for name in TABLE_ORDER:
        assert table_snapshot(recorder.metadata.tables[name]) == exported_schema()[name]
        assert table_snapshot(recorder.metadata.tables[name]) == table_snapshot(Base.metadata.tables[name])
    assert recorder.events == [
        ("table", "departments"), ("table", "projects"), ("table", "employees"),
        ("index", "employees", "department_id"), ("fk", "employees", "employees_ibfk_1"),
        ("table", "employee_projects"), ("index", "employee_projects", "project_id"),
        ("fk", "employee_projects", "employee_projects_ibfk_1"),
        ("fk", "employee_projects", "employee_projects_ibfk_2"),
    ]


def test_mysql_ddl_compiles_without_engine_or_connection():
    dialect = mysql.dialect()
    dialect.server_version_info = (8, 0, 34)
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=dialect))
        assert "ENGINE=InnoDB" in ddl
        assert "utf8mb4_0900_ai_ci" in ddl
        assert "AUTO_INCREMENT=" not in ddl
        for index in table.indexes:
            assert index.name in str(CreateIndex(index).compile(dialect=dialect))
    employees = str(CreateTable(Employee.__table__).compile(dialect=dialect))
    assert "DECIMAL(10, 0)" in employees
    assert "DEFAULT (curdate())" in employees
    assert "_utf8mb4'On Leave'" in employees


def test_actual_alembic_operations_render_into_memory_only():
    buffer = StringIO()
    migration_context = MigrationContext.configure(dialect_name="mysql", opts={
        "as_sql": True, "output_buffer": buffer,
    })
    assert migration_context.connection is None or migration_context.as_sql
    with Operations.context(migration_context):
        load_revision().upgrade()
    ddl = buffer.getvalue()
    assert re.findall(r"CREATE TABLE (\w+)", ddl) == TABLE_ORDER
    assert len(re.findall(r"ADD CONSTRAINT .*?FOREIGN KEY", ddl)) == 3
    assert ddl.index("CREATE INDEX department_id") < ddl.index("ADD CONSTRAINT employees_ibfk_1")
    assert ddl.index("CREATE INDEX project_id") < ddl.index("ADD CONSTRAINT employee_projects_ibfk_2")
    assert "DROP TABLE" not in ddl and "INSERT" not in ddl
    assert "AUTO_INCREMENT=" not in ddl


def test_alembic_history_is_one_root_revision_without_settings():
    script = ScriptDirectory.from_config(Config(str(API_ROOT / "alembic.ini")))
    assert script.get_heads() == ["b0_company_schema"]
    revisions = list(script.walk_revisions())
    assert len(revisions) == 1
    assert revisions[0].down_revision is None


def test_online_environment_refuses_before_configuring_or_running(monkeypatch):
    from alembic import context

    def forbidden(*args, **kwargs):
        pytest.fail("Online execution must stop before configuring migrations")

    monkeypatch.setattr(context, "is_offline_mode", lambda: False)
    monkeypatch.setattr(context, "configure", forbidden)
    monkeypatch.setattr(context, "run_migrations", forbidden)
    spec = importlib.util.spec_from_file_location("companyos_online_guard", API_ROOT / "alembic/env.py")
    with pytest.raises(RuntimeError, match="Online Alembic execution is disabled"):
        spec.loader.exec_module(importlib.util.module_from_spec(spec))


def test_offline_environment_uses_dialect_only_not_url_or_connection(monkeypatch):
    from alembic import context
    configured = []
    called = []

    @contextmanager
    def transaction():
        yield

    monkeypatch.setattr(context, "is_offline_mode", lambda: True)
    monkeypatch.setattr(context, "configure", lambda **options: configured.append(options))
    monkeypatch.setattr(context, "begin_transaction", transaction)
    monkeypatch.setattr(context, "run_migrations", lambda: called.append(True))
    spec = importlib.util.spec_from_file_location("companyos_offline_guard", API_ROOT / "alembic/env.py")
    spec.loader.exec_module(importlib.util.module_from_spec(spec))
    assert configured[0]["dialect_name"] == "mysql"
    assert "url" not in configured[0] and "connection" not in configured[0]
    assert configured[0]["target_metadata"] is Base.metadata
    assert called == [True]


def test_baseline_sources_have_no_engine_ddl_execution_or_model_dependency():
    for path in (API_ROOT / "app/db/base.py", API_ROOT / "app/db/models.py", REVISION_PATH, API_ROOT / "alembic/env.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls = [node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
                 for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, (ast.Attribute, ast.Name))]
        assert not {"create_engine", "create_all", "connect", "execute", "inspect", "reflect"}.intersection(calls)
    assert "app.db.models" not in REVISION_PATH.read_text(encoding="utf-8")


def test_cold_import_and_fastapi_startup_do_not_connect_or_run_migrations():
    # Guards run before importing our modules, unlike an ordinary pytest fixture.
    code = """
import socket, sqlalchemy, pymysql
from sqlalchemy.engine import Engine
from alembic import command
def forbidden(*args, **kwargs):
    raise AssertionError('Engine, DB access and startup migrations are forbidden')
sqlalchemy.create_engine = forbidden
sqlalchemy.engine.create_engine = forbidden
sqlalchemy.engine.create.create_engine = forbidden
Engine.connect = forbidden
Engine.raw_connection = forbidden
pymysql.connect = forbidden
pymysql.connections.Connection.connect = forbidden
socket.create_connection = forbidden
for name in ('upgrade', 'downgrade', 'stamp'):
    setattr(command, name, forbidden)
from app.db.models import Department, Employee, Project, EmployeeProject
from app.db.base import Base
from app.core.config import load_settings
from app.main import create_app
from fastapi.testclient import TestClient
assert len(Base.metadata.tables) == 4
with TestClient(create_app(load_settings({'APP_ENV': 'test', 'AUTH_MODE': 'development-stub'}))) as client:
    assert client.get('/api/v1/health/live').json() == {'data': {'status': 'ok'}}
print('Cold import/startup/liveness passed without DB or migration calls')
"""
    result = subprocess.run([sys.executable, "-B", "-c", code], cwd=API_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert "passed without DB or migration calls" in result.stdout
