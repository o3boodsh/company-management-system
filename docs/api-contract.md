# CompanyOS REST API contract

Status: Proposed contract for review, 2026-10-12. No endpoints are implemented. Policies D03–D10/D12–D14/D18 and new D22/D23 remain pending. USD/new-data monthly semantics are confirmed; salary precision and hire-date default changes are not executed. Examples use isolated synthetic data, never training records.

Owner clarification: all new approved MVP monetary values are USD; salary is monthly USD and project budget is USD. This changes currency metadata, not budget visibility approval. No conversion or relabeling of old training records is permitted. The API still has 23 operations after the assignment Location refinement.

## Common contract — applies to every endpoint

- Base prefix `/api/v1`; JSON snake_case. Breaking changes require a new major API version; additive fields must preserve security projections. Document OpenAPI later from Pydantic schemas. No executable OpenAPI artifact is generated now.
- Role A means Administrator; R means either Administrator or Viewer. Every business endpoint authenticates then authorizes before object lookup. Local stub may supply a principal only under the security plan. Liveness is the sole public nonbusiness exception.
- Request bodies use application/json objects. GET has **no JSON request body**, not `{}`; each GET example below states this. DELETE has no body. Unknown query/body fields, repeated scalar query keys, and invalid JSON/types yield sanitized 422. A method not offered yields 405; an unknown route yields 404.
- Common business errors: 401 missing/invalid credentials, 403 insufficient role, 422 invalid input, 503 unavailable persistence, 500 unexpected failure. Public abuse limiting may yield 429. Endpoint-specific errors add 404/409 below. No raw input values in errors.
- Positive signed-INT path/body IDs: 1–2,147,483,647; generated IDs are read-only. This is a proposed API domain, not proof about training IDs. Request IDs and monetary metadata are transport values, not new DB columns.
- List query P: page=1, page_size=20 (1–100). Response has data array and meta {page,page_size,total,total_pages}; zero matches yields data=[], total=0,total_pages=0; page beyond end also data=[] with actual totals. Default ascending ID, stable ID tie-breaker; unchanged dataset gives stable pages, not a snapshot across requests.
- Employees: q trimmed length 1–150 when supplied, literal substring search (escape SQL wildcard characters). search_in=name (default) or name_email; name_email is A-only, Viewer gets 403 even if q is absent. Filters employee_status exact canonical string; department_id positive ID or literal `unassigned`. sort=employee_id|full_name for Viewer; Administrator may also sort by hire_date; order=asc|desc, null dates last. Viewer sort=hire_date returns 403 before querying; no date-based inference. No implicit email search or hire-date filtering/sorting for Viewer. A well-formed nonexistent filter department returns empty results, not 404.
- Departments/projects: P only, fixed ascending parent ID. Assignment lists: P only, ordered by employee_id within project or project_id within employee. No speculative advanced filters. Stats lists: P only, parent ID order, Unassigned first on department distribution.
- PATCH is partial: absent leaves unchanged; explicit NULL clears only nullable fields. Reject empty PATCH and read-only/unknown keys. No PUT replacement. Last-write-wins remains D14 proposal. Parent hard deletion is not offered. Deactivation is repeat-safe; create requests are not automatically retry-safe.
- Dates are strict calendar YYYY-MM-DD, no timestamps/timezone conversion. Date-only values cannot be empty strings. Required text is trimmed/nonblank with schema length limits. Status is Active, Inactive, or On Leave. Email optional <=150, syntax checked, trimmed blank becomes NULL; non-NULL uniqueness follows MySQL collation. Check conflicts atomically.
- Money input/output is a decimal **string**, never JSON number: digits with optional dot and 1–2 fractional digits, no exponent/sign/comma/NaN/Infinity. Output has exactly two digits. Salary/budget are nonnegative and target maximum 9999999999.99. Baseline salary maximum 9999999999 and nonzero fractional values must be rejected until approved T1. No rounding or conversion. Required salary cannot be null; budget can.
- Target employee create omits hire_date → NULL only once approved T2 is applied. Until then, mutating target endpoints are gated rather than quietly trusting the old current-date default. First read slice remains valid on baseline. API startup/readiness must verify its required schema revision without running migrations.
- All business responses use Cache-Control: private, no-store. Single result envelope is {data:...}; collections use meta above. Employee, department, and project 201 creates include a Location header pointing to their existing GET detail URL. Assignment creation returns 201 with the created DTO and no Location header; use the existing paginated assignment GET collections for reads. No success is returned before commit. 204 has no JSON response.

Error example, used consistently across endpoints:

```json
{"error":{"code":"validation_error","message":"Request validation failed","details":[{"field":"salary","code":"invalid_precision","message":"Use the supported decimal precision"}],"request_id":"req-example-001"}}
```

Conflict codes include email_conflict, department_name_conflict, project_name_conflict, assignment_exists, inactive_employee, and reference_conflict. Do not reveal an existing record's values. Commit-time FK races return 409; an initially missing supplied parent returns 404. 401 invalid credentials and 403 forbidden use empty details arrays. Unknown server errors are generic.

## Role projections and reusable wire shapes

Proposed D18 Employee Viewer fields: employee_id, full_name, employee_status, department (null or {department_id,department_name}). Withhold hire_date, email, salary and financial metadata. Administrator adds hire_date, email, salary, salary_currency, salary_period. This restrictive recommendation is not owner-approved. Currency/period are configuration metadata only for the isolated approved dataset, not inferred per legacy row. Viewer never receives these financial/contact additions.

Department fields: department_id, department_name, employee_count. Project Viewer: project_id, project_name, start_date, member_count. Administrator adds budget and budget_currency; budget_currency is USD for approved MVP data, even when the optional budget amount is null; never inferred for training data. Assignment shape contains project_id, employee_id, role and safe employee {employee_id,full_name,employee_status}/project {project_id,project_name} summaries for both roles.

Detail pages fetch paginated assignments separately rather than returning unbounded nested arrays. This fulfills membership detail requirements with bounded requests. The examples below show Viewer reads and Administrator mutations unless marked otherwise. Admin employee GET example:

```json
{"data":{"employee_id":1,"full_name":"Demo Employee","employee_status":"Active","department":null,"hire_date":null,"email":null,"salary":"5000.00","salary_currency":"USD","salary_period":"monthly"}}
```

USD metadata is forbidden for training company_db; this API proposal targets companyos_dev/new approved data. If environments cannot guarantee the confirmed D20 isolation boundary, block access rather than display unverified money. In every nested response, hidden fields stay absent; generic search/count predicates cannot depend on hidden email. There are no salary/budget query features.

## Endpoint inventory

The numbered endpoint specifications below define all 23 operations. Common validations/errors apply in addition to each entry. Request examples are literal JSON where a body exists; bodyless operations instead show an example URL. IDs/results are illustrative, not seed instructions.

Implementation staging: S1-01 implements liveness only and must start without any DB connection or schema check. Required-revision checks apply when persistence/readiness is added in later separately approved tasks; they never mutate the schema.

### 01 — GET /api/v1/health/live

Parameters: none. Request: no JSON body; `/api/v1/health/live`. Role: none; operational liveness only. Response 200:
```json
{"data":{"status":"ok"}}
```
Rules: no DB or provider dependency, no version/configuration exposure; process failure may yield transport failure/503, not business data. Reject unsupported parameters (422). Trace: NFR-07; US-S01 operational support; no table.

### 02 — GET /api/v1/health/ready

Parameters: none. Request: no JSON body; `/api/v1/health/ready`. Role: R; an approved provider-backed operational identity can be used by probes. Response 200:
```json
{"data":{"status":"ready"}}
```
Rules: bounded read-only DB connectivity and required-schema-revision check; never create tables or stamp. Failure 503 uses common envelope with code not_ready and no DSN/details. Common auth/validation errors apply. Liveness remains available without credentials. Trace: NFR-07, US-S01; DB configuration/version metadata only.

### 03 — GET /api/v1/employees

Parameters: P and employee search/filter/sort above. Request: no JSON body; `/api/v1/employees?page=1&page_size=20&search_in=name&sort=employee_id&order=asc`. Role R. Response 200:
```json
{"data":[{"employee_id":1,"full_name":"Demo Employee","employee_status":"Active","department":null}],"meta":{"page":1,"page_size":20,"total":1,"total_pages":1}}
```
Rules: role projection; no salary/email/hire_date in Viewer response; counts use same allowed filters. Invalid query 422, forbidden search mode 403; empty results 200. Trace FR-E02/E06, US-E02/S01; employees, departments.

### 04 — GET /api/v1/employees/{employee_id}

Parameters: employee_id path only. Request: no JSON body; `/api/v1/employees/1`. Role R. Response 200:
```json
{"data":{"employee_id":1,"full_name":"Demo Employee","employee_status":"Active","department":null}}
```
Rules: projection above; assignments via endpoint 17. Missing employee 404. Trace FR-E03/E06, US-E03/S01; employees, departments.

### 05 — POST /api/v1/employees

Parameters: body only; full_name and salary required; email, department_id, hire_date optional nullable; employee_status optional default Active. Role A. Request:
```json
{"full_name":"Demo Employee","salary":"5000.25","email":null,"department_id":null,"hire_date":null,"employee_status":"Active"}
```
Response 201 after approved target migrations:
```json
{"data":{"employee_id":1,"full_name":"Demo Employee","employee_status":"Active","department":null,"hire_date":null,"email":null,"salary":"5000.25","salary_currency":"USD","salary_period":"monthly"}}
```
Rules: full_name <=100; all common field checks; never accept currency/period/ID from body. Missing department 404; email conflict 409; Viewer 403. No insert before target-schema and money-provenance gates. Trace FR-E01/E05/E06, US-E01/E05/S01; employees, departments; D02 precision/D05.

### 06 — PATCH /api/v1/employees/{employee_id}

Parameters: path ID; nonempty subset of create fields. Role A. Example `/api/v1/employees/1` body:
```json
{"full_name":"Demo Employee Updated","department_id":null}
```
Response 200:
```json
{"data":{"employee_id":1,"full_name":"Demo Employee Updated","employee_status":"Active","department":null,"hire_date":null,"email":null,"salary":"5000.25","salary_currency":"USD","salary_period":"monthly"}}
```
Rules: absent salary remains unchanged; full_name/salary/status cannot be null. Status to Inactive uses same logic as deactivate; Active can reactivate under D06. Existing memberships retained. Missing employee/department 404, duplicate email or FK race 409. Trace FR-E03/E04/E05/E06, US-E03/E04/E05/S01; employees.

### 07 — POST /api/v1/employees/{employee_id}/deactivate

Parameters: path ID, required empty JSON object; no other fields. Role A. Request body at `/api/v1/employees/1/deactivate`:
```json
{}
```
Response 200:
```json
{"data":{"employee_id":1,"full_name":"Demo Employee","employee_status":"Inactive","department":null,"hire_date":null,"email":null,"salary":"5000.00","salary_currency":"USD","salary_period":"monthly"}}
```
Rules: repeat leaves Inactive and returns 200; no hard delete/account revocation/membership removal. Missing employee 404, extra input 422. Lock/status policy D06 applies. Trace FR-E04, US-E04; employees, assignments preserved.

### 08 — GET /api/v1/departments

Parameters P. Request: no JSON body; `/api/v1/departments?page=1&page_size=20`. Role R. Response 200:
```json
{"data":[{"department_id":1,"department_name":"Engineering","employee_count":0}],"meta":{"page":1,"page_size":20,"total":1,"total_pages":1}}
```
Rules: include zero groups; count all employee statuses; Unassigned is not a fake department row and appears in dashboard distribution. Invalid P 422. Trace FR-D01, US-D02; departments/employees.

### 09 — GET /api/v1/departments/{department_id}

Parameters path ID. Request: no JSON body; `/api/v1/departments/1`. Role R. Response 200:
```json
{"data":{"department_id":1,"department_name":"Engineering","employee_count":0}}
```
Rules: browse members through employees?department_id=1; no unbounded nested list. Missing department 404. Trace FR-D01, US-D02, current requested detail contract; departments/employees.

### 10 — POST /api/v1/departments

Parameters body department_name required, <=100. Role A. Request:
```json
{"department_name":"Engineering"}
```
Response 201:
```json
{"data":{"department_id":1,"department_name":"Engineering","employee_count":0}}
```
Rules: trimmed nonblank, global uniqueness under DB collation. Duplicate 409; invalid name 422. Trace FR-D01, US-D01; departments.

### 11 — PATCH /api/v1/departments/{department_id}

Parameters path ID and required department_name (only writable field). Role A. Request at `/api/v1/departments/1`:
```json
{"department_name":"Product Engineering"}
```
Response 200:
```json
{"data":{"department_id":1,"department_name":"Product Engineering","employee_count":0}}
```
Rules: preserve ID/references; no deletion route, as proposed D07. Missing 404; duplicate 409; blank/null/long name 422. Trace FR-D01/D02, US-D01/D03; departments.

### 12 — GET /api/v1/projects

Parameters P. Request: no JSON body; `/api/v1/projects?page=1&page_size=20`. Role R. Response 200:
```json
{"data":[{"project_id":1,"project_name":"Demo Portal","start_date":"2026-11-01","member_count":0}],"meta":{"page":1,"page_size":20,"total":1,"total_pages":1}}
```
Rules: Viewer omits budget/currency; A adds them as in mutation examples; member counts include retained inactive memberships (D10). Invalid P 422. Trace FR-P01, US-P01; projects/employee_projects.

### 13 — GET /api/v1/projects/{project_id}

Parameters path ID. Request: no JSON body; `/api/v1/projects/1`. Role R. Response 200:
```json
{"data":{"project_id":1,"project_name":"Demo Portal","start_date":"2026-11-01","member_count":0}}
```
Rules: memberships via endpoint 16; no implicit sensitive nesting. Missing project 404. Trace FR-P01, US-P01; projects/employee_projects.

### 14 — POST /api/v1/projects

Parameters body project_name <=150 and start_date required; budget optional nullable default null. Role A. Request:
```json
{"project_name":"Demo Portal","start_date":"2026-11-01","budget":null}
```
Response 201:
```json
{"data":{"project_id":1,"project_name":"Demo Portal","start_date":"2026-11-01","member_count":0,"budget":null,"budget_currency":"USD"}}
```
Rules: future start allowed; unique/nonblank name. Budget validation above if supplied; new approved MVP budget amounts are USD; no conversion or relabeling of legacy budgets. Duplicate name 409; invalid date/budget 422. Trace FR-P01, US-P01; projects.

### 15 — PATCH /api/v1/projects/{project_id}

Parameters path ID, nonempty subset project_name/start_date/budget. Role A. Request at `/api/v1/projects/1`:
```json
{"project_name":"Demo Portal Revised","budget":null}
```
Response 200:
```json
{"data":{"project_id":1,"project_name":"Demo Portal Revised","start_date":"2026-11-01","member_count":0,"budget":null,"budget_currency":"USD"}}
```
Rules: only budget nullable; preserve assignment links; budget omitted unchanged. Missing 404; duplicate 409; invalid/empty patch 422. No project delete. Trace FR-P01, US-P01; projects.

### 16 — GET /api/v1/projects/{project_id}/assignments

Parameters path project ID, P. Request: no JSON body; `/api/v1/projects/1/assignments?page=1&page_size=20`. Role R. Response 200:
```json
{"data":[{"project_id":1,"employee_id":1,"role":"Developer","employee":{"employee_id":1,"full_name":"Demo Employee","employee_status":"Active"},"project":{"project_id":1,"project_name":"Demo Portal"}}],"meta":{"page":1,"page_size":20,"total":1,"total_pages":1}}
```
Rules: all memberships retained; no salary/email/hire_date/budget in nested summaries for either role. Parent absent 404; existing project with no assignments empty 200. Trace FR-P01/P02, US-P01/P02; all assignment parents.

### 17 — GET /api/v1/employees/{employee_id}/assignments

Parameters employee ID, P. Request: no JSON body; `/api/v1/employees/1/assignments?page=1&page_size=20`. Role R. Response 200:
```json
{"data":[{"project_id":1,"employee_id":1,"role":"Developer","employee":{"employee_id":1,"full_name":"Demo Employee","employee_status":"Active"},"project":{"project_id":1,"project_name":"Demo Portal"}}],"meta":{"page":1,"page_size":20,"total":1,"total_pages":1}}
```
Rules: same safe shape; sort by project ID. Missing employee 404, no memberships empty 200. Trace FR-E03/P02, US-E03/P02; employees/employee_projects/projects.

### 18 — POST /api/v1/projects/{project_id}/assignments

Parameters project ID; body employee_id and role required (role <=50 nonblank). Role A. Request at `/api/v1/projects/1/assignments`:
```json
{"employee_id":1,"role":"Developer"}
```
Response 201 with the created assignment DTO and **no Location header**. Read through GET `/api/v1/projects/1/assignments` or GET `/api/v1/employees/1/assignments`; PATCH/DELETE address the composite pair. No new GET-detail endpoint is introduced:
```json
{"data":{"project_id":1,"employee_id":1,"role":"Developer","employee":{"employee_id":1,"full_name":"Demo Employee","employee_status":"Active"},"project":{"project_id":1,"project_name":"Demo Portal"}}}
```
Rules: preserve composite PK; duplicate pair 409, not upsert; missing parent 404; Inactive employee 409 under D06; Active/On Leave eligible. Serialize eligibility with employee status changes. Trace FR-P02, US-P02; employee_projects/employees/projects.

### 19 — PATCH /api/v1/projects/{project_id}/assignments/{employee_id}

Parameters both path IDs; body role only. Role A. Request at `/api/v1/projects/1/assignments/1`:
```json
{"role":"Reviewer"}
```
Response 200:
```json
{"data":{"project_id":1,"employee_id":1,"role":"Reviewer","employee":{"employee_id":1,"full_name":"Demo Employee","employee_status":"Active"},"project":{"project_id":1,"project_name":"Demo Portal"}}}
```
Rules: do not change either ID; allow editing retained inactive membership under D06; role never grants auth. Missing pair 404; invalid role 422. Trace FR-P03, US-P03; employee_projects.

### 20 — DELETE /api/v1/projects/{project_id}/assignments/{employee_id}

Parameters both path IDs. Request: no JSON body; `/api/v1/projects/1/assignments/1`. Role A. Response **204 with no JSON body**. Rules: remove exactly the composite pair, preserve parents and other memberships; missing/repeated removal 404 under D13. FK/concurrent change conflict 409 where applicable. Trace FR-P03, US-P03; employee_projects only mutation.

### 21 — GET /api/v1/dashboard/summary

Parameters none. Request: no JSON body; `/api/v1/dashboard/summary`. Role R. Response 200:
```json
{"data":{"total_employees":1,"active_employees":1,"departments_count":1,"projects_count":1,"total_assignments":1,"distinct_assigned_employees":1}}
```
Rules: all retained employee rows count; Active only in active count; assignment pairs and distinct employees differ. Single read transaction for summary; no monetary aggregates. Empty DB returns all zeros. Trace FR-H01, US-H01; all four tables.

### 22 — GET /api/v1/dashboard/employees-by-department

Parameters P. Request: no JSON body; `/api/v1/dashboard/employees-by-department?page=1&page_size=20`. Role R. Response 200:
```json
{"data":[{"department_id":null,"department_name":"Unassigned","employee_count":1},{"department_id":1,"department_name":"Engineering","employee_count":0}],"meta":{"page":1,"page_size":20,"total":2,"total_pages":1}}
```
Rules: synthetic Unassigned group is always present, even count 0; not a table row. Include every department even empty; total means groups including Unassigned. Counts include all statuses and must not join-multiply memberships. Trace FR-H01, US-H01/D02; departments/employees.

### 23 — GET /api/v1/dashboard/project-memberships

Parameters P. Request: no JSON body; `/api/v1/dashboard/project-memberships?page=1&page_size=20`. Role R. Response 200:
```json
{"data":[{"project_id":1,"project_name":"Demo Portal","member_count":1}],"meta":{"page":1,"page_size":20,"total":1,"total_pages":1}}
```
Rules: include zero-member projects; counts include inactive members; no budget or employee contact data. No projects yields empty 200. Separate dashboard calls are not guaranteed to share a snapshot during concurrent writes. Trace FR-H01, US-H01; projects/employee_projects.

## Review gates

These 23 operations add no business entities. Department detail and system health are explicit additions requested in this architecture brief; dashboard breakdowns and assignment reads are bounded delivery of existing requirements. No parent DELETE, registration, custom auth endpoints, bulk operations, export, or audit feature is proposed. D22 records these wire-level choices as pending. [Security](security-plan.md), [transaction ownership](architecture.md), and [frontend](frontend-architecture.md) are part of this contract. Review projection/schema gates before implementation.
