# CompanyOS Alembic adoption and migration plan

Status: Phase 0 specification for review, 2026-10-11. **No migration files, executable SQL, commands, database connections, or schema/data mutations are delivered or authorized.** This plan describes future work after approval.

## Inputs and invariants

Read [database-design.md](database-design.md), [ERDs](erd.md), [decision register](open-decisions.md), and the unmodified [export](../database/company_schema.sql). Preserve four business tables, IDs, rows, composite assignment PK, restrictive FKs, indexes, and checks. The legacy script is not a migration source. The export contains DROP TABLE statements and disables checks temporarily; never replay it over populated company_db as an adoption method.

Owner-confirmed: all new MVP monetary values are USD, salaries monthly and budgets USD. Preserve company_db without modification; no import, conversion, relabeling, reinterpretation or historical-date cleanup. companyos_dev is the approved isolated development target; creation requires separate execution approval. companyos_test remains proposed. Neither a Numeric change nor stamping establishes old data provenance. The selected implementation path is A; path B is retained as an unapproved historical contingency and must not be scheduled against company_db.

## Proposed logical revision order

Labels below identify the design stages; exact authored revision IDs are recorded in the S1-04 section. No database execution has occurred.

| Revision | Intended content | Gate |
|---|---|---|
| B0 exported baseline | Create the four exported table definitions with existing names, types, defaults, constraints, and indexes | Review exact baseline against authoritative export; test in isolated MySQL |
| T1 salary precision | employees.salary DECIMAL(10,0) → DECIMAL(12,2), preserving NOT NULL, no default, and nonnegative CHECK | D02 approved; separate execution authorization required |
| T2 hire-date default | Remove current-date expression default, keep nullable DATE and all existing values | D05 approved; separate execution authorization required |

B0 creation order: departments, projects, employees, employee_projects. Departments precede employees; both employee/project parents precede assignments. Keep FK enforcement enabled and avoid recreating the dump's out-of-order dependency handling. No fixture data belongs in the baseline migration. Exported AUTO_INCREMENT counters are not copied as schema requirements into a fresh empty database.

T1 and T2 are independently reviewable changes, applied in the recorded chain only after approval. Alembic version metadata is infrastructure state, not a speculative business table. Do not stamp a later head containing unapplied changes.

## Shared preflight, backup, and comparison gates

Future authorized operator must:

1. Confirm exact environment/host/database identity, approved access scope, MySQL version, engine, SQL mode, charset/collation, privileges, and the chosen SQLAlchemy/Alembic versions. Never infer environment from a local filename.
2. Compare actual current definitions with the baseline: every column's type/scale/signedness/order/nullability/default expression/AUTO_INCREMENT property; PK order; unique/index names and column order; FK targets/actions; CHECK names, expressions, enforcement; and table options. Investigate extra/missing objects and any existing alembic_version history. A database already managed by another migration lineage needs reconciliation, not an overwrite.
3. Treat equivalent spellings carefully: curdate() versus current_date(), omitted restrictive action versus RESTRICT, redundant expression parentheses, and nullable implicit NULL defaults may render differently. Normalize semantics without hiding real differences. Record dynamic AUTO_INCREMENT counters as instance state, separate from schema comparison.
4. Create a recoverable backup of schema **and data**, including any additional objects found. A schema-only export cannot recover records. Record capture time, source identity, version, integrity checks, secure storage/access, and applicable binary-log recovery position if available. Do not place real backups in source control.
5. Restore into an isolated environment and verify row counts, IDs, field values, assignment pairs, constraints, and a usable recovery procedure. A backup file's existence alone is not proof of recovery.
6. Rehearse baseline/adoption and each approved delta on an isolated copy. Measure lock/rebuild duration, disk needs, and application compatibility rather than promising an online/no-lock change. Plan a maintenance window or controlled write pause and final consistent backup/comparison before execution.
7. Approve the precise revisions, rollback/recovery plan, data-use boundary, and operator authorization. Current documentation approval does not authorize these operations.

Data-quality checks are read-only in the future rehearsal: blanks, unexpected status spellings, duplicate/nonconforming email, nulls, negative monetary values, orphan links, and duplicate assignment pairs. Existing constraints suggest intended protection but do not substitute for checking a real restored dataset. Report discrepancies; never auto-fix them to make a migration pass.

## A. Fresh empty MySQL database

1. Provision an explicitly empty isolated database with agreed MySQL 8 settings, application/migration credentials separated, and no unrelated objects.
2. Apply the reviewed B0 baseline through Alembic so the initial revision builds all business tables. Do not merely stamp an empty database; stamping does not create its business schema.
3. Compare B0 output with the exported schema semantically, excluding instance-specific counters. Verify exact keys/defaults/checks and a fresh database's reproducibility.
4. Apply only approved T1/T2 revisions. Verify target definitions and expected null/default behavior.
5. Test on synthetic data: generated IDs; optional email/department/hire date; status default; decimal boundaries; duplicate email/name/pair rejection; required parent references; restrictive parent deletes; rollback of failed application mutations.
6. If this becomes the approved MVP dataset, new salary entries carry explicit USD/monthly context. Do not copy legacy training records as USD fixtures or seed data. New approved MVP budgets use USD; do not relabel training budgets.

Application startup must not create or mutate production tables outside migration control. Fresh and adopted environments should converge on the same reviewed target schema, not necessarily identical data or ID counters.

## B. Existing populated database — historical contingency, NOT the selected company_db plan

The following earlier adoption specification is retained for traceability only. The current owner decision prohibits its execution on company_db. Any future reversal would require an explicit new owner decision plus all operational approvals; no task in the implementation backlog adopts or stamps company_db.

1. Do all shared gates first, including full backup/restore rehearsal, current-schema comparison, extra-object discovery, and a documented data-preservation manifest. Include IDs, values, assignment key sets, and AUTO_INCREMENT state; comparisons must not expose sensitive values in routine logs.
2. If actual schema differs from B0, stop baseline adoption. Document drift and devise a reviewed reconciliation revision or baseline strategy that represents reality. Do not execute B0 creation, run the dump, reset tables, or silently stamp a nonmatching database. If some target changes already exist, review that state explicitly rather than blindly skipping errors.
3. Once matching B0 is established and authorized, record **that exact baseline revision** using Alembic stamping. This adds/updates version metadata; it is a database write. It must not alter business rows or recreate tables. Stamping records a revision without running its migration operations. [Alembic stamp documentation](https://alembic.sqlalchemy.org/en/latest/api/commands.html#alembic.command.stamp)
4. Recompare business structure and the preservation manifest after stamping. Only migration metadata should differ.
5. Apply approved T1, then approved T2, with a stable write boundary. T1 changes storage precision, preserving numeric value; it does not convert salary units. T2 leaves existing hire dates unchanged. Preserve IDs, assignments, parent records, index/constraint definitions, and monotonic ID generation state.
6. Compare each stage before proceeding. Do not run destructive verification inserts/deletes on the preserved database; behavioral tests belong in isolated restored copies.
7. Keep training data explicitly identified as unverified monetary data; the current confirmed D20 boundary preserves company_db unchanged. Successful migration is not permission to label its salaries USD/monthly or publish them.

## Verification and acceptance evidence

| Area | Evidence required later |
|---|---|
| Schema | Baseline-to-target comparison shows only approved salary type/hire-date default changes; no dropped constraints/indexes, altered nullability, or extra business tables |
| Data | Same row counts, IDs, assignment pairs, and non-target values; salary numeric equality across precision change; existing hire_date equality including NULL; generated ID state not reset |
| Integrity | In isolated tests: duplicate pair rejected, duplicate non-NULL email/name rejected, multiple NULL emails accepted, invalid FK rejected, negative amounts/status rejected, referenced parent deletion blocked |
| Defaults | New status defaults Active; target omitted/explicit-null hire date is NULL through SQLAlchemy/Pydantic path; no client-side today substitution |
| Money | Fractional salary accepted only after T1; overflow/excess precision rejected by application; no USD metadata assigned to legacy rows; no conversion arithmetic |
| Alembic | Expected lineage and exact revision recorded; fresh creation and populated adoption rehearsed separately; no unexplained drift |
| Application | Relevant S2–S7 slice contracts compatible with actual schema; real authentication and sensitive-field checks verified before public release |
| Recovery | Restored copy validates expected schema/data and usable application state; recovery time and acceptable loss boundary recorded |

Autogeneration produces candidates, not an authority. Manually review precision, defaults, CHECK expressions, constraint names, FK actions, and indexes. Column renames can appear as destructive add/drop operations; CHECK comparison has limitations. An empty generated diff does not prove complete equivalence. [Alembic autogeneration guidance](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)

## Failure and recovery considerations

MySQL DDL can cause implicit commits. Do not assume wrapping a multi-revision migration in a transaction makes all schema changes reversible. [MySQL implicit-commit documentation](https://dev.mysql.com/doc/refman/8.0/en/implicit-commit.html)

- Stop application writes on unexpected state. Capture the actual completed schema and version metadata before deciding recovery; DDL may have succeeded before revision bookkeeping failed. Never blindly retry or stamp success to hide a failure.
- Prefer a reviewed forward repair when it preserves verified data. Otherwise restore a tested backup to an isolated/replacement database, verify it, then perform a controlled cutover. Plan how writes after the backup would be recovered; restoring an older snapshot without accounting for them loses data.
- T1 downgrade to DECIMAL(10,0) becomes lossy after fractional values are stored. Refuse automatic rounding/truncation. Only a separately approved, verified no-fraction case or an appropriate recovery plan can justify reversal.
- T2 reversal restores a default for future inserts only. It does not identify or repair historical rows, and must not backfill NULL dates.
- Never downgrade B0 on the populated database: dropping baseline tables destroys data. Baseline teardown is only a possible isolated disposable-environment operation, not a recovery strategy for company_db.
- Test ORM parent-deletion behavior for loaded/unloaded collections; accidental ORM FK nulling/deletion must not defeat the restrictive design.

## Remaining approvals and recommendations

Execution blockers: actual schema equivalence, tested recovery, and explicit migration authorization. Data boundary: D20 no-import/no-conversion/no-relabeling is confirmed and must be enforced. API policy blockers: lifecycle/assignment rules and D09/D18 role/field contracts. Public-release blockers: concrete identity/session and hosting choices and production security gates.

Confirmed direction: preserve training company_db unchanged and use isolated companyos_dev after separate provisioning authorization. companyos_test needs explicit target approval. Both adoption paths are retained for traceability, but only the fresh-database path is in the backlog. No new business tables/indexes, conversion system, or executable migration is proposed beyond the reviewed two-column delta.

See [implementation-backlog.md](implementation-backlog.md) for ordered tasks; each later implementation/execution gate still requires owner approval.

## S1-03 offline B0 implementation evidence

[b0_company_schema.py](../apps/api/alembic/versions/b0_company_schema.py) is manually authored with revision b0_company_schema, down_revision=None and no branch/dependency. It is independent of application models. Creation order is departments → projects → employees → employee_projects; named supporting indexes are created before adding foreign keys. Reverse-order teardown is authored but not invoked and must never be used as populated-database recovery.

B0 preserves DECIMAL(10,0), (curdate()), all existing constraint/index names and table engine/charset/collation. It has no training rows, conversion, target T1/T2 changes or dump AUTO_INCREMENT counters. [env.py](../apps/api/alembic/env.py) explicitly rejects online execution; it contains no engine or connection configuration. Enabling an online path later requires a separately reviewed change and execution authorization.

Actual verification: 14 targeted offline tests pass; complete backend suite 159 passed, 0 failed, 1 existing warning. Alembic history reports the sole B0 root/head. Tests render revision operations into an in-memory buffer and compare definitions against the original export; no SQL is executed against a database and no CLI upgrade/downgrade/stamp, reflection or autogenerate runs. Schema acceptance by a real MySQL server, data preservation and recovery remain unverified until approved isolated rehearsals. Neither company_db nor companyos_dev was accessed; companyos_test remains proposed. Dependency isolation/locking remains a separate follow-up.

## S1-04 target sources — not applied

Chain: b0_company_schema → t1_salary_precision → t2_hire_date_default (sole head). [T1](../apps/api/alembic/versions/t1_salary_precision.py) alters only salary precision/scale, retaining NOT NULL and CHECK. [T2](../apps/api/alembic/versions/t2_hire_date_default.py) removes only the hire_date server default, retaining DATE NULL. Neither source imports runtime models or modifies rows. B0 remains immutable.

T1 downgrade raises before emitting any operation to prevent fractional loss. There is no override: even a verified integral dataset requires separately reviewed recovery code and authorization. T2 reverse source restores (curdate()) for future inserts only, never stored dates. No downgrade CLI was run. Online env.py remains disabled; future provisioning must select and apply the reviewed chain before using target models. company_db remains excluded.

S1-04 verification: targeted 26 passed; full suite 171 passed, 0 failed, 1 existing Starlette/httpx warning. History confirms the three-revision chain. SQL was rendered in memory only; live enforcement, preservation and recovery remain unverified.
