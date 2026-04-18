# Sprint 24 — Task List

## High Priority

- [ ] **TF-456: Fix WebSocket reconnection race condition** — RT collab fails to reconnect after network interruption; reconnect logic races JWT refresh, client retries w/ expired token. Assigned Alex Chen. Due Apr 11. Blocks enterprise demo Apr 14.

- [ ] **TF-489: Optimize dashboard query for large projects** — Dashboard >8s load w/ 500+ tasks. Missing composite index on `tasks(project_id, status, updated_at)` + N+1 in assignee resolution. Assigned Sam Rivera. Due Apr 9.

- [ ] **TF-501: Implement chunked file upload** — Attachments >10MB timeout on slow connections. Refactor upload endpoint for multipart chunked uploads w/ resume. Frontend: progress + cancel. Assigned Jordan Kim. Due Apr 15.

## Medium Priority

- [ ] **TF-478: Add Slack notification integration** — Notify configured Slack channel on task assignment/status change. Webhook infra ready; wire event handlers in task service + Slack message formatting. Assigned Jordan Kim. Due Apr 18.

- [ ] **TF-492: Fix timezone display for due dates** — Due dates show UTC instead of user's local timezone. Fix API response serialization (add tz to user profile) + frontend date utils; `formatDate` in `src/lib/dates.ts` needs timezone param. Assigned Maya Patel. Due Apr 16.

- [ ] **TF-503: Add keyboard shortcuts for common actions** — Shortcuts: new task (Ctrl+N), search (Ctrl+K), nav between views. Use centralized shortcut manager; consider `tinykeys` (700B gzipped). Assigned Maya Patel. Due Apr 20.

## Low Priority

- [ ] **TF-467: Update README with new architecture diagram** — Current diagram outdated; missing background job system + Redis cache layer. Update before open-source community call Apr 25. Unassigned.

- [ ] **TF-510: Investigate Playwright test flakiness** — E2E drag-and-drop reorder fails ~1/5 CI runs; likely animation timing issue. Not blocking; reduces test confidence. Unassigned.

- [ ] **TF-498: Clean up deprecated API endpoints** — v1 endpoints deprecated 3mo ago, safe to remove; frontend on v2. Endpoints: `GET /api/v1/tasks`, `POST /api/v1/tasks`, `PUT /api/v1/tasks/:id`. Unassigned.

## Completed This Sprint

- [x] **TF-445: Migrate from Webpack to Vite** — Completed Maya Apr 2. Build 45s→8s; HMR significantly faster.
- [x] **TF-451: Add rate limiting to public API endpoints** — Completed Alex Apr 3. `express-rate-limit` w/ Redis; 100 req/min authed, 20 unauthed.
- [x] **TF-460: Fix CORS configuration for staging environment** — Completed Sam Apr 1. Staging domain missing from allowed origins.
