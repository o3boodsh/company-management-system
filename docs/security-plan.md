# CompanyOS security and authentication plan

Status: Proposed specification, 2026-10-12. No provider chosen or authentication implemented. D09/D18 and new D23 remain pending. Public business endpoints require real authentication as directed by the owner; local completion is not public readiness.

Currency approval is separate from access approval: all new approved MVP money is USD (salary monthly, budget USD), but Viewer still receives no salary, email, hire_date, budget, or corresponding monetary metadata under the proposed projection. Do not convert or relabel legacy training salaries/budgets. Provider, hosting, and final permission decisions remain pending.

## Identity boundary

FastAPI resolves a principal containing a stable provider subject and trusted application role. Proposed roles are exactly Administrator and Viewer. Never derive role from an employee record, employee_projects.role, email domain, request body, arbitrary header, or editable provider user metadata. Provision initial roles outside the MVP UI using a trusted provider/admin mechanism; exact mapping awaits provider review. No account/permission business tables are proposed.

Provider-backed verification must check token signature with approved algorithms and trusted keys, issuer, audience, expiry, not-before, and intended token type; opaque tokens require the selected provider's supported verification/introspection path. Unknown/disabled subject or missing/unknown role fails closed. Reject stale/revoked credentials within a documented provider-backed session policy. No fallback to a local principal after verification failure. Key fetch/introspection failures never grant access; define bounded retries/cache lifetimes during provider integration. Login/logout/callback endpoints depend on that decision and are deliberately not invented in the business API contract.

## Local development identity proposal

Only when APP_ENV is local or test, dataset is synthetic, service binds to loopback, and AUTH_MODE is explicitly development-stub: a backend setting DEV_IDENTITY_ROLE selects Administrator or Viewer and a fixed synthetic subject. Default Viewer. Switching roles requires trusted local configuration/restart or a test dependency override; no browser-selectable role header or public identity endpoint. It bypasses real identity verification only, not authorization/projections. No secrets or real personnel data belong in fixtures. Artificial salaries, emails, hire dates and budgets are required to test projection safety; use only newly authored synthetic values.

Startup must reject development-stub mode in staging/production, missing real-auth settings, invalid role mapping, or a known training database target. Do not trust Host or forwarded headers alone to establish “localhost.” Deployment configuration must independently disallow stub mode and public exposure. Tests prove disabled stub access in public configurations. The synthetic header-based alternative is not part of this proposal.

Local Uvicorn commands must bind to loopback and explicitly use --no-proxy-headers; use --no-access-log to avoid logging sensitive query strings. Uvicorn proxy processing can otherwise rewrite ASGI client addresses from forwarding headers. The local stub boundary therefore assumes proxy processing is disabled and no public proxy/tunnel/preview reaches the service. These flags never authorize public stub exposure. Real provider verification and approved proxy trust settings are separate future release work. S1-02C tests this boundary with Uvicorn's ASGI wrapper inside TestClient, without an external server or new shipped identity endpoint.

## Proposed permission and projection matrix

| Surface | Administrator | Viewer |
|---|---|---|
| Employees read | Approved fields including salary/email | ID, name, status, department only; exclude hire_date under pending D18 recommendation |
| Employee writes/deactivate | Allow | Deny whole request |
| Department reads | Allow | Allow |
| Department create/update | Allow | Deny |
| Project reads | Include budget and budget_currency USD for approved MVP data | Omit budget and budget_currency by proposed D18 default |
| Project/assignment writes | Allow | Deny |
| Assignment/nested summaries | Safe parent summaries | Same safe summaries; no salary/email/hire_date/budget |
| Dashboard | Counts only | Counts only |

Build allowlisted DTOs before serialization. Omit forbidden keys entirely rather than send NULL placeholders. Never send hidden data to the browser and rely on CSS. Every nested projection uses a purpose-specific safe summary, even for Administrator, avoiding deep cyclic ORM serialization. Dashboard exposes no money aggregates or employee email. All business paths require the backend's known role; a valid identity with no mapped role gets 403.

Viewer generic employee search matches names only; Administrator may match name/email. A Viewer request for search_in=name_email or sort=hire_date gets 403 before querying. Unsupported sensitive filters/sorts get a sanitized 422 without querying those fields. Counts use exactly the permitted predicates. Test hidden email/hire-date changes cannot change Viewer name-search results, order or counts. No salary/budget filters or sorting are offered to either role in the MVP.

## Authentication transport decision — unresolved D23

For the first local slice, browser Client Components call FastAPI directly with the configured synthetic principal; there are no credentials. Proposed public transport is short-lived provider-issued bearer access tokens sent to FastAPI, with a supported authorization-code/PKCE login flow. This is a recommendation, not a selected provider or approved final transport. Prefer memory/provider-managed storage over custom persistent browser token storage. Do not invent a refresh-token implementation.

If bearer transport is selected, backend business endpoints must not also silently authenticate via cookies; browser-supplied Authorization is not an ambient cookie, but provider login/callback still needs state/nonce/PKCE and XSS protection. Client token acquisition and Server Component authenticated reads depend on the chosen SDK. Keep business data client-fetched until secure server token forwarding is designed; do not fake SSR authentication with a shared Administrator token.

If HttpOnly cookie transport is selected instead, require Secure and appropriate SameSite/domain/path settings, CSRF tokens plus origin validation for state-changing requests, safe login/logout, and an explicit cross-site deployment plan. Cross-origin fetch needs credentials handling and exact allowed origins. A Next.js session/proxy adapter is optional only if the chosen provider needs it; it must not duplicate business services or hold an all-powerful shared identity. Resolve the transport before public implementation.

Document session lifetime, renewal, logout/revocation, role-change propagation, cookie policy, and account disablement after provider selection. Employment deactivation does not revoke an unrelated application account. No numeric session lifetime is silently approved here.

## CORS, caches, errors, and operations

CORS allowlists exact frontend origins; never reflect arbitrary origins or combine credentialed access with wildcard origins. Allow only required methods/headers. CORS preflight may be unauthenticated, but cannot access business data. Server-to-server calls and non-browser clients still require real authentication; CORS does not authorize them. [FastAPI CORS guidance](https://fastapi.tiangolo.com/tutorial/cors/)

Authenticated API responses use Cache-Control: private, no-store. Disable shared Next.js/CDN/static caches for user data; do not serialize tokens or forbidden fields into Server Component payloads. Clear client data on identity/role changes and logout. Do not key caches solely by URL if auth state could differ. Avoid personal values in URLs/logs; redact employee search text where it may contain email.

Normalize 401/403/404/409/422 errors without raw validation inputs, SQL, constraint internals, credentials, or existing sensitive values. Add a safe request ID. Log operational metadata, not bodies or Authorization/Cookie headers. Use TLS, least-privilege runtime DB credentials, separate migration access, bounded request/query sizes, and basic abuse controls before public release. Specific rate thresholds depend on hosting; no Redis/rate-limit business table is required now.

## Public-release security acceptance

- Real identities for both roles; no anonymous business access, forged role headers, expired/wrong-audience tokens, role self-assignment, or enabled local stub.
- Direct API tests and UI tests cover mutations, nested projections, forbidden search, revoked sessions, error redaction, and role/cache switching.
- D18 exclusion of salary/email/hire_date/budget explicitly reviewed and approved; provider/session/hosting/origins resolved.
- Liveness exposes only generic status. Readiness exposes no DSN/server/schema details and is authenticated; operator probes follow the contract.
- Synthetic public demo data only unless real-data handling is separately approved. Legacy salary provenance is never inferred from USD configuration.

Traceability: SEC-01–10, FR-E06, US-S01, D09/D15/D17/D18/D20/D23. See [deployment gates](deployment-plan.md) and [API projections](api-contract.md).
