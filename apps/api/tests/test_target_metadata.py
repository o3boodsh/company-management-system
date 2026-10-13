"""Target deltas and migration safety, verified without any database."""

import ast
from copy import deepcopy
import hashlib
import importlib.util
from io import StringIO
import subprocess

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.dialects import mysql

from app.db.base import Base
from test_metadata import API_ROOT, TABLE_ORDER, exported_schema, table_snapshot, sql_tokens


def revision(name):
    path = API_ROOT / "alembic/versions" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AlterRecorder:
    def __init__(self):
        self.calls = []

    def alter_column(self, *args, **kwargs):
        self.calls.append((args, kwargs))


def capture(name, monkeypatch, direction="upgrade"):
    module = revision(name)
    recorder = AlterRecorder()
    monkeypatch.setattr(module, "op", recorder)
    getattr(module, direction)()
    return recorder.calls


def test_b0_bytes_are_immutable_from_reviewed_commit():
    path = "apps/api/alembic/versions/b0_company_schema.py"
    historical = subprocess.check_output(["git", "show", f"3283eaba1bb0edec762de6d20aa56ef279c5ef9f:{path}"], cwd=API_ROOT)
    current = (API_ROOT / "alembic/versions/b0_company_schema.py").read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(current).digest() == hashlib.sha256(historical).digest()


@pytest.mark.parametrize("name", TABLE_ORDER)
def test_target_has_only_the_two_approved_definition_changes(name):
    expected = deepcopy(exported_schema()[name])
    if name == "employees":
        expected["columns"]["salary"]["type"] = "decimal(12,2)"
        expected["columns"]["hire_date"]["default"] = None
    actual = table_snapshot(Base.metadata.tables[name])
    assert list(actual["columns"]) == list(expected["columns"])
    assert actual == expected


def test_t1_changes_only_salary_type_and_preserves_existing_attributes(monkeypatch):
    calls = capture("t1_salary_precision", monkeypatch)
    assert len(calls) == 1
    args, options = calls[0]
    assert args == ("employees", "salary")
    assert set(options) == {"existing_type", "type_", "existing_nullable", "existing_server_default"}
    assert (options["existing_type"].precision, options["existing_type"].scale) == (10, 0)
    assert (options["type_"].precision, options["type_"].scale) == (12, 2)
    assert options["existing_nullable"] is False
    assert options["existing_server_default"] is None


def test_t2_changes_only_hire_date_default(monkeypatch):
    calls = capture("t2_hire_date_default", monkeypatch)
    assert len(calls) == 1
    args, options = calls[0]
    assert args == ("employees", "hire_date")
    assert set(options) == {"existing_type", "existing_nullable", "existing_server_default", "server_default"}
    assert isinstance(options["existing_type"], mysql.DATE)
    assert options["existing_nullable"] is True
    assert sql_tokens(str(options["existing_server_default"])) == sql_tokens("(curdate())")
    assert options["server_default"] is None


def test_t1_downgrade_refuses_before_emitting_operations(monkeypatch):
    module = revision("t1_salary_precision")
    recorder = AlterRecorder()
    monkeypatch.setattr(module, "op", recorder)
    with pytest.raises(RuntimeError, match="downgrade is disabled"):
        module.downgrade()
    assert recorder.calls == []


def test_t2_reverse_restores_default_only(monkeypatch):
    calls = capture("t2_hire_date_default", monkeypatch, "downgrade")
    assert len(calls) == 1
    args, options = calls[0]
    assert args == ("employees", "hire_date")
    assert set(options) == {"existing_type", "existing_nullable", "existing_server_default", "server_default"}
    assert isinstance(options["existing_type"], mysql.DATE)
    assert options["existing_nullable"] is True
    assert options["existing_server_default"] is None
    assert sql_tokens(str(options["server_default"])) == sql_tokens("(curdate())")


def test_target_migrations_are_independent_and_have_no_data_operations():
    for name in ("t1_salary_precision", "t2_hire_date_default"):
        source = (API_ROOT / "alembic/versions" / f"{name}.py").read_text()
        tree = ast.parse(source)
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        assert not any(n and n.startswith("app") for n in imports)
        calls = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        assert not calls.intersection({"execute", "connect", "create_engine", "create_all", "drop_table", "reflect"})


def test_complete_revision_chain_compiles_into_memory_only():
    buffer = StringIO()
    context = MigrationContext.configure(dialect_name="mysql", opts={"as_sql": True, "output_buffer": buffer})
    with Operations.context(context):
        for name in ("b0_company_schema", "t1_salary_precision", "t2_hire_date_default"):
            revision(name).upgrade()
    ddl = buffer.getvalue()
    assert "MODIFY salary DECIMAL(12, 2) NOT NULL" in ddl
    assert "ALTER COLUMN hire_date DROP DEFAULT" in ddl
    assert ddl.index("CREATE TABLE employees") < ddl.index("MODIFY salary") < ddl.index("DROP DEFAULT")
    assert not any(word in ddl for word in ("INSERT", "UPDATE ", "DELETE ", "DROP TABLE"))
    assert ddl.count("CREATE TABLE ") == 4


def test_revision_parent_links_are_deterministic():
    t1, t2 = revision("t1_salary_precision"), revision("t2_hire_date_default")
    assert t1.revision == "t1_salary_precision" and t1.down_revision == "b0_company_schema"
    assert t2.revision == "t2_hire_date_default" and t2.down_revision == t1.revision
    assert t1.branch_labels is t2.branch_labels is t1.depends_on is t2.depends_on is None
