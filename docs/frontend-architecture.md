# CompanyOS frontend architecture

Status: Proposed specification, 2026-10-12. No Next.js project or packages created. Stack: App Router, TypeScript, Tailwind CSS, shadcn/ui. Business rules and permissions remain authoritative in FastAPI.

Minimal apps/web now contains only a credential-free .env.example; all App Router/source paths below remain planned. New approved MVP salaries are monthly USD and budgets USD. Currency approval does not allow Viewer to see those amounts or authorize relabeling old training records.

## Proposed routes

| App Router path | User-facing URL | Purpose / API |
|---|---|---|
| app/(workspace)/layout.tsx | Shared shell | Navigation, responsive sidebar, session status; no business-data authorization solely here |
| app/page.tsx | / | Redirect to /employees for the first slice; eventual dashboard landing is a minor review choice |
| app/(workspace)/employees/page.tsx | /employees | Paginated employee listing |
| app/(workspace)/employees/new/page.tsx | /employees/new | Administrator create form |
| app/(workspace)/employees/[employeeId]/page.tsx | /employees/{id} | Detail, edit form/deactivate controls, paginated memberships |
| app/(workspace)/departments/page.tsx | /departments | List/counts and Administrator create form |
| app/(workspace)/departments/[departmentId]/page.tsx | /departments/{id} | Detail/edit; link to employee list filtered by department |
| app/(workspace)/projects/page.tsx | /projects | List and Administrator create form |
| app/(workspace)/projects/[projectId]/page.tsx | /projects/{id} | Detail/edit and paginated assignment controls |
| app/(workspace)/dashboard/page.tsx | /dashboard | Summary plus paginated department/project statistics |

Provider login/callback routes are unresolved, not implemented as business APIs. No delete UI for parent records, advanced permission UI, exports, payroll, or additional modules.

## Server versus Client Components

Server Components own layouts, static navigation, initial route parsing, and safe configuration boundaries. Client Components own interactive tables, URL-linked filters, pagination, forms, dialogs, and request state. The first slice uses client fetching directly from FastAPI, keeping unresolved SSR credential forwarding out of scope. Later server reads may use a server-only API client once per-user credential transport is approved; they must never use a shared privileged credential.

Next.js distinguishes server rendering from client interactivity; data crossing to Client Components must be serializable and safe to disclose. Explicitly disable caching for identity-dependent server reads. [Next.js Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components)

Proposed folders: features/employees, features/departments, features/projects, features/dashboard for UI concerns; components/ui for shadcn primitives; components/layout for shell; lib/api for transport; lib/contracts for TypeScript DTOs; lib/auth for a provider adapter selected later. No universal component factory or global state store is needed initially.

## API client and contracts

One API client handles configured base URL, URL encoding, approved credential injection, timeouts/cancellation, envelope decoding, request ID, and normalized errors. Separate browser/server entry points prevent server-only credentials leaking into bundles. Do not duplicate business validation in a Next.js API layer. Do not forward arbitrary incoming headers to FastAPI.

TypeScript contracts distinguish EmployeeViewer from EmployeeAdministrator and equivalent project projections; a single optional salary property is not permission enforcement. FastAPI OpenAPI is the later machine-readable source once implementation exists; generate or verify TS types against it during later setup, not now. Until then [api-contract.md](api-contract.md) is the draft source. Test JSON runtime shapes, not just TypeScript compilation.

Money remains a decimal string through forms/API. Display approved new-data salaries with USD/monthly; do not calculate with JS floating-point numbers or label training amounts. Budget displays USD for approved MVP data; do not display or infer legacy training budgets as USD. Dates remain YYYY-MM-DD strings, not timezone-shifted midnight Date objects.

List state uses URL query parameters matching the API. Debounce search and cancel stale requests; reset page when filters change. Under pending D18, Viewer fields exclude salary/email/hire_date/budget and monetary metadata; name-only search and ID/name sorts are available, with no email search or hire-date sort/filter controls. Administrator alone may use hire-date sorting. Backend must enforce this independently of the UI. Role-dependent action hiding is usability only; backend rejects forged requests. Nested rows use safe API summaries, not full employee payloads.

## Forms and state handling

Use client validation for quick feedback (required fields, lengths, date format, decimal strings), with Pydantic validation authoritative. No new validation library selected at this stage. Submit only editable fields, distinguish omitted PATCH fields from explicit null, and preserve input on validation/conflict failures. Prevent double-submit; do not automatically replay uncertain creates after network failure.

Loading: table/form skeleton or progress state without old identity's data. Empty: distinguish no records from no filter matches. 401: clear sensitive state and show session-required flow; 403: forbidden state; 404: entity not found; 409: actionable conflict; 422: safe field errors; 503/network: retry affordance without false empty results. Refresh affected lists/counts after confirmed mutations; no optimistic success for deactivation/assignment changes in the first MVP.

Each route has loading/error/not-found handling appropriate to its fetch path; Client Component errors must be handled locally rather than assuming route error boundaries catch every async request. Responsive shell supports keyboard navigation, focus visibility, labeled forms, accessible dialogs, narrow-screen tables/cards, and readable status labels. No sensitive values are embedded in page metadata or analytics.

Traceability: NFR-01/03/06, US-E01–E05, US-D01–D03, US-P01–P03, US-H01/S01. Vertical implementation remains S1–S9; see [first slice](first-vertical-slice.md).
