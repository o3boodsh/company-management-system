# CompanyOS open decisions

Status: Final Phase 0 planning review, 2026-10-12. **All new approved CompanyOS MVP monetary values are owner-confirmed USD: employee salaries are monthly USD; project budgets are USD.** D02 precision and D05 are approved in S1-04 (2026-10-13); unrelated policies remain pending. Source authoring/testing is authorized, not database execution. Minimal repository structure/documentation is authorized; application initialization, database execution, installation, and deployment are not.

## Owner confirmation record

| Item | Status | Approver / date | Scope and traceability |
|---|---|---|---|
| D02 currency | Approved: USD | Owner, explicit instruction in this conversation, 2026-10-11 | New approved MVP salary data; FR-E01/E03, US-E01/E03 |
| D02 payment period | Confirmed: monthly salaries for new MVP data | Owner, reconfirmed in final-planning instruction, 2026-10-12 | New approved MVP salary data; no payroll processing implied |
| D02 precision | Approved: DECIMAL(12,2), NOT NULL and nonnegative CHECK preserved | Owner, S1-04 instruction, 2026-10-13 | Source/tests authorized; database execution separately gated |
| D05 hire date | Approved: DATE NULL without current-date default; no backfill | Owner, S1-04 instruction, 2026-10-13 | Source/tests authorized; database execution separately gated |
| D21 development target | Approved: isolated companyos_dev; preserve company_db unchanged | Owner, explicit final-planning instruction, 2026-10-12 | Target decision only. Creation, connections, migrations and fixtures require separate implementation authorization; companyos_test remains proposed |
| D20 data boundary | Approved: no import, conversion, or relabeling of training records | Owner, explicit final-planning instruction, 2026-10-12 | New synthetic MVP data only; company_db never an application/test/migration target |
| D20 budget currency / MVP money scope | Approved: USD for all new approved MVP monetary values, including project budgets; salaries monthly USD | Owner, explicit repository-setup instruction, 2026-10-12 | FR-P01, US-P01; FR-E01/E03, US-E01/E03. No conversion or relabeling of training records |

Existing training salaries and budgets retain unverified original currency context; salary period is also unverified. Do not label old amounts USD, reinterpret salary periods, convert values, or infer provenance from IDs. Currency configuration is not a conversion. D20 currency and the no-import/no-conversion/no-relabeling boundary are approved. Historical provenance remains unknown and is not a prerequisite for the isolated new MVP dataset. See [database-design.md](database-design.md).

## Phase 0 decision summary

- Verified evidence: exported four-table baseline; no new live-state verification. Existing salary is DECIMAL(10,0), hire date has a current-date default, and assignments have a composite PK.
- Proposed database target: retain employee_status, use monthly DECIMAL(12,2) salary, keep email unique/optional and department/hire date optional, remove the hire-date default, deactivate employees, retain restrictive FKs and composite PK, and preserve all existing data. No speculative tables or indexes.
- Proposed access target: exactly Administrator and Viewer; omit salary/email/hire_date for Viewer and prefer Administrator-only budget. Real authentication on every public backend business endpoint; development stub only for local synthetic-data work.
- Proposed delivery target: S1–S9 vertical slices in [mvp-scope.md](mvp-scope.md), beginning with Employees GET API and connected listing; test each slice and complete real identity integration before public exposure.
- Confirmed: USD for new approved MVP salaries; monthly is the agreed design assumption. This does not confirm training-data semantics.
- Unresolved concrete choices: isolated test database approval, identity provider/session integration, Python backend host, managed MySQL provider, and Viewer field allowlist/budget visibility. Budget currency itself is approved USD.
- Approval state: D02 salary currency/period/precision, D05 hire-date default removal, D20 MVP currency and training-data preservation, and the D21 development target are confirmed. S1-04 sources/tests are authorized; unrelated policies and database execution remain unapproved.

## Established inputs

- User-specified: four MVP modules; specified full-stack technologies; monorepo; Vercel frontend with separate backend and managed MySQL; production authentication/authorization; salary privacy; documentation-only work at this stage; stated feature exclusions.
- Verified in [schema export](../database/company_schema.sql): four tables, existing names/types/nullability/defaults, three restrictive FKs, assignment composite PK, unique department/project names and nullable email, status/salary/budget checks.
- Not established: present live schema, actual rows, data quality, training-record currency/period, identity provider, production audience, hosting providers for backend/database, performance results, or compliance requirements.
- The user presented database policy choices as provisional. Existing schema behavior is evidence, not approval of its long-term business meaning.

## Decision register

| ID | Decision and consequences | One recommended default | Approval gate |
|---|---|---|---|
| D01 | Status naming: a rename affects API contracts, ORM mappings, and migrations. Constraint name `chk_employment_status` does not imply a column with that name. | Retain `employee_status` throughout the initial MVP; keep the working constraint name. | Before schema/API design sign-off |
| D02 | Partially confirmed: USD approved and monthly confirmed as the current design assumption for new approved salaries; precision DECIMAL(12,2) is approved in S1-04. Current DECIMAL(10,0) cannot represent fractions. | Configure salary currency USD and period monthly for new approved MVP data; use approved DECIMAL(12,2). Never convert or relabel existing training salaries. | Separate database execution authorization required; enforce confirmed D20 isolation before new-data use |
| D03 | Email optionality and normalization: requiring email would need existing-data remediation; uniqueness must respect DB collation. | Keep nullable unique email; trim input, normalize blank to NULL, validate nonblank values; preserve existing stored values pending review. | Before employee validation design |
| D04 | Department optionality: requiring assignments could force invented departments or data edits. | Retain nullable department and explicit Unassigned presentation. | Before employee/dashboard design |
| D05 | Approved in S1-04: hire date: current default can misrepresent unknown dates as today; existing dates may already be inferred but this is unverified. | Keep nullable DATE, remove current-date default through approved T2 source, store omitted date as NULL; never infer or erase existing dates. | Source approved; database execution separately gated |
| D06 | Status transitions and memberships: automatic membership deletion loses information; employment status is separate from account access. | Deactivate to Inactive while retaining assignments; block new Inactive assignments; allow Active/On Leave assignments, existing-role edits/removal, and reactivation via status update. | Before employee/project acceptance approval |
| D07 | Deletion surface: empty-department deletion adds a workflow; cascades would change data-retention behavior. | Retain restrictive FKs; no employee, project, or department deletion endpoint in first MVP. If empty-department deletion is desired, approve it explicitly while preserving referenced-department blocking. | Before scope/API sign-off |
| D08 | Name uniqueness and role cardinality: relaxing either changes keys or domain behavior. | Preserve globally unique department/project names and one assignment per pair with one nonblank free-text role; allow editing that role. | Before target-schema approval |
| D09 | Identity provider, two-role model, and Viewer allowlist: affects sensitive-data access and cross-origin sessions; concrete provider/session choice is unresolved. | A maintained managed identity provider with backend-verified identity and trusted Administrator/Viewer mapping. Administrator manages all four modules; Viewer reads allowlisted nonsensitive fields, never salary/email. No anonymous access, self-registration, extra roles, or permission editor. | Approve matrix before API design; select concrete provider/session design before S8 |
| D10 | Metric definitions: excluding inactive memberships can hide retained relationships; joins can double-count. | Total counts include all retained rows; Active is separate. Include Unassigned/zero groups. Show per-project membership, total assignment pairs, and distinct assigned employees with distinct labels. | Before dashboard acceptance approval |
| D11 | Existing-data preservation and baseline adoption: destructive replay risks loss; export/live drift is unknown. | Preserve all records, later verify current schema under explicit authorization, create a reproducible baseline for empty DBs, and stamp only a matching existing DB at that exact baseline revision after backup. | Before any DB connection, stamping, or migration work |
| D12 | Listing/search behavior: hidden-field search can disclose private information; unbounded lists undermine performance. | Bounded lists: page 1/size 20/max 100. Employee name search for Viewer; name/email for Administrator. Status/department filters and ID/name sorts, Administrator-only hire-date sorting, with ID tie-breaker and null dates last, subject to approved allowlists. Department/project default ID order. No salary/budget query features. | Before S2/S3 list/API contracts |
| D13 | Error and update semantics: inconsistent conflicts and retries confuse clients. | 401 unauthenticated, 403 forbidden, 404 missing, 409 integrity/state conflict, 422 invalid input; sanitized service failures. Partial updates preserve omitted values. Missing assignment removal returns 404. | Before API contracts |
| D14 | Concurrent edits: version checks add schema/API complexity; silent overwrites need explicit acknowledgment. | Accept last-write-wins for ordinary edits in this small MVP, refreshing after save; retain atomic DB constraints for uniqueness and relationships. Defer version-column optimistic locking unless concurrent editing becomes a requirement. | Before implementation sign-off |
| D15 | Real-data production obligations and auditing: organizational obligations may require retention/access auditing beyond current scope. | Use synthetic data for initial public portfolio release; no full audit-trail subsystem. Require explicit owner review before real personnel data is deployed; reopen scope if audit requirements arise. | Before deployment/data-use approval |
| D16 | Performance expectations: no owner-approved volume, load, hardware, or latency target exists. | Keep bounded queries and measure representative lists/dashboard on documented fixtures during slice verification; defer numeric thresholds until real expectations are known. No benchmark subsystem. | Before performance acceptance |
| D17 | Production backend and database hosting: concrete providers, region, cost, TLS/networking, backup ownership, and session origin topology are unresolved. | Separately host the Python/FastAPI service with managed MySQL near it and Vercel frontend; select compatible providers within the owner's budget later. No provider is selected here. | Before deployment design and S9; coordinate origins with D09 |
| D18 | Pending: project budget and employee-field visibility. No final field policy is approved by this planning instruction. | Recommend withholding salary, email, hire_date, project budget and monetary metadata from Viewer everywhere. Viewer employee fields: ID/name/status/department; safe memberships; department ID/name/count; project ID/name/start date/member count; dashboard counts. Disallow hidden-field search/filter/sort inference, including Viewer hire-date sorting. | Explicit owner approval of the complete allowlist before employee/API implementation |
| D19 | Delivery strategy: building all backend modules first delays end-to-end feedback; late tests hide integration problems. | Follow S1–S9 vertical slices, with role-aware contracts and tests from the first read slice, local synthetic identities until S8, and no public access until security gates pass. | Before implementation planning sign-off |
| D20 | Confirmed: all new MVP money is USD, salaries monthly and budgets USD. Preserve company_db; no import, conversion or relabeling of training records. Historical provenance is unknown. | Enforce the approved data boundary with newly authored synthetic fixtures in separately authorized environments. | Data boundary approved; database provisioning, fixtures and public data use still require their execution gates |
| D21 | Partially approved: isolated companyos_dev is the chosen development target; companyos_test remains proposed. Target approval is not creation authorization. | Later reviewed Alembic creation and synthetic fixtures in companyos_dev. Recommend separate disposable companyos_test, fail-closed identity/name guards, and localhost frontend 3000/API 8000/MySQL 3306. | Owner must approve companyos_test before provisioning/testing; separately authorize any DB connection, creation, migration or fixture command; ports/guards remain proposed |
| D22 | Wire contract details: endpoints, envelopes, queries, error semantics, nested projections, and bounded dashboard/assignment reads affect frontend integration. | Adopt the draft 23-operation /api/v1 contract and its common conventions after review; retain no parent DELETE endpoints. | Pending contract approval before implementation; does not close D06–D14/D18 |
| D23 | Authentication transport and frontend integration: bearer versus cookies affects CSRF, CORS, token storage, and authenticated server rendering. | First local slice uses direct Client Component API fetch and backend-configured development principal; prefer short-lived provider bearer tokens for public direct API access, subject to provider/session review. No provider selected. | Pending owner choice before public auth implementation; no production stub |

## Proposed minimum production permission matrix (D09)

| Capability | Anonymous | Viewer | Administrator |
|---|---|---|---|
| Employee allowlisted list/detail, excluding salary/email/hire_date | Deny | Allow pending field approval | Allow |
| Salary, employee email and hire_date read/write (D18 proposal) | Deny | Deny | Allow |
| Employee create/update/deactivate | Deny | Deny | Allow |
| Department/project/assignment allowlisted reads | Deny | Allow, excluding budget | Allow |
| Project budget read/write (D18 proposal) | Deny | Deny | Allow |
| Department/project/assignment writes | Deny | Deny | Allow within scope |
| Dashboard without salary aggregates | Deny | Allow | Allow |
| Application role assignment | Deny | Deny | Trusted provisioning outside MVP UI only |

Project assignment `role` is unrelated to application roles. Exactly two roles are proposed. D18 requires explicit owner approval; the preferred budget restriction is not a settled decision. Omit forbidden fields from nested memberships as well as top-level responses, and prevent Viewer searches from matching email and prohibit Viewer hire-date filters/sorts. Local identity stubs exercise these same permissions; public deployment requires a real identity provider and no bypass.

## Future database-design and adoption work

Recommended design order, subject to approval:

1. Approve policy decisions and preserve the original schema export as evidence.
2. Document SQLAlchemy metadata matching the existing schema exactly before introducing improvements. Map employee_projects as an association with its composite key and role; preserve named checks, keys, defaults, and collation.
3. Plan a baseline migration that creates the exported structure in an empty isolated database, with parents before child tables. Do not encode instance AUTO_INCREMENT counters as business requirements.
4. Plan salary precision and hire-date-default changes as separate reviewed revisions, only if approved. Preserve existing rows. Tighter nonblank checks require a later data-quality review first; do not silently clean data.
5. Plan current-schema verification, backups, restore rehearsal, and migration tests under separate authorization. Never run the export's DROP statements or practice mutations as the adoption workflow.
6. Historical contingency only, excluded from the selected companyos_dev backlog and prohibited on company_db under the confirmed preservation decision: for a verified matching existing database, plan stamping the specific baseline revision rather than replaying creation. Stamping writes migration metadata and therefore needs future authorization. New empty databases should be buildable through the baseline migration.
7. Review autogeneration manually, especially names, CHECK expressions, server defaults, decimal scale, and explicit renames. A generated empty diff is not sufficient evidence of complete equivalence. Define recovery for migration failure; do not assume a transaction can reverse every MySQL schema operation.

Target migration sources approved in S1-04; execution separately gated: salary DECIMAL(12,2) and removal of the hire-date expression default. Nonblank validation starts as an application requirement; a database check would need separate justification and data review. No new identity tables are proposed while provider selection is unresolved. Any concrete persistence need must return for design approval. No dashboard tables, assignment surrogate key, cascade changes, speculative indexes, or audit subsystem are added to the target. Alembic version metadata is an adoption mechanism, not a new business module.

## Approval recording and readiness

For each decision, record the chosen value, approver, approval date, and affected requirement/story IDs when the user approves it. D02 currency/period and D20 budget currency are recorded above. D02 precision and D05 source design are approved; D18, companyos_test and unrelated pending portions remain open. Database execution remains separately gated. companyos_dev creation is separately gated. Provider selections require concrete values, not placeholders.

Database Design deliverables: [current and target ERDs](erd.md), [data dictionary and mapping specification](database-design.md), and [migration adoption plan](database-migration-plan.md). These are review artifacts, not executable migrations.

System Architecture deliverables: [architecture](architecture.md), [API contract](api-contract.md), [security plan](security-plan.md), [frontend architecture](frontend-architecture.md), [deployment plan](deployment-plan.md), and [first vertical slice](first-vertical-slice.md). The current brief establishes design constraints (modular monolith, /api/v1, layers, Decimal, Alembic authority, DI sessions, no direct frontend DB access). D21 is partially approved as recorded above; remaining D21 details and D22–D23 remain proposals.

Minimal repository structure is now prepared; application setup remains future work. The final [implementation backlog](implementation-backlog.md), [first coding task](phase-1-start.md), and [readiness checklist](phase-0-checklist.md) are ready for review. Target-schema sign-off depends primarily on D01–D08 and D11; database setup and wire contracts remain D21/D22; provider/transport remains D09/D23. D22 refinement keeps 23 operations: assignment POST returns 201 plus its DTO, without Location; existing paginated collection reads remain the retrieval path. Production is blocked until security/provider/data-use decisions and release gates are satisfied. See [development workflow](development-workflow.md). No commits, remotes, pushes, or deployments are authorized automatically.

## S1-04 confirmation

Owner explicitly approved D02 precision and D05 on 2026-10-13. Source authoring and offline testing are authorized; no database provisioning, access, application or stamping is authorized. All unrelated decisions remain pending. Training records retain unverified monetary provenance and remain unchanged.
