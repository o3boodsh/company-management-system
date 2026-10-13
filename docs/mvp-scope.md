# CompanyOS MVP scope

Status: Revised draft for owner review, 2026-10-11. USD salary currency is owner-approved; monthly payment is the confirmed design assumption for new approved MVP data. Other targets and policies remain proposed under [open-decisions.md](open-decisions.md). No implementation is authorized.

Existing training salary amounts must remain unchanged and must not be converted or presented as verified USD/monthly salaries. The precision migration remains proposed; project budget currency is approved as USD; D20 no-import boundary and companyos_dev target are confirmed; creation remains separately gated and companyos_test is proposed. Database Design review artifacts are [erd.md](erd.md), [database-design.md](database-design.md), and [database-migration-plan.md](database-migration-plan.md).

## In scope

- Employee create/list/detail/update, bounded pagination, search/filter/sort, optional department assignment subject to approval, and deactivation rather than physical deletion.
- Department create/list/detail/update and employee counts; no department deletion endpoint in the proposed MVP, including empty departments (D07 pending).
- Project create/list/detail/update and employee membership management, including role definition and removal of assignments. Role edits are proposed as part of membership management.
- Dashboard counts for employees, active employees, departments, projects, department distribution, and project membership.
- Monorepo architecture using the specified Next.js/TypeScript/Tailwind/shadcn stack, FastAPI/Pydantic/SQLAlchemy/Alembic backend, and MySQL 8.
- Documentation, validation, error handling, meaningful tests, and deployment preparation appropriate to the release stage.
- Two proposed roles, Administrator and Viewer. Proposed Viewer responses exclude salary, employee email, and hire_date; project budget is proposed Administrator-only pending D18. Real authentication and backend authorization are required before public deployment. Implementation is not part of this documentation task.

## Out of scope

Attendance, leave requests, payroll processing, notifications, complex analytics, multi-company tenancy, advanced permission administration, employee self-service, public employee directories, import/export workflows, multiple currencies per record, currency conversion, project deletion, and employee hard deletion are excluded. No new project lifecycle, time tracking, or assignment-history subsystem is proposed.

Audit-trail implementation is excluded unless a concrete production requirement is identified and approved. Authentication-account security is not excluded merely because advanced permission management is excluded.

## Vertical slice milestones and gates

Before S1, review these requirements and the Phase 0 Database Design/ERD, resolve blocking database policies, and approve any later database access separately. D19 proposes vertical slice development: deliver working API-to-frontend behavior incrementally, rather than all backend modules before the frontend.

| Stage | Deliverable | Acceptance gate and traceability |
|---|---|---|
| S1 | Backend foundation and isolated development MySQL connection | Agreed baseline/configuration, synthetic fixture strategy, development-only identity stub and permission boundary. No use of live records as test data. |
| S2 | Employees GET API | US-E02 read contract works against isolated MySQL fixtures before create API exists; pagination and role-aware projection tested. |
| S3 | Next.js Employees listing connected to the real FastAPI API | US-E02 browser-to-API-to-DB path works, including search/filter/sort and loading/empty/error states. Static frontend mocks alone do not pass. |
| S4 | Employee create/update/deactivation and details, API plus UI | US-E01/E03/E04; optional department IDs validated with synthetic existing departments. Department picker/count integration completes at S5; membership detail completes at S6. |
| S5 | Departments API and frontend | US-D01–D03 and US-E05; employee department picker and counts work end to end. No new deletion workflow without approval. |
| S6 | Projects and assignments API and frontend | US-P01–P03; composite-PK conflicts, role edits/removal, employee memberships, and sensitive nested-response rules verified. |
| S7 | Dashboard API and interface | US-H01; all specified statistics reconcile with fixture data. Local MVP gate reached, with real production identity still incomplete. |
| S8 | Production authentication and authorization | US-S01 with real identities; replace the local stub, verify every existing endpoint and cache, and disallow deployed bypass. |
| S9 | Integrated testing, deployment, production verification | Cross-slice regression, builds, recovery/migration rehearsal, approved hosting/configuration, and all public-release gates pass before public business access. |

Every slice includes relevant validation, integrity, permission, and UI tests. S8 completes real identity integration and authorization hardening; it does not defer backend field protection until deployment. S9 consolidates verification rather than starting testing. No public previews or business endpoints may be exposed during S1–S7. Deployment and all implementation remain future work requiring approval.

## Module acceptance criteria

| Module | Acceptance conditions |
|---|---|
| Employees | Create a valid record; retrieve it; update only intended fields; navigate/search/filter/sort deterministically; assign/clear a department under approved optionality; deactivate without deleting rows or assignments; reject invalid salary/status/email and nonexistent departments; omit salary/email/hire_date for Viewer and prevent hidden-email search matches. US-E01–E05 and US-S01. |
| Departments | Create/list/rename departments; show counts including zero; reject duplicate or blank names; expose no parent deletion endpoint under proposed D07 and retain restrictive FK protection. Empty-department deletion would require a separately approved scope change. US-D01–D03. |
| Projects/assignments | Create/list/detail/update projects with valid start date and budget; apply proposed Administrator-only budget visibility; assign an existing eligible employee with a role; reject duplicate pairs, missing parents, and blank roles; remove or edit one assignment without changing parent records; enforce Viewer field omissions in nested memberships. US-P01–P03. |
| Dashboard | Display all six requested metric families from persisted state; preserve zero-member groups and Unassigned employees; count unique assignment pairs without join multiplication; reflect successful mutations on refresh; expose no salary aggregates. US-H01. |

All acceptance tests must use isolated, synthetic records. Existing `company_db` records are not disposable test fixtures.

## Definition of Done

- Scope and blocking decisions have recorded approval; approved rules map to requirement and story IDs.
- Module acceptance and error scenarios pass; integrity conflicts and authorization checks are tested, including direct API access and concurrent duplicates.
- Frontend has usable loading, empty, validation, forbidden, not-found, and service-error states; forms and tables support keyboard use and responsive layouts.
- API contracts specify optional versus omitted values, list behavior, permissions, and stable error categories. No raw database exceptions leak.
- SQLAlchemy metadata matches the accepted baseline and approved deltas. Alembic changes are reviewed and rehearsed in isolated environments. Existing records remain preserved.
- Setup, architecture, configuration variables without secret values, test instructions, migration instructions, and known limitations are documented.
- Tests and agreed build/type/lint checks pass. Agreed performance measurements are recorded, not asserted without measurement.
- Completion is labeled either Local MVP or Production-ready MVP according to the gates below.

## Local MVP versus production release

| Area | Local MVP gate | Production-release gate |
|---|---|---|
| Access | Loopback-only, synthetic data. An explicitly development-only identity stub supplies test roles to real permission checks; production identity remains incomplete. | Real authentication, session validation/revocation, backend permission checks, and no deployed bypass. |
| Sensitive fields | Administrator/Viewer projection tested using development identities. Proposed Viewer gets no salary/email/hire_date; budget restriction follows proposed D18. | Approved field allowlists enforced on all endpoints and nested responses; no sensitive inference through supported queries, errors, or caches. |
| Data | Isolated fixtures; no mutation of existing company records for testing. | Approved data use, preserved records, recoverable backups, successful restore rehearsal, and controlled migration execution. |
| Network | No public exposure. | HTTPS, private/restricted DB connectivity, explicit origins, approved cross-origin auth and CSRF strategy where applicable. |
| Configuration | Documented local settings; no committed secrets. | Server-only secrets, separate runtime/migration credentials, separate environments, and approved hosting/identity providers. |
| Verification | Module and validation tests; security gaps listed. | Access-control matrix tested end to end, direct API failures verified, sensitive logging/caching checked, release checks passed. |
| Operations | Reproducible setup and troubleshooting notes. | Basic health/error monitoring, abuse protection, backup ownership, recovery procedure, and dependency review. |

A local demonstration is not permission to publish unsecured services. A publicly deployed synthetic portfolio demo must satisfy the production access gates. Real personnel data additionally requires approval of the organization's actual handling obligations; no compliance certification is implied.

## Scope control

Any change to roles, employee deletion, assignment multiplicity, currency model, audit requirements, or module boundaries must update the decisions, requirements, stories, and acceptance criteria before implementation. Approval of documentation does not automatically authorize SQL execution or deployment.
