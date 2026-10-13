# CompanyOS database design specification

Status: Phase 0 review draft, 2026-10-11. Documentation only; no database access, SQL execution, model implementation, or migration generation.

## Authority and confirmed semantics

The complete [company_schema.sql](../database/company_schema.sql) is authoritative for its exported state. Its header reports MySQL 8.0.34, database company_db, dump completion 2026-10-11 18:51:17 (timezone unspecified). It does not prove the current live state. [Legacy practice SQL](../database/legacy-sql/03_queries.sql) is historical evidence, never a migration or proof of execution. Requirements, scope, stories, and [decisions](open-decisions.md) were reviewed together.

Owner confirmation on 2026-10-11: salary currency **USD** is approved; **monthly** is the current agreed design assumption for new approved MVP data. This confirms neither old training salaries' units nor their payment period. No conversion, automatic relabeling, or inference from record IDs is permitted. Project budgets for new approved MVP data are owner-confirmed USD; old training amounts remain unverified. Approval to write this specification is not approval to execute it.

## Current physical inventory

Four tables, 16 columns, four primary keys, three foreign keys, three additional unique indexes, two nonunique secondary indexes, and three CHECK constraints. All tables use InnoDB, utf8mb4, and utf8mb4_0900_ai_ci. All INT columns are signed. No generated columns are declared. Exported AUTO_INCREMENT table counters are departments=5, employees=8, projects=3; they are instance state, not row counts or proof of existing IDs.

No views, routines, triggers, events, or application identity tables are defined in this export; export options/completeness for such objects are unknown. It contains no data rows or database-creation definition. Its temporary session SET statements do not establish the original runtime SQL mode or database defaults.

### Complete current data dictionary

“None declared” means no explicit DEFAULT clause. Generated IDs are supplied by AUTO_INCREMENT, not a literal default. Target values are identical unless shown otherwise.

| Table.column | Current MySQL type | Nullable | Current default | Generated/key role | Proposed target difference |
|---|---|---|---|---|---|
| departments.department_id | INT | No | None declared | AUTO_INCREMENT; PK | None |
| departments.department_name | VARCHAR(100) | No | None declared | Unique department_name | None |
| employees.employee_id | INT | No | None declared | AUTO_INCREMENT; PK | None |
| employees.full_name | VARCHAR(100) | No | None declared | None | None |
| employees.salary | DECIMAL(10,0) | No | None declared | CHECK nonnegative | DECIMAL(12,2), still required, no default |
| employees.department_id | INT | Yes | NULL | FK; nonunique index | None |
| employees.email | VARCHAR(150) | Yes | NULL | Unique email | None |
| employees.employee_status | VARCHAR(20) | No | 'Active' | CHECK allowed values | None; keep canonical name |
| employees.hire_date | DATE | Yes | Expression (curdate()) | None | Remove expression default; omission becomes NULL |
| projects.project_id | INT | No | None declared | AUTO_INCREMENT; PK | None |
| projects.project_name | VARCHAR(150) | No | None declared | Unique project_name | None |
| projects.start_date | DATE | No | None declared | None | None |
| projects.budget | DECIMAL(12,2) | Yes | NULL | CHECK nonnegative | None |
| employee_projects.employee_id | INT | No | None declared | Composite PK position 1; FK; not AUTO_INCREMENT | None |
| employee_projects.project_id | INT | No | None declared | Composite PK position 2; FK; not AUTO_INCREMENT | None |
| employee_projects.role | VARCHAR(50) | No | None declared | None | None |

### Complete key and index inventory

All index names below are per-table. No other indexes are declared.

| Table | Index name | Ordered columns | Kind / purpose |
|---|---|---|---|
| departments | PRIMARY | department_id | PK, unique |
| departments | department_name | department_name | UNIQUE; department-name uniqueness |
| employees | PRIMARY | employee_id | PK, unique |
| employees | email | email | UNIQUE; nullable email |
| employees | department_id | department_id | Nonunique secondary; FK support |
| projects | PRIMARY | project_id | PK, unique |
| projects | project_name | project_name | UNIQUE; project-name uniqueness |
| employee_projects | PRIMARY | employee_id, project_id | Composite PK; duplicate-pair prevention; employee FK support |
| employee_projects | project_id | project_id | Nonunique secondary; project FK support |

No additional employee_id index on assignments is needed for FK coverage because employee_id leads the PK. No speculative salary, status, search, or dashboard indexes are proposed. Future measured queries may justify a separately reviewed change.

### Foreign keys and referential actions

| Child table | Constraint name | Child → parent | Nullable link | ON DELETE / ON UPDATE |
|---|---|---|---|---|
| employees | employees_ibfk_1 | department_id → departments.department_id | Yes | Omitted in export; effective restrictive behavior |
| employee_projects | employee_projects_ibfk_1 | employee_id → employees.employee_id | No | Omitted; restrictive |
| employee_projects | employee_projects_ibfk_2 | project_id → projects.project_id | No | Omitted; restrictive |

Referenced parents cannot be physically deleted or have referenced keys changed while children remain. A nullable department FK does not mean ON DELETE SET NULL. Retain current actions and names; no CASCADE migration is proposed. InnoDB treats NO ACTION as RESTRICT. [MySQL foreign-key documentation](https://dev.mysql.com/doc/refman/8.0/en/create-table-foreign-keys.html)

### CHECK constraints and unique semantics

| Table | CHECK name | Exported logical expression | Consequence |
|---|---|---|---|
| employees | chk_salary_positive | salary >= 0 | Zero allowed despite “positive” name; salary is NOT NULL |
| employees | chk_employment_status | employee_status IN ('Active','Inactive','On Leave') | Column name remains employee_status; no employment_status column |
| projects | projects_chk_1 | budget >= 0 | Zero or NULL allowed; negative values prohibited |

The export renders status literals with utf8mb4 introducers and nested parentheses; those formatting details do not imply another column or status type. No NOT ENFORCED clause is present. CHECK accepts TRUE or UNKNOWN; nullability is separately enforced. [MySQL CHECK documentation](https://dev.mysql.com/doc/refman/8.0/en/create-table-check-constraints.html)

Nullable UNIQUE email permits multiple NULL entries; optional does not mean duplicate non-NULL values. Name/email comparisons inherit case/accent-insensitive collation; status comparison is not exact-case validation. NOT NULL does not prohibit whitespace-only strings. Email syntax and role vocabulary are not validated by the database. [MySQL unique-index semantics](https://dev.mysql.com/doc/refman/8.0/en/create-index.html), [collation naming](https://dev.mysql.com/doc/refman/8.0/en/charset-collation-names.html)

## Proposed physical delta and preserved structure

| Change | Reason | Data effect intended | Approval |
|---|---|---|---|
| employees.salary DECIMAL(10,0) → DECIMAL(12,2) | Two fractional digits while preserving ten integer digits | Same numeric values, represented with two decimal places; no multiplication, division, conversion, or currency labeling | D02 precision pending |
| Remove employees.hire_date current-date default | Unknown hire dates should remain unknown | Existing dates unchanged; future omitted dates become NULL | D05 pending |

Current checked salary range is 0–9,999,999,999; target is 0–9,999,999,999.99. Budget retains its existing nonnegative DECIMAL(12,2) range and nullable state. No rounding policy is implied: proposed input validation rejects excess fractional precision.

Preserve every existing table/column name other than the two definition changes above, all IDs, the assignment composite PK, nullability, Active status default, checks, indexes, charset/collation, foreign keys, and rows. No current employee, department, project, or assignment is changed by this documentation task. Future approved operational edits/removal of an assignment are distinct from preserving records during schema adoption; no migration performs those business operations.

Current and target diagrams are separate in [erd.md](erd.md). Status retention, FK retention, and composite-key retention are design constraints of this task; they do not close unrelated decisions in the wider register.

## Relationships and normalization through 3NF

| Relation | Functional dependencies used for analysis | Normalization assessment |
|---|---|---|
| departments | department_id determines department_name; required unique name is an alternate key | Atomic attributes, no composite-key partial dependency, no non-key transitive dependency |
| employees | employee_id determines name, salary, department_id, email, status, hire_date | Department name is stored in departments, not repeated here; no identified non-key-to-non-key dependency within employees |
| projects | project_id determines name, start_date, budget; required unique name is an alternate key | No repeated groups or identified partial/transitive dependency |
| employee_projects | (employee_id, project_id) determines role | Role belongs to the whole pair; neither employee nor project alone determines it. Names and other parent attributes are not duplicated |

1NF: columns hold scalar values and project membership is represented as rows, not lists in employees. 2NF: single-column parent PKs have no partial-key dependency; assignment role depends on both IDs. 3NF: no identified non-key determinant of another non-key attribute within any relation under the stated business model. Nullable email uniqueness is not an unconditional relational candidate key for every row. A free-text role does not itself require a lookup table. This is a design assessment under the documented dependencies, not a data audit or proof that unknown business rules introduce no further dependencies.

Department membership is optional, project assignment parents are mandatory, and parent participation can be zero. There is no project ownership-by-department relationship in evidence. Counts are derived, not duplicated in summary tables.

## Validation specification and status

Existing constraints are verified facts; API rules below are proposed acceptance behavior unless specifically marked confirmed. Traceability uses the requirements and user-story IDs already defined.

| Area | Required validation / behavior | Basis and traceability |
|---|---|---|
| IDs | Server generates parent IDs; assignment requires both existing parent IDs; no client key rewrites | PK/FK facts; FR-E01, FR-P02; US-E01/P02 |
| Names/role | Required, trim boundaries, reject blank; lengths 100 employee/department, 150 project, 50 role; employee names may repeat | Length/nullability facts; nonblank policy proposed D08; US-E01/D01/P01/P02 |
| Salary | Required finite exact decimal, >=0, within storage range; reject >2 decimals only after target migration, >0 fractional digits before it; no silent rounding | CHECK/type facts; precision proposed D02; US-E01/E03 |
| Salary meaning | USD per month for new approved MVP data only; never automatically reinterpret legacy values | Owner-confirmed D02/D20; enforce no-import boundary |
| Email | Optional; blank → NULL, validate syntax if supplied; <=150; unique under DB collation; race-safe conflict handling | UNIQUE fact; input rules proposed D03; US-E01/E03 |
| Department | Optional; NULL clears; non-NULL must reference an existing department | FK fact; D04; US-E05 |
| Status | Canonical Active/Inactive/On Leave application values; missing create status Active; proposed deactivate/reactivate rules; no hard delete | Existing default/CHECK; proposed D06/D07; US-E04 |
| Hire date | Optional valid date-only value; target omission/explicit NULL means unknown; no today substitution; partial omission leaves existing value | Proposed D05; US-E01/E03 |
| Project | Required valid start date, future allowed; optional finite budget >=0 and <=9,999,999,999.99, max two fractional digits; currency USD for new approved MVP data, never inferred for training rows | Schema facts; proposed application rules; D20; US-P01 |
| Uniqueness | Department/project names unique; assignment pair unique; concurrent duplicates rejected, never silently overwrite role | Existing keys; D08; US-D01/P01/P02 |
| Assignment eligibility | Proposed: block new Inactive assignments; allow Active/On Leave; preserve existing memberships on deactivation; allow explicit role edit/removal | D06 pending; US-P02/P03 |
| Mutations | Validate complete operation before commit; omitted update fields unchanged, explicit NULL only where allowed; reject unknown writable fields | D13 proposed; US-E03/P01/P03 |
| Queries/dashboard | Bounded pagination, allowlisted sorting, no duplicate count inflation, zero groups/unassigned visible; counts/status semantics per D10 | D10/D12 pending; US-E02/D02/H01 |
| Authorization | Proposed Administrator/Viewer; omit salary/email/hire_date for Viewer in all representations; Administrator-only budget preferred; no hidden-email search inference | D09/D18 pending; FR-E06, US-S01 |
| Public release | Real backend authentication, no production stub/bypass; local synthetic identity only; sanitize errors/logs | User security boundary; SEC-01–10, US-S01 |

An application precheck does not replace a constraint. Later tests must include concurrent duplicates and assignment/deactivation races; if inactive assignment prohibition is approved, serialize the status check and assignment mutation against employee status changes rather than trusting an earlier UI read. Do not silently clean old whitespace, email, status casing, or dates to make them fit new application rules.

## SQLAlchemy 2.x mapping specification — no implementation

Use typed declarative mappings with explicit nullability and one metadata collection. Map baseline first; apply approved target type/default changes only with the corresponding migration. ORM classes are persistence models, not public response schemas.

| Proposed class / table | Attribute mapping |
|---|---|
| Department / departments | department_id: integer generated PK; department_name: required string length 100 with named unique key |
| Employee / employees | employee_id: integer generated PK; full_name: required string(100); salary: Decimal through Numeric(10,0) baseline / Numeric(12,2) target; department_id: optional integer FK; email: optional string(150); employee_status: required string(20); hire_date: optional Python date |
| Project / projects | project_id: integer generated PK; project_name: required string(150); start_date: required Python date; budget: optional Decimal through Numeric(12,2) |
| EmployeeProject / employee_projects | employee_id and project_id: required integer FKs, both PK=True in existing order, no autoincrement; role: required string(50) |

Specify all existing FK/CHECK/index names from the inventory. Represent uniqueness once, not both an extra unique constraint and a duplicate index. Preserve table engine/charset/collation. Keep employee_status as a string with its existing CHECK, not a new native ENUM. Preserve Active as a server default. Baseline hire_date maps the server expression; target removes it and adds no Python date default. Explicit NULL versus omission must be tested because defaults can be applied when values are omitted by ORM persistence. Preserve constraints when altering columns; do not rename them merely to fit a new naming convention.

Relationships: Department.employees ↔ Employee.department (optional scalar); Employee.assignments ↔ EmployeeProject.employee (required scalar); Project.assignments ↔ EmployeeProject.project (required scalar). Use explicit bidirectional mapping. EmployeeProject is an association object because it carries role; avoid a second independently writable many-to-many relationship over the same table. [SQLAlchemy association-object mapping](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#association-object)

No ORM delete or delete-orphan cascade from parents. Parent deletion must not silently NULL department IDs or delete assignments before the FK sees it. Specify passive database enforcement for parent-delete paths (including the SQLAlchemy passive_deletes="all" behavior where needed), and verify loaded/unloaded relationship cases later. Assignment removal should be an explicit operation on that association, not an incidental collection mutation. No parent hard-delete business API is proposed. [SQLAlchemy cascade behavior](https://docs.sqlalchemy.org/en/20/orm/cascades.html)

FastAPI/Pydantic requests and responses use separate allowlists for roles. Decimal stays exact through validation/storage; a proposed API contract uses decimal strings for monetary JSON values to avoid frontend floating-point assumptions. Do not expose whole ORM objects or unverified legacy currency metadata. SQLAlchemy runtime type/default choices do not grant authorization or change currency semantics.

## Owner blockers versus recommendations

**Blockers before the relevant action:** review target precision/default changes (D02 precision, D05); enforce confirmed D20 training isolation; obtain companyos_test approval (D21); approve operational policies and Viewer allowlist (D06–D10/D18) before API contract sign-off; choose identity/session and hosting before public implementation/deployment (D09/D17). Current database equivalence, backup validity, and execution authorization are mandatory operational gates, not facts established by this document.

**Confirmed environment boundary:** preserve company_db; companyos_dev is the approved isolated target, with provisioning separately gated. companyos_test remains proposed. **Recommendations, not additional scope:** use exact Decimal types; retain existing constraint names; defer all new indexes/tables; validate nonblank input in the application first. No audit/history or currency-conversion subsystem is proposed. Mixing/importing training records is outside the confirmed scope; a global USD setting cannot establish row provenance.

Ready for review and subsequent API architecture planning, with unresolved decisions clearly bounded. No executable model or migration is included. See [migration plan](database-migration-plan.md) for fresh versus populated database adoption.
