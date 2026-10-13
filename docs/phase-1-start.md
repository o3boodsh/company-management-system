# Phase 1 start — S1-01 only

Status: Proposed first coding task, 2026-10-12. **READY FOR FIRST CODING TASK as a planning handoff, pending explicit owner execution approval. Nothing below has been executed.** This document does not authorize installation, Git initialization or application creation.

## Exact objective

Verify local prerequisites and, after reviewing the findings and approving versions/bootstrap commands, run a minimal FastAPI service with **GET /api/v1/health/live** on loopback. Verify the response, automated health tests, Swagger UI and OpenAPI. Do not connect to MySQL, initialize Alembic, create a database, read schema remotely, implement readiness/business endpoints, or initialize Next.js.

The larger [first vertical slice](first-vertical-slice.md) needs later S1–S3 tasks. S1-01 proves HTTP liveness only; it does not prove database readiness or authentication. Trace: NFR-07, API endpoint01, [backlog](implementation-backlog.md).

## Arabic explanation and review checkpoints

Before running anything, explain in Arabic: why each prerequisite is checked, which files will be created, the exact commands, expected output, and what failures mean. Explain that FastAPI handles HTTP, Pydantic validates data, Uvicorn serves the process, and OpenAPI describes the contract; a liveness probe checks process responsiveness and needs no database.

1. Ask for approval to start S1-01 and its read-only prerequisite checks.
2. Report detected versions/missing tools. Propose exact dependency pins and bootstrap/install commands. Do not install a missing runtime or MySQL server automatically.
3. Obtain explicit approval for virtual environment/dependency installation and FastAPI file creation. Git initialization requires a separate explicit choice; it is not necessary for running the health probe.
4. Execute only the approved bootstrap and checks, report actual evidence in Arabic, then stop for owner review before S1-02.

## Planned files

- apps/api/pyproject.toml: minimal project/test configuration and reviewed dependency declarations.
- apps/api/requirements.lock and requirements-dev.lock: reproducible reviewed resolved dependencies; dev includes runtime plus pytest/httpx. Exact pins are selected after prerequisite review, not fabricated here.
- apps/api/app/main.py: composition only, local docs enabled, no SQLAlchemy import/DB settings requirement.
- apps/api/app/system/router.py: /api/v1/health/live and its small Pydantic response model; reject unsupported query input with the agreed sanitized error envelope. Do not add service/repository layers for a constant health response.
- Package __init__.py files only where necessary.
- apps/api/tests/test_health_live.py: liveness response/schema and no-DB independence, strict query rejection and OpenAPI route checks.
- README.md: actual approved run/test instructions and accurate status after success.

A root .venv is an ignored generated artifact, created only after approval. No actual .env is needed for this task. Preserve existing environment examples and SQL. No application files are created during the present planning phase.

## Proposed compatible version families — not installed or certified

| Component | Candidate | Decision boundary |
|---|---|---|
| Python | 3.12 latest supported patch | Proposed conservative compatibility target; inspect installed interpreter and package support first |
| FastAPI | Maintained stable 0.x release supporting Pydantic2/Python3.12 | Resolve exact minor/patch and pin after review; do not treat 0.x minors as automatically interchangeable |
| Pydantic | 2.x supported by selected FastAPI | Exact pin/resolution after compatibility review |
| Uvicorn, pytest, httpx | Maintained versions compatible with selected FastAPI/Starlette/Python | Resolve together and verify health tests; let FastAPI constrain Starlette, do not impose an unrelated Starlette override |
| Node.js / npm | Node24 LTS with its supported bundled npm | Prerequisite proposal for later web task only |
| Next.js / React / TypeScript | Next16, compatible React19 and TypeScript5 | Review exact supported pair when S3 begins; no frontend packages in S1-01 |
| Tailwind / shadcn/ui | Tailwind4 with the then-compatible shadcn CLI/components | Review S3 setup, pin reproducible tooling; no execution now |
| SQLAlchemy / Alembic / MySQL driver | SQLAlchemy2.x, compatible Alembic1.x, synchronous driver selected later | Deferred to S1-02/03; none needed for liveness |
| MySQL | Owner-specified MySQL8 | mysql --version checks client only; exported 8.0.34 is historical evidence, not live server verification |
| Git | Maintained installed Git2.x | Version check first; initialize only after explicit approval |

These are candidate families, not a tested dependency lock. At implementation time inspect current official compatibility/security guidance and present exact pins before installing. FastAPI recommends tested version pinning and allowing its Starlette dependency to resolve compatibly. [FastAPI version guidance](https://fastapi.tiangolo.com/deployment/versions/). Node release status and Next runtime requirements must be rechecked before S3. [Node releases](https://nodejs.org/en/about/previous-releases), [Next installation](https://nextjs.org/docs/app/getting-started/installation), [Pydantic installation](https://docs.pydantic.dev/latest/install/).

## Planned commands — NOT executed

Run prerequisite checks from repository root in PowerShell, only after task approval:

```powershell
py -0p
py -3.12 --version
node --version
npm --version
git --version
mysql --version
```

If a command is missing, report it; do not install automatically. mysql --version does not connect, check passwords or inspect server state. No mysql -u/-p, client login, service start, schema query, credential request, or MySQL installation is part of this task. Node/npm/MySQL client absence is recorded for later tasks; it does not necessarily block the Python-only health probe. An unavailable Python interpreter blocks bootstrap until an installation/version choice is approved.

Only if Git initialization is explicitly approved, from root:

```powershell
git init -b main
git status --short --untracked-files=all
git check-ignore -v --no-index apps/api/.env apps/web/.env.local
```

No stage/commit/remote/push is implied. Before initialization check whether another task/owner already created a repository; never reinitialize blindly.

After exact pins, lock-generation method and installation/bootstrap approval, and only once reviewed lockfiles exist, from root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r apps/api/requirements-dev.lock
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest apps/api/tests/test_health_live.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8000 --no-proxy-headers --no-access-log
```

Resolve dependencies with an owner-reviewed tool/method before the install block; exact resolver commands depend on approved pins/tool choice and must be shown before execution. Do not pretend nonexistent lockfiles are currently runnable. pyproject test configuration must make apps/api importable when tests run from root. No activation or execution-policy change is required. Uvicorn runs in a controlled local terminal; stop it after verification or explicitly report a retained process.

In a second local PowerShell terminal while the approved service is running:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/health/live
Invoke-RestMethod -Uri http://127.0.0.1:8000/openapi.json
```

Open http://127.0.0.1:8000/docs in a browser and verify the liveness operation. Unsupported query validation is covered by the test. Do not publish a tunnel or bind to all interfaces.

## Acceptance and stop condition

- Liveness returns HTTP200 with exactly {"data":{"status":"ok"}} and no settings/version/DB details.
- The only application operation is /api/v1/health/live; documentation/OpenAPI routes are local framework tooling, not extra business scope.
- Unknown liveness query input returns sanitized422 per draft contract; OpenAPI describes the response. Tests do not need MySQL or secrets.
- Startup and request handling do not construct DB sessions, connect, migrate, stamp or create tables.
- Record actual package versions, command exit/results, health/OpenAPI evidence and failures. A proposed command is never reported as executed.
- Git exists only if separately approved; no commits/remotes/push. Frontend/DB work remains unstarted.
- Report files changed and results in Arabic and await owner review. D02/D05/D18/companyos_test/provider choices remain pending and do not need to be silently resolved to finish liveness.
