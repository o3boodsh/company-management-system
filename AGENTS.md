# CompanyOS agent instructions

These rules govern future work. They do not authorize implementation during a documentation-only task. Read the applicable Phase 0 documents and decision register before acting; distinguish verified export facts, owner approvals, proposals and executed results.

1. **Explain before implementation in Arabic.** State the objective, proposed files, exact commands, expected results and relevant risks before every implementation task.
2. **Use small reviewable steps.** Follow the approved implementation backlog; make each step understandable and independently verifiable.
3. **Obtain owner approval before consequential commands.** Especially database creation/access, migrations/stamping, seed insertion, destructive changes/tests, deployment and Git remote operations. Git initialization, application bootstrap and dependency installation also require the relevant explicit approval. A database target decision is not execution authorization. Do not repeat a request for the same action when current explicit authorization already covers it.
4. **Preserve company_db unchanged.** Never use it for the app or tests, never import/relabel/convert its training records, and do not replay original SQL as setup.
5. **Use only separately approved isolated databases.** companyos_dev is the approved development target; its creation/connection/migration/fixtures remain separately gated. companyos_test remains proposed until explicitly confirmed, with separate execution approval for provisioning and destructive/integration testing.
6. **Teach the relevant concepts.** Explain technical decisions and applicable FastAPI, Pydantic, SQLAlchemy, SQL, React/Next.js, transaction, migration and security concepts in clear Arabic at the point they matter.
7. **Protect secrets.** Never expose credentials/tokens or commit real .env files, backups or personnel data. Use credential-free examples and redact diagnostics. Frontend public variables must contain no DB/provider secrets.
8. **Report after every task in Arabic.** List all files changed, exact commands actually executed, tests/results, failures, limitations and open issues; identify any running local process.
9. **Separate plans from evidence.** Never claim a proposed command/test/migration ran or passed. State when no implementation tests exist, checks were skipped, or live DB state is unknown.
10. **Stop for owner review before the next major task.** Finish currently authorized work, then await approval; do not treat backlog inclusion as permission to start the next task.
11. **Follow approved documents and notify the owner of necessary design changes.** Keep pending policies pending. Only explicit owner confirmation closes a decision. Preserve company_schema.sql and legacy SQL evidence. Alembic is the future schema authority; no startup create_all/migrate/stamp and no unapproved business tables/indexes.
12. **Prefer minimal understandable solutions.** Use the modular monolith, concrete feature layers and vertical slices; avoid speculative abstractions or scope expansion. Keep new MVP money USD, salaries monthly and budgets USD; do not infer training-record semantics.

For the current handoff, see [first coding task](docs/phase-1-start.md), [backlog](docs/implementation-backlog.md), [decisions](docs/open-decisions.md), and [readiness checklist](docs/phase-0-checklist.md). S1-01 has no MySQL connection. Real provider-backed authentication is required before any public business deployment; no production development-identity bypass.
