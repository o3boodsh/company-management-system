# CompanyOS — Company Management System

CompanyOS is a single-company management MVP and portfolio project. The goal is a maintainable application for employees, departments, projects, assignments, and operational dashboard statistics.

## Current status

Phase 0 planning is complete. **S1-02 adds explicit startup configuration and safety to the working FastAPI liveness endpoint:** GET /api/v1/health/live. Liveness has no database, credential, or identity dependency. Application startup now validates explicit APP_ENV/AUTH_MODE; importing the app does not load settings or connect. Employee/business endpoints, readiness, real authentication, Next.js, and migrations are not implemented.

The owner installed Python and dependencies globally before this task. This bootstrap reused that environment; it did not install/upgrade packages, create a virtual environment, initialize Git, connect to MySQL, or deploy anything. No dependency manifests or lockfiles have been generated. Isolated project dependency management and reproducible locking remain future improvements requiring review.

The schema export describes an exported MySQL state, not a fresh inspection of live company_db. Existing SQL is preserved as evidence and must not be run as an application setup script. Git was not initialized when checked; no initialization, commit, remote creation, or push was performed.

## MVP scope and stack

- Employee listing/detail/create/update/deactivation, department assignment, protected contact/financial data.
- Department listing/detail/create/update and employee counts.
- Project listing/detail/create/update and role-bearing employee assignments.
- Dashboard counts and department/project membership distributions.

Planned stack: Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui; FastAPI, Pydantic, SQLAlchemy 2.x, Alembic; MySQL 8. Frontend deployment targets Vercel; separate Python hosting, managed MySQL, and identity provider remain unselected.

The backend is a modular monolith with versioned `/api/v1` REST routers, schemas, services, repositories, and database configuration. FastAPI owns business authorization and transactions. The frontend never connects directly to MySQL. Alembic is the schema authority; no automatic table creation at startup.

## Currency and approval boundaries

Owner-approved: **all new approved MVP monetary values are USD; salaries are monthly USD and project budgets are USD**. No import, currency conversion or relabeling of existing training records. The owner requires Arabic learning-oriented explanations before implementation and exact command/result reporting afterward.

Approved: isolated companyos_dev as the MVP development target, with creation separately gated. Still proposed: companyos_test, salary DECIMAL(12,2), removal of the hire-date automatic default, operational policies, and final access matrix. Preserve company_db, four business entities, employee_status, restrictive foreign keys, and the composite assignment key. See the [decision register](docs/open-decisions.md) for partial approvals; currency approval does not approve schema changes or execution.

## Actual project tree

```text
company-management-system/
├── apps/
│   ├── api/
│   │   ├── .env.example
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── core/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── config.py
│   │   │   │   ├── identity.py
│   │   │   │   └── errors.py
│   │   │   ├── db/
│   │   │   │   ├── __init__.py
│   │   │   │   └── session.py
│   │   │   └── system/
│   │   │       ├── __init__.py
│   │   │       └── router.py
│   │   └── tests/
│   │       ├── conftest.py
│   │       ├── test_config.py
│   │       ├── test_identity.py
│   │       ├── test_errors.py
│   │       ├── test_session_lifecycle.py
│   │       └── test_health_live.py
│   └── web/
│       └── .env.example
├── database/
│   ├── company_schema.sql
│   └── legacy-sql/
│       └── 03_queries.sql
├── docs/                  # Phase 0 specifications and development workflow
├── AGENTS.md              # Arabic explanations and owner review gates
├── .gitignore
└── README.md
```

apps/api contains health, configuration/error guards, a future local identity dependency, and session cleanup preparation. No engine/session factory is configured and no database is accessed. apps/web contains its credential-free template only. Generated Python/pytest caches are ignored and omitted from this tree. Further planned source layout is in [architecture.md](docs/architecture.md).

## Working local API commands — S1-02

Verified interpreter: Python 3.13.16 at C:\Users\artis\AppData\Local\Programs\Python\Python313\python.exe. This session's bare python command still resolves to a Microsoft Store alias, so use the full interpreter path. Globally installed versions observed: pip 26.2.1, FastAPI 0.143.0, Pydantic 2.14.1, Uvicorn 0.54.0, pytest 9.1.1, httpx 0.28.1. These observations are not a reproducible dependency installation specification.

From the repository root in PowerShell, run:

```powershell
$env:APP_ENV='local'
$env:AUTH_MODE='development-stub'
& 'C:\Users\artis\AppData\Local\Programs\Python\Python313\python.exe' -m uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8000 --no-proxy-headers --no-access-log
```

From apps/api, run all focused safety and health tests (including the existing eight health cases):

```powershell
& 'C:\Users\artis\AppData\Local\Programs\Python\Python313\python.exe' -m pytest tests -q
```

While the server is running, from another local terminal:

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8000/api/v1/health/live
Invoke-RestMethod -Uri http://127.0.0.1:8000/openapi.json
Invoke-WebRequest -Uri http://127.0.0.1:8000/docs
```

Open http://127.0.0.1:8000/docs for Swagger UI. Expected liveness response is HTTP 200 with {"data":{"status":"ok"}}. Unsupported query parameters return a sanitized 422 error envelope with a generated request_id and no echoed names/values. Pydantic defines the successful response shape; no service/repository layer is needed for this constant result.

S1-02 verification: **68 passed, 0 failed, 1 warning** (42 configuration cases, 6 identity cases, 6 error cases, 6 fake-session lifecycle cases, and the existing 8 health cases). The warning is the existing Starlette deprecation about httpx TestClient integration; no package was changed. Import without settings/DB modules, local startup, HTTP liveness, OpenAPI, Swagger HTML, and sanitized query rejection passed. Swagger's external browser assets were not visually tested. The local server was stopped after verification. No real authentication or database readiness is established by these checks.

## Configuration and safety — S1-02

Environment variables are process settings supplied outside the source code. The small frozen Pydantic Settings model reads only recognized process variables; it does not load .env files or print configuration values. pydantic-settings was checked and is not installed; Pydantic already provides the validation needed here, so no extra dependency was installed.

APP_ENV and AUTH_MODE are required, case-sensitive selections. APP_ENV accepts local, test, staging, production; there is no implicit local fallback. Tests isolate these values and clear all recognized operator settings. Missing/invalid configuration fails startup with a generic ConfigurationError that omits original validation input. Importing the application remains safe without environment settings. Liveness requires no DB URL, credentials, provider contact or database availability after valid startup.

- development-stub is permitted only in local/test with synthetic-mvp and an explicit loopback IP in API_BIND_HOST (default 127.0.0.1). Use the matching Uvicorn --host flag; the config variable does not bind the server itself.
- staging/production reject the stub. provider is a recognized future mode but currently rejected in every environment because real provider verification is not implemented. Configuring issuer/JWKS fields alone cannot make the current application production-ready.
- get_development_principal is a future opt-in dependency, not attached to liveness or any shipped business/authentication endpoint. It uses trusted DEV_IDENTITY_ROLE (default Viewer), verifies actual ASGI server/client loopback addresses and ignores role/Host/forwarding headers. There is no role-switch endpoint. Test-only routes are not part of the application.
- company_db, companyos_test and all other unapproved database names are rejected. Optional local DSNs are checked syntactically for companyos_dev and masked with SecretStr; accepted syntax does not authorize connecting. Test mode rejects every nonempty DB URL, including companyos_dev, while companyos_test remains unapproved. Blank URLs require no credentials and configure no access.
- The request session dependency has no factory/engine configured and cannot open a database. session_scope accepts an explicitly supplied future factory, closes each session and rolls back unfinished work; it never commits. If cleanup also fails during a service failure, the original exception is preserved. Without a service failure, cleanup failure raises a sanitized SessionCleanupError. Close is attempted even after rollback failure; cleanup logs contain no driver exception text. Only fake sessions were exercised. Engine creation, credentials, DB connections and MySQL integration verification remain separately gated.

RequestSafetyMiddleware generates a fresh UUID per HTTP request, ignoring client-supplied request IDs; X-Request-ID matches error.request_id. Responses use private, no-store. Validation failures omit raw input; unexpected failures return a generic 500 envelope and log only the generated request ID without exception text/stack or request values. Default framework 401/403/404/405 errors are also sanitized. The launch command disables access logging so query strings are not logged by Uvicorn. These safeguards do not constitute provider authentication, authorization for business records or final approval of the D09/D18 policy.

This task implements S1-02's configuration/identity boundary and fake-tested session cleanup. Compared with the original backlog, dependency installation/lockfiles and the lazy engine are deliberately deferred; no new dependency was needed and no engine was created. Remaining planning documents retain their historical proposal status; the current implementation status and tested commands are recorded here.

### S1-02C regression verification

Latest full-suite result: **145 passed, 0 failed, 1 existing warning** (109 configuration cases, 8 identity cases, 6 error cases, 14 session cases, 8 health cases). The first run had three failures in a new redaction assertion that confused the legitimate synthetic-mvp setting with credentials; the assertion was corrected and the complete suite rerun successfully. No installed package changed.

SQLAlchemy make_url is now the authoritative DSN parser; the exact parsed database must match companyos_dev. Raw control/whitespace characters, decoded controls, malformed ports/hosts, raw fragments and all query options (including empty delimiters) are rejected. Properly encoded credential characters are allowed when the final database matches; credentials remain SecretStr values. Import now loads SQLAlchemy for URL parsing only, never constructs an Engine or connects. company_db/companyos_test remain forbidden and test mode still rejects all nonempty DSNs.

Regression coverage includes tab/newline/fragment/whitespace cases, escaped components, malformed DSNs, combined service/rollback/close failures and log/error redaction. Uvicorn's loaded ASGI wrapper was tested in-process with proxy_headers=False: forwarded headers cannot change the real client boundary or trusted role. The development stub must never be exposed through a public proxy, tunnel or preview. --no-proxy-headers disables address rewriting; it does not make public stub exposure acceptable.

All tests block Engine construction/Engine connections and outbound socket.create_connection. A separate cold-import/startup/liveness probe also blocked PyMySQL connection entry points and recorded zero attempted DB operations. Real loopback HTTP checks returned liveness 200 with the unchanged JSON, sanitized query 422, and the same single OpenAPI path. The server was stopped. Historical SQL hashes are unchanged; no DB access, migrations, installs or S1-03 work occurred.

## Documentation map

| Area | Documents |
|---|---|
| Requirements | [Requirements](docs/requirements.md), [MVP scope](docs/mvp-scope.md), [User stories](docs/user-stories.md), [Decisions](docs/open-decisions.md) |
| Database | [ERDs](docs/erd.md), [Database design](docs/database-design.md), [Migration plan](docs/database-migration-plan.md) |
| Application | [Architecture](docs/architecture.md), [API contract](docs/api-contract.md), [Security](docs/security-plan.md), [Frontend](docs/frontend-architecture.md) |
| Final planning | [26-task backlog](docs/implementation-backlog.md), [First coding task](docs/phase-1-start.md), [Readiness checklist](docs/phase-0-checklist.md), [Agent rules](AGENTS.md) |
| Delivery | [Deployment](docs/deployment-plan.md), [First vertical slice](docs/first-vertical-slice.md), [Development workflow](docs/development-workflow.md) |

## Planned setup — not executed

1. Review completed S1-02 configuration/safety before authorizing S1-03.
2. Initialize version control if approved. Review the ignore rules and files before staging.
3. Review isolated dependency management for apps/api and initialize apps/web only in a later authorized phase.
4. Configure local ignored environment files from the examples. Empty credential/auth values intentionally make the examples nonfunctional; do not invent production credentials or enable a stub publicly.
5. After separate authorization, provision isolated development/test databases, create their schema through reviewed Alembic migrations, and use synthetic fixtures. Do not reuse training records as USD data.
6. Deliver the first vertical slice: health/readiness, Employees GET, and the connected Next.js listing with role-aware projections and MySQL integration tests.

Only the local health API is runnable using the commands above. [phase-1-start.md](docs/phase-1-start.md) and the [backlog](docs/implementation-backlog.md) retain the earlier planning commands; this task's owner authorization specifically used the installed global interpreter without venv creation, installation, manifests or lockfiles. Those planned setup actions were not executed.

Recommended Git commands for the owner to run later from this folder (not executed):

```powershell
git init -b main
git status --short --untracked-files=all
git check-ignore -v --no-index apps/api/.env apps/web/.env.local
```

Review files before selectively staging. This document does not instruct an automatic commit, remote, or push. `.gitignore` does not protect files already tracked or replace a secret review.

## Local versus public release

Local development may use synthetic data and an explicitly development-only identity stub with real permission checks. Proposed Viewer responses omit salary, employee email, hire_date, and project budget; nested responses and search/counts obey the same policy. The final field allowlist remains pending owner review.

No public preview or production bypass is permitted. Before public release, use real provider-backed authentication, backend role enforcement, HTTPS, safe CORS/session handling, private database networking, backups/restore verification, and approved deployment settings. No passwords, tokens, personal data dumps, or real backups belong in Git. The project is not production-ready.
