# CompanyOS requirements

Status: Draft for review. Prepared 2026-10-11. Documentation only; no implementation or migration is authorized by this document.

## Evidence and decision status

- **Verified export fact:** [company_schema.sql](../database/company_schema.sql) defines the exported state of `company_db`; its header reports MySQL 8.0.34. It is not proof of the current live database state.
- **Historical evidence only:** [03_queries.sql](../database/legacy-sql/03_queries.sql) contains exercises, DDL, mutations, and transaction examples. Successful execution is not established. It is not a migration or seed baseline.
- **Review inputs:** the four MVP modules, technology stack, exclusions, and security boundaries below come from the architectural review. They are target requirements, not a record of final owner approval.
- **Owner-confirmed:** All new approved MVP monetary values are USD: salaries are monthly USD and project budgets are USD (expanded confirmation 2026-10-12). Existing training-record currency/period is unverified and must not be relabeled or converted. This does not approve unrelated policy decisions.
- **Proposed:** D02 precision and unrelated policy decisions remain pending in [open-decisions.md](open-decisions.md), including companyos_test (D21); D20 training isolation and all new MVP money semantics are confirmed. USD approval does not approve schema execution.
- **Owner-confirmed environment:** preserve company_db unchanged; use isolated companyos_dev, whose creation requires separate implementation approval. No training-record import, conversion or relabeling. companyos_test remains proposed.
- **Owner-required transparency:** before each implementation task explain the objective, files, commands and expected results in Arabic; afterward report actual commands, results and issues. Review each small step and await approval before the next major task. See [AGENTS.md](../AGENTS.md).
- **Authorized work:** documentation refinement only. The four existing drafts were reviewed; no database connection or SQL execution was used. Verified facts and authorization to edit documentation must not be confused with approval to implement target policies.

## Project overview and business problem

CompanyOS is a single-company management MVP and Systems Programmer portfolio project. It provides a consistent interface for employee, department, project, and project-membership records. It replaces ad hoc SQL interactions with validated workflows, controlled access, and reliable operational counts. It does not process payroll or attempt to implement a complete HR platform.

The intended architecture is a monorepo containing a Next.js App Router frontend using TypeScript, Tailwind CSS, and shadcn/ui; a Python backend using FastAPI, Pydantic, SQLAlchemy, and Alembic; and MySQL 8. Deployment targets are Vercel for the frontend, a separately hosted FastAPI backend, and managed MySQL. These are specified technologies, not existing implementations.

## Target users

- Company administrators maintain employee, department, and project records.
- Operational viewers inspect directory information, assignments, and aggregate counts.
- Administrators also manage salary and employee email; no separate compensation role is proposed.
- The developer/reviewer runs a local demonstration and assesses architecture, validation, tests, and documentation.

These are personas. They do not imply that application accounts, authentication, or permission tables already exist. A minimal proposed role model is documented under D09.

## Functional requirements

| ID | Requirement | Acceptance reference |
|---|---|---|
| FR-E01 | Create employees with validated identity, salary, status, and optional fields subject to approved rules. | US-E01 |
| FR-E02 | List employees with bounded pagination, search, filters, and deterministic sorting. | US-E02 |
| FR-E03 | View employee details and update information without losing omitted fields. | US-E03 |
| FR-E04 | Deactivate employees instead of exposing physical deletion; retain their records. | US-E04 |
| FR-E05 | Assign, change, or clear a department subject to approved optionality. | US-E05 |
| FR-E06 | Enforce backend authorization; propose omitting salary, employee email, and hire_date from Viewer responses, including nested representations. | US-S01 |
| FR-D01 | Create, list, and rename departments with employee counts. | US-D01, US-D02 |
| FR-D02 | Prevent deletion of a department referenced by employees. The proposed MVP exposes no department deletion endpoint (D07 pending). | US-D03 |
| FR-P01 | Create, list, view, and update projects. | US-P01 |
| FR-P02 | Assign employees to projects with one role per pair; prevent duplicate assignments. | US-P02 |
| FR-P03 | Remove assignments without deleting their employee or project. Role editing is proposed within assignment management. | US-P03 |
| FR-H01 | Show total employees, active employees, department/project counts, employees per department, and project membership statistics. | US-H01 |

Detailed acceptance and failure scenarios are in [user-stories.md](user-stories.md).

## Business rules

### Verified schema baseline

- Four tables exist in the export: `departments`, `employees`, `projects`, and `employee_projects`. All use InnoDB, `utf8mb4`, and `utf8mb4_0900_ai_ci`.
- Departments have generated integer IDs and required, unique names of at most 100 characters.
- Employees have generated integer IDs, required names up to 100 characters, and required nonnegative `DECIMAL(10,0)` salaries.
- Employee department IDs are nullable foreign keys. Email is nullable `VARCHAR(150)` with a unique index.
- The actual status column is `employee_status`, a required `VARCHAR(20)` with default `Active`. `chk_employment_status` references this column and lists `Active`, `Inactive`, and `On Leave`; no `employment_status` column is defined.
- `hire_date` is nullable DATE with an expression default of `curdate()`.
- Projects have generated integer IDs, required unique names up to 150 characters, required start dates, and nullable nonnegative `DECIMAL(12,2)` budgets.
- Assignments have required employee/project foreign keys, required `VARCHAR(50)` role, and composite primary key `(employee_id, project_id)`.
- Foreign keys declare no cascades; the existing restrictive behavior is the baseline. All FK columns have supporting indexes, including the composite key's employee prefix.
- String uniqueness follows the exported collation. API validation must not assume case-sensitive uniqueness.

### Proposed application policies — approval pending

- D01: retain `employee_status` across database and API naming.
- D02: USD is the approved salary currency and monthly is the confirmed design assumption for new approved MVP data. Salary type `DECIMAL(12,2)` remains proposed. Configure the semantics explicitly; no conversion, payroll, legacy relabeling, or currency guessed from locale. Project budgets are owner-confirmed USD under D20; legacy amounts remain unverified.
- D03/D04: email and department remain optional. Blank optional email input becomes NULL; nonblank email must be valid and unique. Multiple missing emails are allowed.
- D05: omitted/unknown hire date means NULL in the future design; remove the automatic current-date default without rewriting historical dates.
- D06: deactivation sets `Inactive`, preserves assignments, and changes active counts. Block new assignments for inactive employees; preserve historical memberships. Reactivation may use the ordinary status-edit workflow.
- D07: retain restrictive FK behavior and no physical employee deletion; propose no parent deletion endpoints in MVP, including empty departments; D07 remains pending.
- D08: preserve globally unique department/project names and one role per assignment; role remains bounded, nonblank free text.
- D10: counts include all retained employees and assignments unless explicitly labeled Active. Employees with no department appear as an Unassigned group. Zero-member departments/projects remain visible.
- D11: preserve all records; no cleanup, inferred backfill, or legacy-script replay is authorized.
- D08/D11: preserve the assignment composite primary key. No speculative tables or indexes are part of the target design. A concrete new persistence need requires a separate reviewed decision.
- Trim boundary whitespace for names and roles and reject blank values. Allow duplicate employee names. Accept zero salary/budget. Reject negative, excessive-precision, or out-of-range amounts rather than silently rounding.
- Partial updates leave omitted fields unchanged; explicit NULL is accepted only for optional fields. Treat status as one of the canonical application spellings.
- Project start date is required; a future start date is allowed. Date-only inputs do not acquire a timezone. Further employment chronology rules are not assumed.

Until the D02 precision change is approved and its migration applied, the exported salary type cannot represent fractional amounts. USD/monthly approval alone changes no database values or storage type. Requirements for two decimal places must not be presented as existing database behavior.

## Security requirements

These are proposed mandatory release gates implementing the brief's requirement for authenticated, authorized production access; authentication is not implemented in this phase.

- SEC-01: Require authenticated identities for every deployed business-data endpoint; no anonymous directory, salary, or dashboard access. Use a maintained identity/session solution and enforce session/token verification in the backend.
- SEC-02: Exactly two proposed application roles: Administrator manages employees, salaries, departments, projects, and assignments; Viewer reads approved nonsensitive information only and cannot mutate records. No compensation-specific role, advanced permission editor, or employee self-service is in scope. See D09.
- SEC-03: Proposed Viewer responses omit salary, employee email, and hire_date entirely, including employee lists/details and nested project memberships. Project budget is proposed Administrator-only under D18, pending explicit approval. Reject Viewer mutations as a whole. Prevent sensitive-field disclosure through search matches, counts, sorting/filtering, validation errors, logs, analytics, or shared caches. Viewer search must never match hidden email. A frontend hidden field is insufficient.
- SEC-04: Account identity is separate from `employees.employee_status`; inactive employment must not silently be treated as revoked application access. Define independent account revocation, logout, and session expiration.
- SEC-05: Require HTTPS, explicit frontend origins, server-side input validation, bound database parameters, secret storage outside source/client bundles, and least-privilege application DB access. The browser must never connect directly to MySQL. Migration credentials are separated from application credentials.
- SEC-06: Select cross-origin session/cookie/token behavior before deployment. If using cookies, explicitly design CSRF defenses and cookie attributes; CORS is not authorization. Prevent sensitive response caching across identities.
- SEC-07: Use sanitized errors and operational logs, access-control integration tests, bounded requests, and basic abuse protection. Never log passwords, tokens, full salary payloads, or production data in demo telemetry.
- SEC-08: Public portfolio demos must use synthetic data and still satisfy the deployed authorization gates. Real employee information must not be published as demonstration content.
- SEC-09: Audit-trail implementation remains excluded unless an actual organizational requirement is identified and approved as a scope change (D15). Do not represent ordinary logs as a compliant audit trail.
- SEC-10: Local slices may use synthetic data and an explicitly development-only identity stub supplying Administrator/Viewer identities to real permission checks. Keep them loopback-only. Public deployments, including previews, require real authentication on all backend business endpoints. Production must fail closed if authentication is missing or a development stub is enabled; no production bypass is permitted.

## Non-functional requirements

- NFR-01 Maintainability: separate HTTP validation, business operations, and persistence concerns; typed frontend contracts and explicit error handling; documented setup and module boundaries.
- NFR-02 Integrity: one business mutation succeeds or fails atomically. FK/unique/check conflicts return actionable errors without exposing raw SQL. Concurrent duplicate assignment/name/email attempts cannot bypass database constraints.
- NFR-03 Usability: responsive layouts, labeled forms, keyboard operation, visible focus, and loading/empty/error/success states. Errors preserve user input where safe.
- NFR-04 Query behavior: proposed page size 20, allowed 1–100; stable ID tie-breaker for sorts. Employee search uses name for Viewer and name/email for Administrator; filters use status/department and sorts use name/ID for Viewer, with hire date restricted to Administrator under pending D18; Viewer hire-date sort is rejected before querying. No salary or budget query features in the MVP. See D12.
- NFR-05 Performance: bounded queries and no per-row department/membership query pattern. Measure representative lists/dashboard later and document fixture size and environment. A numeric target remains unresolved under D16; no invented load target or benchmark subsystem is required for the MVP.
- NFR-06 Verification: meaningful integration tests cover constraints, pagination, state transitions, aggregated counts, and permissions; production authorization must be tested against direct API calls.
- NFR-07 Operations: separate development/test/production configuration, pinned dependencies, recoverable backups, restore rehearsal, migration rehearsal, basic health monitoring, and a release procedure before production deployment.

## Vertical slice development — proposed D19

After requirements and Database Design/ERD review, build a small backend foundation, then deliver the employee read API and connected Next.js listing before employee mutations. Continue with departments, projects/assignments, and dashboard as complete API-to-UI slices. Integrate real production identity and complete authorization verification before deployment. Tests and role-aware response contracts start in each slice, not at the final testing stage. See the S1–S9 sequence in [mvp-scope.md](mvp-scope.md).

## Requirements traceability

All migration entries below are possibilities for later approval, not authorized work.

| Feature / requirement | Existing tables and evidence | Gap or application responsibility | Possible future migration |
|---|---|---|---|
| Employee create/detail/update — E01/E03 | employees; PK, name, salary, email, status, hire date | Validation and authorized API/UI | D02 salary precision; D05 hire-date default |
| Employee list/search — E02 | employees; email unique index, department index | Pagination, query allowlist, stable sorting | Only measured query indexes; none assumed necessary |
| Department assignment — E05 | employees.department_id → departments | Optionality and invalid-parent handling | None if nullable relation retained |
| Deactivation — E04 | employees.employee_status and CHECK | Transition policy, preserved memberships | None for current three-state model |
| Sensitive-field protection — FR-E06 / US-S01 | employees.salary, employees.email, employees.hire_date; projects.budget under D18 | Role-aware backend responses and queries | None required for field omission; identity architecture remains unresolved |
| Department management — D01/D02 | departments; unique name; employee FK | Nonblank validation, safe deletion policy | Optional nonblank checks after data review |
| Project management — P01 | projects; unique name, start_date, budget CHECK | Form validation and details | Optional nonblank check; no new project fields required |
| Assignment management — P02/P03 | employee_projects; composite PK, two FKs, role | Existing-parent/status validation and role editing | None if one free-text role per pair retained |
| Dashboard — H01 | all four tables | Defined aggregation semantics, zero groups, no salary aggregates | No summary tables needed for MVP |
| Authentication/authorization — SEC-01–04/10 / US-S01 | No accounts, credentials, or application-role tables exported | D09 provider choice and backend enforcement | No new tables proposed; concrete provider requirements need separate review |
| Existing DB adoption — NFR-02/07 | authoritative export and named constraints | Reconcile live state later, preserve records | Reproducible baseline plus Alembic version metadata; later approved deltas |

## Assumptions and limitations

Single-company operation is specified. USD salary currency is approved and monthly is the agreed assumption for new approved data. Training monetary provenance remains unverified; new approved MVP salaries and project budgets are USD; user permissions, exact search behavior, and performance targets remain proposed. No production users, compliance obligations, volumes, hosting provider beyond frontend Vercel, or identity provider have been confirmed. Existing rows and current schema drift have not been inspected. The export contains destructive reconstruction statements and must not be treated as an executable adoption plan. Practice SQL includes fixed-ID updates/deletion and a non-idempotent insert; it must remain historical evidence.

See [database-design.md](database-design.md), [erd.md](erd.md), and [database-migration-plan.md](database-migration-plan.md) for the Phase 0 design. Only documentation is authorized at this stage.

See [mvp-scope.md](mvp-scope.md) for milestones and release gates, [user-stories.md](user-stories.md) for scenarios, and [open-decisions.md](open-decisions.md) for approvals.
