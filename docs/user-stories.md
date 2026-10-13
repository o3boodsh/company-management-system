# CompanyOS user stories

Status: Draft for review, 2026-10-11. USD salary currency is approved and monthly is the owner-confirmed design assumption for new approved MVP data. D02 precision and other policies remain pending in [open-decisions.md](open-decisions.md).

Money provenance acceptance: display USD/monthly only for new approved MVP salary data only. Existing training salaries must not be relabeled, converted, or inferred from IDs. Their original currency/period remains unknown. No automatic conversion is part of any story. Project budgets are owner-confirmed USD for new approved MVP data (D20); legacy amounts remain unverified. See [database-design.md](database-design.md).

Priorities: **Must** is required for the stated milestone; **Conditional** depends on a scope decision. Production-security Must items remain mandatory even when a local prototype uses a development identity stub. Personas and proposed permissions are defined in [requirements.md](requirements.md).

## Vertical slice delivery and traceability — proposed D19

The S1–S9 sequence is defined in [mvp-scope.md](mvp-scope.md). Each slice must demonstrate its API-to-UI path and relevant validation/permission tests; S2 establishes the API before S3 connects its frontend. Tests use isolated synthetic MySQL fixtures. Local Administrator/Viewer identities may be stubbed, but field permissions are real application behavior from the first slice. US-S01 adds real production identity at S8 and is a public-release dependency, not a prerequisite for starting a local slice.

| Stage | Stories / requirements | Database entities | Slice completion |
|---|---|---|---|
| S1 | Foundation for all stories; NFR-01/02/07 | Exported baseline, isolated development DB | Connection/configuration and fixture strategy; no business-schema expansion |
| S2–S3 | US-E02 / FR-E02, FR-E06 | employees, departments for labels | GET API then connected listing; role-aware output, pagination, search, empty/error states |
| S4 | US-E01/E03/E04 / FR-E01/E03/E04 | employees; existing synthetic departments | Create/detail/update/deactivate forms persist via API; salary/date target changes only after approval |
| S5 | US-E05, US-D01–D03 / FR-E05, FR-D01/D02 | departments, employees.department_id | Department UI/API, employee picker, counts, deletion protection |
| S6 | US-P01–P03 / FR-P01–P03; US-E03 membership completion | projects, employee_projects, employees | Project/assignment UI/API, composite-key conflict handling, nested field protection |
| S7 | US-H01 / FR-H01 | All four tables | Dashboard API and interface; counts reconcile with fixtures |
| S8 | US-S01 / FR-E06, SEC-01–10 | Existing business tables; identity design unresolved | Real authenticated identities and approved permissions across every slice |
| S9 | Regression of all stories; NFR-06/07 | Approved baseline and migrations only | Release verification and approved deployment; no public access without S8 gates |

Later-stage integration assertions do not block earlier local demonstrations: use fixtures before create APIs exist, verify deactivation status before dashboard UI exists, and add membership presentation at S6. All deferred assertions must pass before declaring the complete MVP done.

## Shared validation and error contract

Proposed contract D13: invalid fields or list parameters produce validation errors (422); missing authentication produces 401; insufficient permission produces 403; unavailable records produce 404 after access checks; unique/referential/state conflicts produce 409; unexpected failures produce a sanitized service error. No raw SQL, credentials, sensitive input values, or stack traces are returned.

Reject unknown writable fields, invalid identifiers, blank required strings, excessive lengths, invalid dates, negative amounts, unsupported precision, and noncanonical status values. Database constraints remain the final arbiter for concurrent conflicts. A rejected mutation leaves no partial change. Permissions are checked before sensitive fields are disclosed. Omitted update fields remain unchanged; explicit NULL clears only optional fields. These criteria apply to every story.

## Employees

### US-E01 — Create employee

- Priority: Must, core/local and deployed MVP. Maps to FR-E01.
- Story: As an authorized administrator, I can create an employee so that the company directory has a reliable record.
- Acceptance: A valid full name, salary, and approved optional inputs create one employee with a generated ID. Missing status uses Active. Optional email/department/hire date follow D03–D05. New approved MVP salary data is explicitly presented as USD per month. Two-decimal salary support is accepted only after the precision change is approved and applied. No fixture/import silently reclassifies existing training salaries.
- Validation/errors: Reject blank/overlength name, invalid or duplicate email, negative/out-of-range/excess-precision salary, invalid status/date, and nonexistent department. Missing optional values are distinguished from empty strings. A user without compensation-write permission cannot create a salary-bearing employee through a forged request. Concurrent duplicate emails leave at most one matching non-NULL email.
- Dependencies: D01–D05, D09, D11, D13; schema baseline and any approved salary/date migration; US-S01 for deployed access.

### US-E02 — Browse employees

- Priority: Must. Maps to FR-E02.
- Story: As an authorized reader, I can locate employees using pages, search, filters, and sorting.
- Acceptance: Proposed defaults are page 1, size 20, maximum 100; return total matching count. Viewer searches name only; Administrator may search name/email. Combine with status/department filters and Unassigned. Name and ID sorts are available to Viewer; hire-date sort is proposed Administrator-only. All allowed sorts use a stable ID tie-breaker; default ID ascending, null dates last. Empty matches/out-of-range pages return an empty list. Proposed Viewer responses omit salary, email, and hire_date. At S3 the Next.js page consumes the real GET API with loading/empty/error states and functional controls.
- Validation/errors: Reject invalid page/size, unsupported fields, and invalid status. No salary search/sort/filter is supported. Viewer email search is unavailable: explicit email-query requests are forbidden and generic search never matches email. Test an email-only match yields no Viewer result or count change. Test duplicate names across page boundaries and no matches. A valid department filter without matches yields an empty result.
- Dependencies: S1 isolated fixtures, not US-E01 create functionality; D09, D12, D13, D18. US-S01 is required before public exposure. Pagination consistency is guaranteed for unchanged data, not a snapshot across concurrent edits.

### US-E03 — View and update employee

- Priority: Must. Maps to FR-E03.
- Story: As an authorized user, I can view permitted details; as an administrator, I can correct employee information.
- Acceptance: Detail shows proposed Viewer identity/status/department fields only. Hire date, salary and employee email appear only for Administrator under pending D18. Add project memberships at S6 without leaking hidden employee fields. At S4 the connected detail/edit form persists valid updates; omitted fields remain unchanged and optional fields can explicitly be cleared. Canonical status changes include Active, Inactive, and On Leave under D06.
- Validation/errors: Missing record gives 404. Invalid fields follow US-E01. An unauthorized salary update is rejected as a whole, even when other supplied fields are otherwise permitted. No mass assignment to ID or undefined fields. Overlapping edits follow the documented D14 default.
- Dependencies: S2/S3 and fixtures or US-E01; D03–D06, D09, D13, D14, D18. US-P02 supports later S6 membership integration, not initial S4 completion. US-S01 gates public exposure.

### US-E04 — Deactivate employee

- Priority: Must. Maps to FR-E04.
- Story: As an administrator, I can deactivate an employee while retaining their information.
- Acceptance: Deactivation changes status to Inactive, leaves the employee ID/record and assignments intact, and decreases the active count when the prior state was Active. Repeating deactivation has no further effect. No employee-delete action is exposed. Proposed reactivation uses the ordinary status edit; it creates no new employee.
- Validation/errors: Missing record gives 404; unauthorized change gives 403. Existing assignments remain visible with employee status. No new assignment to an inactive employee is accepted under D06. Employee deactivation does not promise to revoke an independent application account.
- Dependencies: D06, D07, D09; US-E03 at S4. Verify persisted status immediately; dashboard count integration is tested at S7 with US-H01. US-S01 gates public exposure.

### US-E05 — Set department

- Priority: Must. Maps to FR-E05.
- Story: As an administrator, I can assign, transfer, or clear an employee's department.
- Acceptance: A valid department is stored; transfer updates only the department relationship; clearing stores NULL under D04. Old/new department counts and Unassigned count reconcile after refresh.
- Validation/errors: Reject nonexistent department or employee. If a concurrent parent deletion invalidates the operation, return a conflict with no partial update.
- Dependencies: D04, D10, D13; US-D01, US-E01.

## Departments

### US-D01 — Create and rename department

- Priority: Must. Maps to FR-D01.
- Story: As an administrator, I can maintain department names.
- Acceptance: Nonblank trimmed names up to 100 characters create a generated ID or update the existing name without changing its ID or employee links.
- Validation/errors: Duplicate names under database collation return conflict; concurrent identical creates cannot create duplicates. Reject blank/overlength input. Missing update target gives 404.
- Dependencies: D08, D09, D13; US-S01.

### US-D02 — View departments and employee counts

- Priority: Must. Maps to FR-D01.
- Story: As a reader, I can see departments and their employee totals.
- Acceptance: List includes zero-employee departments. Proposed counts include Active, Inactive, and On Leave employees; labels state that meaning. Unassigned employees are shown separately rather than attributed to a department.
- Validation/errors: Empty database renders zero/empty states. Department counts must not multiply employees because of project joins.
- Dependencies: D10, D12; US-E05, US-D01.

### US-D03 — Protect department deletion

- Priority: Must for protection; no deletion workflow in the proposed MVP. Maps to FR-D02.
- Story: As an administrator, I cannot accidentally remove a department that employees still reference.
- Acceptance: Referenced departments cannot be deleted, regardless of employee status. Proposed D07 default exposes no deletion endpoint in the first MVP. Empty-department deletion would be a separately reviewed scope change, not a conditional implementation task in this backlog.
- Validation/errors: No supported DELETE operation or UI action; unsupported method returns 405 on an existing route. Restrictive FK behavior is tested only in the approved isolated test DB, with no employee deletion or detachment.
- Dependencies: D07, D13; US-D01, US-E05.

## Projects and assignments

### US-P01 — Maintain projects

- Priority: Must. Maps to FR-P01.
- Story: As an administrator, I can create and update projects; as a reader, I can list and inspect them.
- Acceptance: Connected project forms/list/detail use the API. Require nonblank name up to 150 characters and valid start date; allow future start date and optional nonnegative budget with at most two decimal places fitting DECIMAL(12,2). Proposed D18 makes budget Administrator-only; omit it from Viewer list/detail responses. Memberships show roles but no employee salary/email/hire_date to Viewer. Updates preserve omitted fields; explicit NULL clears budget. No project deletion workflow is exposed.
- Validation/errors: Duplicate name gives conflict; invalid date, negative/excess-precision budget, or missing required field gives validation error; missing project gives 404. Viewer cannot write budget or infer it through query parameters. Budget visibility requires explicit D18 approval.
- Dependencies: D07–D09, D12, D13, D18; US-P02 for populated membership detail within S6; US-S01 before public exposure.

### US-P02 — Assign employee with a role

- Priority: Must. Maps to FR-P02.
- Story: As an administrator, I can add an employee to a project with a defined project role.
- Acceptance: Existing eligible employee and existing project plus a nonblank role up to 50 characters create one assignment. Under D06, Active and On Leave employees are eligible; Inactive employees are not. Existing pair gives a conflict, not a second row or silent role replacement. Concurrent requests result in one assignment.
- Validation/errors: Missing parent gives 404; inactive employee or duplicate pair gives 409; blank/overlength role gives 422. Parent-removal races are safely rejected by constraints. Assignment role grants no application permissions.
- Dependencies: D06, D08, D09, D13; US-E01, US-P01; existing composite PK and FKs.

### US-P03 — Edit or remove assignment

- Priority: Must, with role edit proposed for review. Maps to FR-P03.
- Story: As an administrator, I can change a member's project role or remove their membership.
- Acceptance: Address assignments by both IDs. Role edit changes that pair only. Removal deletes only that assignment and preserves both parents. Existing inactive memberships can be edited or removed under D06. Membership counts reconcile after refresh.
- Validation/errors: Missing pair, including repeated removal, returns 404 under proposed D13; invalid role gives 422; unauthorized mutation gives 403. Removing one employee from a project does not affect their other assignments.
- Dependencies: D06, D08, D13; US-P02.

## Dashboard and deployed access

### US-H01 — View operational dashboard

- Priority: Must. Maps to FR-H01.
- Story: As an authorized reader, I can understand the current directory and project membership at a glance.
- Acceptance: Total employees counts all rows; Active counts only canonical Active status; departments/projects count all rows. Distribution includes zero-member departments plus Unassigned. Project statistics show members per project, total assignments, and distinct assigned employees, clearly distinguished. Membership counts include retained inactive memberships under D10. Empty database yields zeros. Refresh after a mutation reflects persisted data. No salary totals, averages, or other salary aggregates appear.
- Validation/errors: Fixtures include unassigned employees, inactive employees, one employee on multiple projects, and projects with no members. Avoid join multiplication. Failed loading shows an error rather than false zero counts. No live real-time consistency guarantee across separate concurrent reads is implied.
- Dependencies: D06, D09, D10; US-E04/E05, US-D02, US-P03; US-S01 for deployed access.

### US-S01 — Enforce deployed access and sensitive-field privacy

- Priority: Must before any public deployment; field-policy tests begin in each local slice. Maps to FR-E06 and SEC-01–10.
- Story: As the company owner, I require authenticated users and enforced permissions so employee data is not public.
- Acceptance: Exactly Administrator/Viewer permissions follow proposed D09/D18. Anonymous access to every public backend business endpoint fails. Viewer reads approved fields, cannot mutate, and receives no salary/email/hire_date, including nested responses. Budget is proposed Administrator-only. Administrator manages all four modules. Invalid/expired/revoked sessions fail. S8 replaces local identity stubs with real provider integration without removing permission checks. Direct requests and shared caches cannot bypass restrictions. Production fails closed if real authentication is absent or a development stub is enabled.
- Validation/errors: Verify missing/invalid credentials, insufficient role, forged sensitive writes, forbidden email queries, hidden-field inference, nested serialization, unauthorized mutation, logout/revocation, and error/log redaction. Test the connected frontend with both real roles before public deployment. Application role cannot be self-assigned. Role changes take effect within the approved session policy. Cookie authentication, if selected, includes CSRF testing.
- Dependencies: D09, D15, D17, D18; concrete identity-provider/session and hosting choices; all business endpoints. No authentication is implemented by this documentation task.
