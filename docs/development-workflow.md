# CompanyOS development workflow

Status: Phase 0 setup/refinement, 2026-10-12. Minimal structure and documentation only. No applications, dependencies, Git repository, databases, or deployment have been initialized by this task.

## Git conventions — proposed working defaults

Initialize Git only when the owner runs or authorizes it. Suggested commands are in [README](../README.md). Use main as the integration branch and short focused branches such as docs/api-contract or feat/employees-list. Prefer one reviewable vertical slice per branch and concise imperative commit messages describing behavior. A PR should state the problem, resulting behavior, validation actually performed, unresolved decisions, and any data/schema impact. No automatic commits, remotes, pushes, or merges.

Before staging, inspect status and diff, check the ignore rules, and scan for credentials or personal data. Stage intended paths selectively. Track dependency lockfiles and reviewed migrations once they exist. Do not track .env files, venvs, node_modules, builds, logs, production dumps, or backups. `.env.example` must remain credential-free. Existing schema-only and practice SQL are intentional evidence, not disposable dumps.

## Vertical slices and approval boundaries

Follow S1–S9 in [scope](mvp-scope.md): foundation → Employees GET → connected listing → employee mutations → departments → projects/assignments → dashboard → production identity → release verification. Build relevant backend/API/frontend/test behavior together. Test from the first slice rather than deferring all quality work to S9.

The first coding task is [phase-1-start.md](phase-1-start.md), a no-database subset of [first-vertical-slice.md](first-vertical-slice.md), but this setup task does not authorize initialization or execution. D21 companyos_dev target is owner-approved; creating it needs separate approval. companyos_test remains proposed and cannot be used or provisioned without confirmation. Keep company_db unchanged; use new synthetic records only in future authorized development/test environments. Tests must refuse training/production targets.

Owner-approved money semantics: all new approved MVP money is USD, salaries monthly and budgets USD. Do not convert or relabel training amounts. Currency approval does not approve precision/default migrations, access-policy details, provider selection, or database provisioning. Record approvals granularly in [open-decisions.md](open-decisions.md).

## Review and API consistency

Treat [api-contract.md](api-contract.md) as the draft wire contract until implemented OpenAPI is reviewed. Use `/api/v1` consistently; frontend route URLs are separate from backend endpoints. Request department_id maps to a nullable department summary in response; IDs and currency metadata are read-only. Decimal amounts remain JSON strings. Role DTOs and nested summaries omit forbidden data server-side.

All collection endpoints use page/page_size and matching meta; no unbounded nested membership lists. The dashboard's Unassigned group is derived, not a database row. Assignment POST returns 201 and its created DTO without Location. Read via the existing project/employee assignment collections; edit/remove via the composite pair. Do not add a new endpoint solely to repair the old header.

Review changes against requirement/story IDs, schema facts, approvals, and production implications. Reject undocumented automatic defaults, training-data assumptions, arbitrary role headers, and hidden-field inference. Hosting and identity choices remain open; no provider is picked to make a document look complete.

## Tests and verification

- Documentation changes: verify links, examples, endpoint/DTO consistency, decision status, and preservation of SQL evidence. Secret scans are bounded checks, not proof that no secret can ever exist.
- First read slice: verify real FastAPI/MySQL/listing integration, bounded pagination/search/filter/sort, safe projections, isolated fixtures, and session cleanup. Test both local roles without a public role-switch endpoint.
- Mutation slices: unit-test business rules and integrate against MySQL 8 for FK/unique/CHECK behavior, composite-key races, rollback, and deactivation/assignment concurrency. A SQLite-only test does not establish MySQL compatibility.
- Frontend: relevant type/build/lint checks, forms, loading/error/empty states, keyboard behavior, sensitive-data absence, and API contract examples.
- Public release: direct-API auth tests, real identity/role revocation, no production stub, safe caching/CORS/session handling, reviewed migrations, and backup restore evidence.

Run only checks supported by existing code/tooling. There are currently no application tests or package commands to run; documentation checks are the present validation. Add reproducible commands when their implementations exist. Do not label a proposed test as passed.

## Alembic and persistence authority

Alembic is the only schema-change authority; never create tables, migrate, or stamp on startup. Follow [migration plan](database-migration-plan.md): reviewed B0 baseline for fresh environments; verified equivalence plus authorized exact-baseline stamp for an existing environment only if separately approved. The owner confirmed preservation of company_db and a separate companyos_dev target. Existing populated-database adoption remains a reference contingency, not the selected execution path.

T1 salary DECIMAL(12,2) and T2 hire-date-default removal remain proposed. Preserve existing names, four business tables, restrictive FKs, indexes, checks, and assignment composite PK. No speculative new tables/indexes. Back up and rehearse restore before any future populated-database change. Schema-only exports cannot recover rows; MySQL DDL recovery is not a blanket transaction rollback.

Mutations have one service-owned commit/rollback boundary; repositories never commit. No accidental ORM cascade deletion or FK nulling. Runtime/migration credentials stay separate and out of Git. Installation, provisioning, migrations, and database tests require the appropriate later authorized scope.

## Definition of Done

For a reviewed slice: approved blockers resolved, linked acceptance criteria met, intended API/UI behavior demonstrated, relevant tests actually passed, failures/conflicts safe, permissions enforced, docs/contracts synchronized, no unrelated scope changes, no secrets or training-data damage, and a concise reviewer-facing report.

Local Done explicitly identifies stub identity and remaining production gates. Public Done requires real authentication and backend authorization before exposing business endpoints, including previews. Currency approval and a successful local demo are not deployment approval.

## Present handoff

Minimal folders and safe examples exist; apps are not runnable. Git initialization remains an owner action. The [final backlog](implementation-backlog.md) covers pending decisions and small implementation tasks. Follow [AGENTS.md](../AGENTS.md): Arabic explanations before execution, actual command/result reporting afterward, and owner review before each next major task. Wait for approval before S1-01.
