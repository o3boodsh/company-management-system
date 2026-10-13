# CompanyOS implementation backlog

Status: Final Phase 0 planning for owner review, 2026-10-12. **No task below has been executed.** This is not blanket implementation approval.

## Authority, sequence and shared completion rules

Sources: [requirements](requirements.md), [stories](user-stories.md), [API contract](api-contract.md), [decision register](open-decisions.md), [migration plan](database-migration-plan.md), [workflow](development-workflow.md), and [agent rules](../AGENTS.md).

Owner-confirmed: new MVP money is USD; salaries monthly; budgets USD; company_db is preserved without modification; no training-record import/conversion/relabeling; companyos_dev is the isolated development target. Its creation remains separately authorized. companyos_test, D02 precision, D05 hire-date default, D09/D18 roles/projections and other proposed business policies remain pending.

There are **26 tasks**: S1 6, S2 2, S3 2, S4 3, S5 2, S6 3, S7 2, S8 3, S9 3. S1-04 is optional for the B0-only read slice and mandatory before target employee writes. Do not skip owner review between major tasks. The full first vertical slice is S1–S3; [S1-01 alone](phase-1-start.md) is the initial coding task and has no DB access.

Every task inherits this Definition of Done (DoD): owner-authorized scope completed; relevant acceptance criteria and tests actually demonstrated; requirements/contracts updated if necessary; no secrets or original SQL edits; Arabic report lists every changed file, exact executed commands, test results, failures and limitations; owner reviews before the next major task. A deferred or failed check is not a pass. Each task below adds its own completion evidence.

**All commands below are planned, not executed.** Paths are planned files, not claims that they exist. Backend commands use the approved root virtual environment interpreter with working directory apps/api; frontend commands use apps/web. Repository/Git commands run at root. The future package manifests must define the mentioned scripts before they can be run. No placeholder/provider command is to be executed literally. Before every task explain its goal, files, commands and expected result in Arabic, then obtain required approval. Installing dependencies, Git initialization, DB access/writes, seeds, migrations, destructive tests, deployment and remote operations have distinct gates; target approval is insufficient.

## S1 — Foundation, configuration and schema setup (6 tasks)

### S1-01 — Prerequisites and minimal liveness bootstrap

- **Goal:** Prove the local Python HTTP process works, without MySQL access (NFR-07).
- **Dependencies:** Owner approval of [phase-1-start.md](phase-1-start.md); inspect prerequisites before confirming versions.
- **Planned files:** apps/api/pyproject.toml, requirements.lock, requirements-dev.lock, app/main.py, app/system/router.py, tests/test_health_live.py; README instructions. Package initializers only where needed.
- **Implementation:** Check Python/Node/npm/Git/MySQL client versions; propose compatible pins. Git initialization is optional and separately approved. After bootstrap/install approval, implement only GET /api/v1/health/live with the documented envelope and no DB import/settings prerequisite.
- **Planned commands:** Version checks and gated venv/install/uvicorn commands are specified exactly in phase-1-start.md; git init -b main only if separately approved.
- **Verification commands:** python -m pytest tests/test_health_live.py; local Invoke-RestMethod checks for /api/v1/health/live and /openapi.json; browser /docs.
- **Acceptance:** 200 {"data":{"status":"ok"}}; no DB/provider connection; no business endpoints; unsupported liveness query yields sanitized 422.
- **Definition of Done:** Shared DoD plus recorded runtime/pin choices and actual liveness/OpenAPI evidence. No claim that MySQL server or full slice works.
- **DB impact / approval:** None. No connection, schema introspection, creation, migration or fixture. Stop for review before S1-02.

### S1-02 — Settings, session lifecycle and local identity boundary

- **Goal:** Establish testable infrastructure without connecting to a database (NFR-01/02, SEC-03/10).
- **Dependencies:** S1-01; approve proposed local stub, settings contract and role matrix for local tests (D09/D18/D21/D23).
- **Planned files:** apps/api/app/core/{config,identity,errors}.py, app/db/session.py; tests/test_config.py, test_identity.py, test_session_lifecycle.py; dependency locks.
- **Implementation:** Validated environment/name guards; reject company_db and unapproved test targets; loopback-only synthetic principal; role spoofing rejected. Lazy engine/session factory with request cleanup; no import/startup DB connection or create_all. Install reviewed SQLAlchemy/driver/settings dependencies only with approval. Safe errors/private cache policy.
- **Planned commands:** python -m pip install -r requirements-dev.lock after dependency approval.
- **Verification commands:** python -m pytest tests/test_config.py tests/test_identity.py tests/test_session_lifecycle.py (fakes, network denied).
- **Acceptance:** Invalid/public stub configurations fail closed; secrets absent from errors; no repository commits; session closure tested without DB.
- **Definition of Done:** Shared DoD plus unit evidence for guards and no network access; DB-backed behavior explicitly unverified.
- **DB impact / approval:** No DB access. Later connection requires distinct authorization.

### S1-03 — Reviewable B0 ORM and Alembic baseline

- **Goal:** Represent the exported baseline reproducibly (D01/D08/D11, NFR-02/07).
- **Dependencies:** S1-02; explicit authorization to install Alembic and generate migration files; approve retained schema/key policy. Read original SQL only.
- **Planned files:** apps/api/app/db/{base,models}.py, alembic.ini, alembic/env.py, alembic/versions/<reviewed-B0>.py, tests/test_metadata.py; dependency locks.
- **Implementation:** Four business tables, exact exported types/defaults/checks/names/collation; composite association with role. No delete cascades or new business tables/indexes. Reviewed B0 creates parents before dependents; exclude instance auto-increment counters. Offline generation only; no autogenerate connection.
- **Planned commands:** python -m alembic init alembic; python -m alembic revision -m "exported baseline" (only after file-generation approval; manually review contents).
- **Verification commands:** python -m pytest tests/test_metadata.py; python -m alembic history; manual complete export-to-metadata/revision comparison.
- **Acceptance:** All exported columns/constraints accounted for, no fixtures, startup DDL or executable legacy replay. Offline review does not claim MySQL equivalence tested.
- **Definition of Done:** Shared DoD plus owner-reviewed B0 artifact and pending DB rehearsal clearly identified.
- **DB impact / approval:** Files only; do not upgrade, stamp or connect in this task. Alembic version metadata later is infrastructure, not a fifth business entity.

### S1-04 — Separately reviewed target revisions T1/T2

- **Goal:** Prepare only approved salary/default deltas (FR-E01/E03, US-E01/E03).
- **Dependencies:** S1-03; explicit D02 DECIMAL(12,2) and D05 nullable/no-current-date-default approvals plus migration-file generation authorization. Otherwise leave task blocked.
- **Planned files:** apps/api/alembic/versions/<T1>.py, <T2>.py, app/db/models.py, tests/test_target_metadata.py; database design if decisions differ.
- **Implementation:** T1 widens salary precision; T2 removes hire-date default without rewriting dates. Preserve all other definitions. Document lossy downgrade risk; no automatic rounding or backfill. Metadata must match the deployed chosen revision.
- **Planned commands:** python -m alembic revision -m "salary precision"; python -m alembic revision -m "remove hire date default", only after approval.
- **Verification commands:** python -m pytest tests/test_target_metadata.py; python -m alembic history; manual delta review. Execution tests deferred to authorized isolated DB tasks.
- **Acceptance:** Only two approved changes; no legacy conversion; downgrade/recovery limitations recorded.
- **Definition of Done:** Shared DoD plus separate reviewed revisions; do not claim them applied.
- **DB impact / approval:** No DB access in this task. May be deferred for S2/S3 B0 reads; mandatory before target employee writes.

### S1-05 — Authorized development database and readiness

- **Goal:** Provision the approved isolated target and prove connectivity safely (NFR-07).
- **Dependencies:** S1-03, optional approved S1-04; separate approval for host access, database creation, credentials, exact revisions and commands. Resolve expected revision before execution.
- **Planned files:** apps/api/app/system/router.py, app/core/config.py, tests/test_health_ready.py; local ignored configuration; setup/recovery documentation.
- **Implementation:** Verify approved host/name before any access; provision empty companyos_dev via owner-reviewed administration method. Never connect to company_db. Apply B0 and only approved deltas; bounded authenticated readiness verifies connectivity/revision. Separate runtime/migration privileges.
- **Planned commands:** Provisioning command must be presented after approved method/host is known; no SQL supplied here. Then python -m alembic upgrade <approved-revision>; python -m alembic current (placeholders resolved and approved before use).
- **Verification commands:** python -m pytest tests/test_health_ready.py (fakes first); later authenticated local readiness probe and authorized schema comparison. Do not log DSNs.
- **Acceptance:** Empty-target preflight, expected revision, liveness independence, sanitized unavailable/mismatch 503 and unauthenticated readiness 401. Preserve company_db.
- **Definition of Done:** Shared DoD plus execution log, schema comparison and fresh-environment recovery procedure; backup/restore before any later populated modification.
- **DB impact / approval:** Creates companyos_dev/schema/version metadata only after explicit authorization. No training data, automatic seeds, startup migration or stamping.

### S1-06 — Isolated test database, fixtures and migration rehearsal

- **Goal:** Enable safe MySQL-specific integration tests (NFR-02/06/07).
- **Dependencies:** S1-05; explicit approval of companyos_test target AND provisioning, migration, fixture/cleanup operations. Fixture insertion into companyos_dev needs its own authorization.
- **Planned files:** apps/api/tests/conftest.py, fixtures.py, test_migration_roundtrip.py, test_database_guards.py; fixture and recovery instructions.
- **Implementation:** Synthetic USD/monthly salaries and USD budgets only. Guard host/database/environment before connection and before cleanup; least privilege limits destructive tests to companyos_test. Test B0 and approved T1/T2; prove constraints and recoverability. No SQLite-only equivalence claim.
- **Planned commands:** Owner-reviewed provisioning method; python -m alembic upgrade <approved-revision> under explicitly isolated test settings; no unreviewed seed CLI.
- **Verification commands:** python -m pytest tests/test_database_guards.py tests/test_migration_roundtrip.py; fixture creation/cleanup occurs only inside approved guarded tests.
- **Acceptance:** Tests refuse company_db/companyos_dev/production as destructive targets; restore/rebuild rehearsal verified; blank/null/default/decimal/key cases checked.
- **Definition of Done:** Shared DoD plus actual MySQL results, revision identity and test cleanup evidence.
- **DB impact / approval:** Destructive disposable-test activity is explicit, never inferred from general test permission. Stop if companyos_test remains unapproved.

## S2 — Employee read API (2 tasks)

### S2-01 — Employee list/detail and role DTOs

- **Goal:** Deliver read endpoints 03/04 (FR-E02/E03/E06, US-E02/E03/S01).
- **Dependencies:** S1-05/06; D09/D12/D18/D22 read-policy approval. S1-04 optional for B0-compatible reads.
- **Planned files:** apps/api/app/modules/employees/{router,schemas,service,repository}.py; tests/test_employee_reads.py.
- **Implementation:** Bounded list/count transaction, stable ID tie-breaker, nullable department, exact Decimal strings for Administrator. Proposed Viewer excludes salary/email/hire_date and financial metadata; no nested leaks. Safe 404/422 and no commits on reads.
- **Planned commands:** python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers --no-access-log.
- **Verification commands:** python -m pytest tests/test_employee_reads.py against approved synthetic companyos_test.
- **Acceptance:** Defaults 1/20/max100; correct totals, zero/out-of-range pages, detail not-found, B0 integer salary serialization; no training labels.
- **Definition of Done:** Shared DoD plus reviewed OpenAPI/examples and actual MySQL HTTP integration.
- **DB impact / approval:** App reads companyos_dev; tests write only approved companyos_test. No schema changes.

### S2-02 — Query privacy and read-contract regression

- **Goal:** Verify inference and serialization boundaries (FR-E06, SEC-03, US-S01).
- **Dependencies:** S2-01 and approved D18/D22.
- **Planned files:** apps/api/tests/test_employee_query_security.py, test_read_contracts.py; employee module fixes if tests expose issues.
- **Implementation:** Email-only matching fixture; Viewer name_email and hire-date sort reject before queries; unsupported filters 422. Confirm hidden-value changes cannot affect permitted Viewer results/count/order; bounded query count, session cleanup, sanitized errors.
- **Planned commands:** No setup/migration command; run targeted checks.
- **Verification commands:** python -m pytest tests/test_employee_query_security.py tests/test_read_contracts.py.
- **Acceptance:** Administrator access works; Viewer keys/values and nested outputs obey reviewed allowlist; no role headers accepted.
- **Definition of Done:** Shared DoD plus negative-test evidence; do not declare real authentication complete.
- **DB impact / approval:** Synthetic fixture mutations only within separately approved companyos_test scope.

## S3 — Connected employee listing (2 tasks)

### S3-01 — Minimal web application and typed API transport

- **Goal:** Establish planned App Router shell and API client (NFR-01/03, US-E02).
- **Dependencies:** S1-01, S2-02; owner approval of web initialization, compatible exact package pins and installation.
- **Planned files:** apps/web/package.json, package-lock.json, tsconfig.json, Next/Tailwind config, app/layout.tsx, app/page.tsx, app/globals.css, lib/api/client.ts, lib/contracts/employees.ts, components/layout/; only needed shadcn primitives.
- **Implementation:** Initialize in the existing apps/web folder while preserving .env.example; review scaffolder output before accepting it. Client/server secrets separated; /api/v1 base once; no extra Next business API or global state framework.
- **Planned commands:** Reviewed Next scaffold/install commands fixed after version approval; npm run dev -- --hostname 127.0.0.1 --port 3000.
- **Verification commands:** npm run typecheck; npm run lint; npm run build (define scripts first).
- **Acceptance:** Responsive accessible shell; typed distinct Viewer/Administrator shapes; no DB/client secrets; no initialization overwrites.
- **Definition of Done:** Shared DoD plus package/lockfile review and actual build evidence.
- **DB impact / approval:** None directly; no browser DB connection. Dependency/scaffolder execution requires approval.

### S3-02 — Real employee listing integration

- **Goal:** Complete first end-to-end slice (FR-E02/E06, US-E02/S01).
- **Dependencies:** S3-01/S2-02; approved local CORS origins and safe synthetic dev fixtures.
- **Planned files:** apps/web/app/(workspace)/{layout.tsx,employees/page.tsx}, features/employees/list.tsx, tests/employees-list.spec.ts; lib/api error/cancellation handling.
- **Implementation:** Client API fetch; URL state for allowed query controls; no Viewer hire-date/email controls. Loading/error/empty/forbidden states, cancel stale requests, clear identity-dependent state, no privileged SSR fallback.
- **Planned commands:** Start local API/web via previously approved commands; npm run test:e2e -- tests/employees-list.spec.ts after reviewed test-tool setup.
- **Verification commands:** npm run typecheck; npm run build; npm run test:e2e -- tests/employees-list.spec.ts.
- **Acceptance:** Browser → real API → isolated MySQL, not mock-only; both role projections and permission failures demonstrated; keyboard/mobile checks.
- **Definition of Done:** Shared DoD plus [first-slice evidence](first-vertical-slice.md). Owner review before S4.
- **DB impact / approval:** Reads approved development fixtures. Automated setup/cleanup only approved companyos_test; no public stub deployment.

## S4 — Employee mutations without hard deletion (3 tasks)

### S4-01 — Create employee API and form

- **Goal:** Deliver FR-E01 / US-E01.
- **Dependencies:** S3-02; approved D02/D03/D04/D05/D09/D13/D18/D22; S1-04 applied/rehearsed in authorized environments.
- **Planned files:** employee backend module, tests/test_employee_create.py; apps/web/app/(workspace)/employees/new/page.tsx, features/employees/form.tsx, tests/employee-create.spec.ts.
- **Implementation:** Monthly USD Decimal(12,2), optional unique normalized email/department/hire date; no today default. Service validates DTO then commits before 201 with valid employee Location; atomic conflicts mapped safely.
- **Planned commands:** Existing local app commands; no implicit schema setup.
- **Verification commands:** python -m pytest tests/test_employee_create.py; npm run test:e2e -- tests/employee-create.spec.ts; npm run typecheck.
- **Acceptance:** Fraction/overflow/null/blank and concurrent duplicate-email cases; Viewer 403; form preserves failed input.
- **Definition of Done:** Shared DoD plus tested API/form create and no startup mutation.
- **DB impact / approval:** Approved synthetic employee writes; schema prerequisites explicitly applied elsewhere, never silently here.

### S4-02 — Employee detail and partial update

- **Goal:** Deliver FR-E03/E05 / US-E03/E05.
- **Dependencies:** S4-01; D14 last-write-wins and update/department rules approved.
- **Planned files:** employee backend module, tests/test_employee_update.py; apps/web/app/(workspace)/employees/[employeeId]/page.tsx, employee form, tests/employee-update.spec.ts.
- **Implementation:** GET detail and PATCH workflow, omitted versus null semantics, read-only fields rejected, department FK/race conflict handling; Administrator-only sensitive editing. Status updates use same employee lock as deactivation/assignment policy.
- **Planned commands:** Existing local app commands; no migrations.
- **Verification commands:** python -m pytest tests/test_employee_update.py; npm run test:e2e -- tests/employee-update.spec.ts; npm run typecheck.
- **Acceptance:** Omitted fields preserved, optional fields clearable, required null rejected, safe conflict/404, Viewer read projection and write denial.
- **Definition of Done:** Shared DoD plus explicit concurrency limitation and persisted-value verification.
- **DB impact / approval:** Authorized synthetic row updates only; no training changes.

### S4-03 — Deactivation and lifecycle rules

- **Goal:** Deliver FR-E04 / US-E04.
- **Dependencies:** S4-02; D06/D07 lifecycle/no-parent-delete approval.
- **Planned files:** employee service/router, tests/test_employee_deactivate.py; employee detail controls, tests/employee-deactivate.spec.ts.
- **Implementation:** Repeat-safe POST deactivate sets Inactive and retains memberships. Approved reactivation via PATCH. Employee lock coordinates later assignment creation; no hard-delete API/UI or ORM cascades.
- **Planned commands:** Existing local application commands only.
- **Verification commands:** python -m pytest tests/test_employee_deactivate.py; npm run test:e2e -- tests/employee-deactivate.spec.ts.
- **Acceptance:** Repeated deactivate succeeds; assignments/parents remain; missing employee404, Viewer403; counts refresh.
- **Definition of Done:** Shared DoD plus retention evidence; assignment-race regression expanded in S6-02.
- **DB impact / approval:** Status writes only under authorized synthetic-data scope; no deletes/migration.

## S5 — Departments (2 tasks)

### S5-01 — Department API and integrity

- **Goal:** Deliver FR-D01/D02 / US-D01/D02/D03.
- **Dependencies:** S4-03; D07/D08/D10/D13 department/count policies approved.
- **Planned files:** apps/api/app/modules/departments/{router,schemas,service,repository}.py, tests/test_departments.py.
- **Implementation:** List/detail/create/PATCH; unique trimmed name with collation-aware conflicts; counts include retained employees; no deletion endpoint even for empty department.
- **Planned commands:** Existing API command only.
- **Verification commands:** python -m pytest tests/test_departments.py.
- **Acceptance:** Empty/count pagination, duplicate-name races, stable IDs, Viewer writes403; FK protection tested only in isolated tests.
- **Definition of Done:** Shared DoD plus endpoints08–11 matched to OpenAPI.
- **DB impact / approval:** Approved synthetic department writes; no new schema/index or parent deletion.

### S5-02 — Department UI

- **Goal:** Complete connected department workflows (US-D01/D02/D03/E05).
- **Dependencies:** S5-01.
- **Planned files:** apps/web/app/(workspace)/departments/page.tsx, departments/[departmentId]/page.tsx, features/departments/, lib/contracts/departments.ts, tests/departments.spec.ts.
- **Implementation:** List/count/detail/create/rename, employee-filter link and optional department selector; no delete controls; field errors retained.
- **Planned commands:** Existing local API/web start commands.
- **Verification commands:** npm run typecheck; npm run build; npm run test:e2e -- tests/departments.spec.ts.
- **Acceptance:** Connected forms and counts, role restrictions, empty/error/loading and keyboard states.
- **Definition of Done:** Shared DoD plus API/UI behavior demonstrated; owner review before S6.
- **DB impact / approval:** Calls previously approved mutation endpoints; test writes confined to companyos_test.

## S6 — Projects and assignments (3 tasks)

### S6-01 — Project API and UI

- **Goal:** Deliver FR-P01 / US-P01.
- **Dependencies:** S5-02; D08/D18/D22 project/field policy approval.
- **Planned files:** apps/api/app/modules/projects/{router,schemas,service,repository}.py, tests/test_projects.py; apps/web/app/(workspace)/projects routes, features/projects/, lib/contracts/projects.ts, tests/projects.spec.ts.
- **Implementation:** Four project endpoints and connected forms; required date, optional nonnegative exact USD budget. Approved Viewer projection excludes budget and budget_currency; no budget search/filter/sort, no deletion.
- **Planned commands:** Existing local app commands.
- **Verification commands:** python -m pytest tests/test_projects.py; npm run typecheck; npm run test:e2e -- tests/projects.spec.ts.
- **Acceptance:** Unique-name conflict, future start date, budget null/precision, nested privacy and accessible UI tested.
- **Definition of Done:** Shared DoD plus endpoints12–15 integration evidence.
- **DB impact / approval:** Synthetic project writes under approved scope; existing budget precision unchanged.

### S6-02 — Composite-key membership transactions

- **Goal:** Deliver FR-P02/P03 / US-P02/P03 safely.
- **Dependencies:** S6-01/S4-03; D06/D08/D13 approved.
- **Planned files:** projects assignment router/schemas/service/repository as needed within same module; tests/test_assignments.py, test_assignment_races.py.
- **Implementation:** Five operations16–20: both paginated parent collections, POST, composite-pair PATCH/DELETE. No surrogate key. Lock employee before project for creates; synchronize deactivation/status mutation. POST201 DTO without Location; collections are read path. DELETE only membership.
- **Planned commands:** Existing API command; no new table/index.
- **Verification commands:** python -m pytest tests/test_assignments.py tests/test_assignment_races.py.
- **Acceptance:** Concurrent duplicate pair409; inactive create409, parent missing404, deletion repeat404; role nonblank; preserved parent rows and rollback on failure; no implicit mutation retries.
- **Definition of Done:** Shared DoD plus MySQL race tests and error/transaction evidence.
- **DB impact / approval:** Authorized synthetic membership writes/removals; destructive tests only companyos_test; no parent deletes.

### S6-03 — Membership UI and safe nested contracts

- **Goal:** Complete employee/project membership workflows (US-E03/P02/P03/S01).
- **Dependencies:** S6-02.
- **Planned files:** apps/web/features/projects/assignments.tsx, employee/project detail integration, lib/contracts/assignments.ts, tests/assignments.spec.ts.
- **Implementation:** Paginated memberships, bounded employee selection using existing list endpoint, assign/role edit/remove confirmation, conflict display, refresh only after committed success. No new lookup/resource endpoint.
- **Planned commands:** Existing local application commands.
- **Verification commands:** npm run typecheck; npm run build; npm run test:e2e -- tests/assignments.spec.ts.
- **Acceptance:** Both parent views agree; Viewer reads safe summaries and cannot write; no hidden data or unbounded arrays.
- **Definition of Done:** Shared DoD plus end-to-end composite-pair evidence.
- **DB impact / approval:** Existing approved assignment endpoints only; synthetic test scope.

## S7 — Dashboard (2 tasks)

### S7-01 — Aggregate API

- **Goal:** Deliver FR-H01 / US-H01.
- **Dependencies:** S6-03; D10 metric definitions and D22 pagination approved.
- **Planned files:** apps/api/app/modules/dashboard/{router,schemas,service,repository}.py, tests/test_dashboard.py.
- **Implementation:** Endpoints21–23; counts without multiplied joins, distinct assigned employees separate from membership pairs; include zeros and derived Unassigned group, never insert a fake department row. Parameterized SQL only if ORM/Core insufficient and justified.
- **Planned commands:** Existing API start command.
- **Verification commands:** python -m pytest tests/test_dashboard.py.
- **Acceptance:** Empty/all-inactive/multiple-membership fixtures, paginated totals including Unassigned, no monetary/contact/date leakage; both roles read same counts.
- **Definition of Done:** Shared DoD plus query correctness/boundedness measurements, without inventing D16 latency promises.
- **DB impact / approval:** Read-only app operations; approved test fixture writes only; no summary tables/indexes.

### S7-02 — Dashboard UI

- **Goal:** Complete statistics interface (US-H01, NFR-03).
- **Dependencies:** S7-01.
- **Planned files:** apps/web/app/(workspace)/dashboard/page.tsx, features/dashboard/, lib/contracts/dashboard.ts, tests/dashboard.spec.ts.
- **Implementation:** Labeled cards and paginated distributions; distinguish active/total/distinct/pairs. Use simple accessible tables; no chart library unless justified and approved.
- **Planned commands:** Existing local app commands.
- **Verification commands:** npm run typecheck; npm run build; npm run test:e2e -- tests/dashboard.spec.ts.
- **Acceptance:** Real aggregate API, zero/error/loading states, accessible mobile display; no synthetic department persisted.
- **Definition of Done:** Shared DoD plus local MVP module review; still no public readiness.
- **DB impact / approval:** Read-only via API; approved test setup only.

## S8 — Real authentication and authorization (3 tasks)

### S8-01 — Provider, transport and trusted role design approval

- **Goal:** Resolve D09/D23 concretely before integrating public identities (SEC-01/04/06).
- **Dependencies:** Local module review; owner selection of provider/session design, allowed origins, role provisioning and revocation policy.
- **Planned files:** docs/open-decisions.md, security-plan.md, deployment-plan.md, frontend-architecture.md; no account table assumed.
- **Implementation:** Present compatible provider options with current official documentation; compare cookie/CSRF versus bearer/PKCE, SSR needs, key rotation, session lifetime/logout, role mapping and costs. Record actual owner choice only.
- **Planned commands:** Documentation inspection only; provider-specific setup commands cannot be fixed until selected, then require separate review.
- **Verification commands:** Relative-link/decision/contract review; no authentication tests claimed yet.
- **Acceptance:** Concrete provider and approved security flow; no client-authoritative roles or public stub; any new persistence requirement returns to design approval.
- **Definition of Done:** Shared DoD plus recorded owner decision, or task explicitly remains blocked.
- **DB impact / approval:** None; no new business tables or provider tenant setup authorized by documentation review.

### S8-02 — Implement provider-backed identity

- **Goal:** Replace local synthetic identity for all public modes (US-S01, SEC-01–06/10).
- **Dependencies:** S8-01; explicit provider project/SDK installation and integration approval.
- **Planned files:** apps/api/app/core/identity.py, tests/test_provider_auth.py; apps/web/lib/auth/, selected login/callback/logout routes, API credential transport and environment examples; lockfiles.
- **Implementation:** Verify signature/issuer/audience/time/type, trusted role mapping, logout/revocation and failure behavior. Implement approved cookie+CSRF or token flow; no shared privileged SSR credential; staging/production fail without real auth.
- **Planned commands:** Exact provider/SDK commands presented for approval after S8-01; existing app commands; no invented provider CLI.
- **Verification commands:** python -m pytest tests/test_provider_auth.py; npm run typecheck; npm run test:e2e -- tests/auth.spec.ts (new planned spec).
- **Acceptance:** Both roles, invalid/expired credentials, trusted role provisioning, no secrets in bundles/logs, role-switch state clearing.
- **Definition of Done:** Shared DoD plus actual provider-backed verification evidence without exposing tokens.
- **DB impact / approval:** No schema change planned; provider stores identities. Any DB/session persistence requirement blocks for explicit design approval.

### S8-03 — Security release regression

- **Goal:** Prove authorization independently of UI (US-S01, SEC-03/05–10).
- **Dependencies:** S8-02 and final D18 approval.
- **Planned files:** apps/api/tests/test_security_release.py; apps/web/tests/security.spec.ts; release security checklist.
- **Implementation:** Direct API allow/deny matrix across all23 operations; nested DTOs, hidden query inference, cache separation, CORS, chosen CSRF flow, revoked/unknown roles, sanitized errors, public-stub rejection.
- **Planned commands:** Approved isolated/local security harness only; never probe an unapproved public service.
- **Verification commands:** python -m pytest tests/test_security_release.py; npm run test:e2e -- tests/security.spec.ts; npm run build and inspect for secret exposure.
- **Acceptance:** No bypass via UI headers/caches; liveness only public nonbusiness exception; sensitive fields absent for Viewer.
- **Definition of Done:** Shared DoD plus traceable negative-test evidence; unresolved security failure blocks S9.
- **DB impact / approval:** Synthetic approved test scope only; no production fixtures/destructive tests.

## S9 — Deployment and production verification (3 tasks)

### S9-01 — Release plan and recovery rehearsal

- **Goal:** Make a reviewable release with operational evidence (NFR-07, D15/D17).
- **Dependencies:** S8-03; owner-selected backend/managed MySQL providers, region/cost, origin topology and synthetic public data policy; release approval not inferred.
- **Planned files:** Provider-required deployment configuration only after review; docs/deployment-plan.md and runbook; approved CI configuration if requested.
- **Implementation:** Pin runtime/build settings, HTTPS/private DB network, runtime versus migration secrets, backup/restore, health probes, revision compatibility and rollback. Review original SQL preservation and no committed secrets.
- **Planned commands:** npm run build; python -m pytest; provider validation syntax deferred until provider selection. Full tests still require approved isolated target.
- **Verification commands:** npm run typecheck; npm run lint; approved API/e2e suite and isolated restore rehearsal.
- **Acceptance:** Actual build/test evidence; recovery practiced; no provider/staging exposure with stub; costs and operational responsibility accepted.
- **Definition of Done:** Shared DoD plus concrete reviewed release manifest and go/no-go; no deployment yet.
- **DB impact / approval:** Backup/restore rehearsal only on separately approved environments; production provisioning is not part of this approval.

### S9-02 — Separately authorized release execution

- **Goal:** Deploy the reviewed artifact to approved Vercel/backend/MySQL topology.
- **Dependencies:** S9-01; explicit approvals for deployment, provider resources, production DB creation/migration/synthetic seed scope and any Git remote operations.
- **Planned files:** Reviewed deployment configuration and runbook execution record only; no ad hoc production code.
- **Implementation:** Secret injection via provider controls; provision approved empty target; apply exact reviewed revisions as separate release operation; deploy real-auth backend and frontend. No startup migrations or training import; no bypass previews.
- **Planned commands:** Exact provider deploy commands cannot be specified until D17 is approved; show them to owner before execution. python -m alembic upgrade <reviewed-release-revision> only against separately approved production target.
- **Verification commands:** Provider deployment status, authenticated readiness, TLS/network checks, approved non-destructive smoke suite.
- **Acceptance:** Known artifact/revision, healthy topology, CORS allowlist and real auth, secrets server-only; failed gate stops rollout.
- **Definition of Done:** Shared DoD plus deployment IDs, actual command log and recovery decision; no claim production ready before S9-03.
- **DB impact / approval:** Consequential production creation/migration/seed actions each explicitly approved. No remote/push is automatic.

### S9-03 — Production verification and owner handover

- **Goal:** Confirm released behavior and teach ongoing operation (all approved MVP requirements).
- **Dependencies:** S9-02 and explicit production verification scope.
- **Planned files:** docs/release-verification.md, operational runbook and README status; no product changes unless reviewed separately.
- **Implementation:** Verify both real roles, allowed responses, no Viewer hidden fields, logout, no public stub, health/backup ownership and UI workflows. Use approved synthetic smoke records; no destructive suite against production.
- **Planned commands:** Owner-approved production smoke commands/URLs after release; no generic test command that might reset production.
- **Verification commands:** Authenticated read probes and manual browser checks; any smoke mutations explicitly listed and approved first.
- **Acceptance:** Real public authorization and nonsensitive metrics correct; unresolved failures reported with recovery steps, not hidden as success.
- **Definition of Done:** Shared DoD plus Arabic owner walkthrough, recorded limitations and explicit acceptance.
- **DB impact / approval:** Read-only by default; any production write/cleanup requires separate precise approval. No training access.

## Decisions that can block later tasks

- S1-01: runtime availability, reviewed exact pins and bootstrap/install approval; Git initialization only if chosen and approved. None of the DB-policy decisions authorize a connection here.
- S1-03–06: D01/D08/D11 retained baseline policy, execution approvals; D02/D05 for T1/T2; companyos_test approval for destructive/integration verification.
- S2–S7: D03–D10/D12–D14/D18/D22 and relevant acceptance criteria. D18 currently recommends withholding salary/email/hire_date/budget, not a settled owner policy. D16 performance expectations remain open, with bounded measurements proposed.
- S8–S9: concrete D09/D23 provider/transport/session and D17 hosting/networking; D15 data-use obligations; real authentication before any public preview.
- Every task: Arabic explanation and transparent execution reporting; no permissions inherited from a planning document. See [phase-0-checklist.md](phase-0-checklist.md).
