# Terminal 1 — Web Dashboard (FastAPI Backend + React SPA)

> **Scope:** Full web dashboard with REST API, real-time WebSocket updates, and React frontend
> **New packages:** `src/signalops/api/`, `dashboard/`
> **Touches existing:** `pyproject.toml`, `database.py` (add relationships)
> **Depends on:** None (fully isolated until Phase 3 integration)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Phase 1 — FastAPI Backend Foundation](#2-phase-1--fastapi-backend-foundation)
3. [Phase 2 — React Frontend](#3-phase-2--react-frontend)
4. [Phase 3 — Integration & Real-Time](#4-phase-3--integration--real-time)
5. [Phase 4 — Polish & Tests](#5-phase-4--polish--tests)
6. [File Manifest](#6-file-manifest)
7. [API Endpoint Reference](#7-api-endpoint-reference)
8. [Testing Plan](#8-testing-plan)

---

## 1. Overview

The web dashboard replaces the CLI approval queue with a browser-based interface.
Users can browse leads, approve/edit/reject drafts, view analytics, and monitor
pipeline runs in real time. The backend is a FastAPI app that shares the same SQLite/Postgres
database as the CLI. The frontend is a Vite + React + TypeScript SPA.

**Key design decisions:**
- FastAPI backend is a **separate entry point** (`signalops-api` command), not embedded in Click
- Shares the same SQLAlchemy models and database — no data duplication
- API-key auth for MVP (expandable to OAuth later)
- WebSocket for real-time pipeline progress and queue updates
- React SPA with Tailwind CSS, consistent with landing page design system

---

## 2. Phase 1 — FastAPI Backend Foundation

### Step 1: Project Setup

**Create `src/signalops/api/__init__.py`:**
```python
"""FastAPI web dashboard backend for SignalOps."""
```

**Create `src/signalops/api/app.py`:**
- FastAPI application factory pattern
- CORS middleware (allow localhost:5173 for Vite dev, configurable origins)
- Include all route modules
- Lifespan handler for DB engine initialization
- Exception handlers for SignalOps custom exceptions

```python
# Key structure:
def create_app(db_url: str = "sqlite:///signalops.db") -> FastAPI:
    app = FastAPI(title="SignalOps API", version="0.3.0")
    app.add_middleware(CORSMiddleware, ...)
    app.include_router(projects_router, prefix="/api/projects", tags=["projects"])
    app.include_router(leads_router, prefix="/api/leads", tags=["leads"])
    app.include_router(queue_router, prefix="/api/queue", tags=["queue"])
    app.include_router(stats_router, prefix="/api/stats", tags=["stats"])
    app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])
    app.include_router(experiments_router, prefix="/api/experiments", tags=["experiments"])
    return app
```

**Create `src/signalops/api/deps.py`:**
- `get_db()` — yields SQLAlchemy Session (FastAPI Depends pattern)
- `get_current_project()` — resolves active project from query param or header
- `get_config()` — loads ProjectConfig for current project
- `require_api_key()` — validates `X-API-Key` header

```python
# Key dependency functions:
def get_db(request: Request) -> Generator[Session, None, None]:
    engine = request.app.state.engine
    session = get_session(engine)
    try:
        yield session
    finally:
        session.close()

def require_api_key(x_api_key: str = Header(...)) -> str:
    expected = os.environ.get("SIGNALOPS_API_KEY", "")
    if not expected or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
```

**Create `src/signalops/api/auth.py`:**
- API key validation
- Optional JWT token generation/validation (for future OAuth)
- Rate limiting middleware for API endpoints

**Create `src/signalops/api/schemas.py`:**
- Pydantic response models (read-only, separate from config schemas)
- `ProjectResponse`, `LeadResponse`, `DraftResponse`, `StatsResponse`, etc.
- Pagination model: `PaginatedResponse[T]` with `items`, `total`, `page`, `page_size`

```python
class LeadResponse(BaseModel):
    id: int
    platform: str
    platform_id: str
    author_username: str | None
    author_display_name: str | None
    author_followers: int
    text_original: str
    text_cleaned: str
    created_at: datetime
    score: float | None
    judgment_label: str | None
    judgment_confidence: float | None
    draft_status: str | None

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int
```

### Step 2: Route Modules

**Create `src/signalops/api/routes/projects.py`:**
```
GET  /api/projects                — List all projects
GET  /api/projects/{id}           — Get project details
GET  /api/projects/{id}/config    — Get project config (sanitized, no secrets)
POST /api/projects/{id}/activate  — Set active project
```

**Create `src/signalops/api/routes/leads.py`:**
```
GET  /api/leads                   — List leads with filtering/pagination
     Query params: project_id, min_score, max_score, label, sort_by, page, page_size
GET  /api/leads/{id}              — Get lead detail (post + judgment + score + draft)
GET  /api/leads/top               — Get top N leads by score
```

**Create `src/signalops/api/routes/queue.py`:**
```
GET    /api/queue                  — List pending drafts
GET    /api/queue/{id}             — Get draft detail
POST   /api/queue/{id}/approve     — Approve draft
POST   /api/queue/{id}/edit        — Edit and approve draft (body: {"text": "..."})
POST   /api/queue/{id}/reject      — Reject draft (body: {"reason": "..."})
POST   /api/queue/send             — Send all approved drafts
POST   /api/queue/send-preview     — Preview what would be sent (dry-run)
```

**Create `src/signalops/api/routes/stats.py`:**
```
GET  /api/stats                   — Pipeline stats (collected, judged, scored, drafted, sent)
GET  /api/stats/timeline          — Stats over time (daily/weekly/monthly buckets)
GET  /api/stats/outcomes          — Outcome breakdown (reply rate, like rate, follow rate)
```

**Create `src/signalops/api/routes/analytics.py`:**
```
GET  /api/analytics/score-distribution   — Histogram of lead scores
GET  /api/analytics/judge-accuracy       — Precision/recall from human corrections
GET  /api/analytics/query-performance    — Which queries produce best leads
GET  /api/analytics/persona-effectiveness — Draft approval rates by persona/template
     (NOTE: derives persona from the `tone` and `template_used` columns on the drafts table;
      there is no separate `persona_name` column)
GET  /api/analytics/conversion-funnel    — Collected → Judged → Scored → Drafted → Sent → Outcome
```

**Create `src/signalops/api/routes/experiments.py`:**
```
GET    /api/experiments              — List A/B experiments
GET    /api/experiments/{id}         — Experiment detail with results
POST   /api/experiments              — Create new experiment
POST   /api/experiments/{id}/stop    — Stop experiment
GET    /api/experiments/{id}/results — Statistical comparison
```

### Step 3: CLI Entry Point

**Update `pyproject.toml`:**
```toml
[project.scripts]
signalops = "signalops.cli.main:cli"
signalops-api = "signalops.api.app:main"
```

**Add `main()` function to `app.py`:**
```python
def main() -> None:
    """Run the SignalOps API server."""
    import uvicorn
    uvicorn.run(
        "signalops.api.app:create_app",
        factory=True,
        host="0.0.0.0",
        port=8400,
        reload=True,
    )
```

### Step 4: Database Relationships

**Update `src/signalops/storage/database.py`:**
- Add SQLAlchemy `relationship()` declarations for efficient eager loading
- Add `relationship("NormalizedPost", ...)` to `RawPost`
- Add `relationship("Judgment", ...)` and `relationship("Score", ...)` to `NormalizedPost`
- Add `relationship("Draft", ...)` to `NormalizedPost`
- Add `relationship("Outcome", ...)` to `Draft`
- These are non-breaking additions (no schema migration needed)

```python
# Example additions to NormalizedPost:
class NormalizedPost(Base):
    # ... existing columns ...
    judgments = relationship("Judgment", backref="normalized_post",
                             foreign_keys="Judgment.normalized_post_id")
    scores = relationship("Score", backref="normalized_post",
                          foreign_keys="Score.normalized_post_id")
    drafts = relationship("Draft", backref="normalized_post",
                          foreign_keys="Draft.normalized_post_id")
```

---

## 3. Phase 2 — React Frontend

### Step 5: Scaffold React App

```bash
cd C:\GitHubProjects\Syntrix
npm create vite@latest dashboard -- --template react-ts
cd dashboard
npm install
npm install tailwindcss @tailwindcss/vite
npm install react-router-dom
npm install recharts                    # Charts
npm install @tanstack/react-query       # Data fetching
npm install lucide-react                # Icons (consistent with landing page)
npm install clsx                        # Classname utility
```

**Configure Vite proxy for API:**
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8400',
      '/ws': { target: 'ws://localhost:8400', ws: true },
    }
  }
})
```

### Step 6: Layout & Routing

**Create `dashboard/src/App.tsx`:**
- React Router with sidebar layout
- Routes: `/`, `/leads`, `/queue`, `/analytics`, `/experiments`, `/settings`
- Sidebar navigation with project selector dropdown
- Top bar with connection status indicator

**Create `dashboard/src/layouts/DashboardLayout.tsx`:**
- Sidebar: nav links with icons, project selector, connection status
- Main content area with breadcrumbs
- Responsive: sidebar collapses on mobile

**Create `dashboard/src/lib/api.ts`:**
- Fetch wrapper with API key header injection
- Base URL configuration
- Error handling (401 → redirect to settings, 429 → rate limit toast)
- Generic `get<T>`, `post<T>` functions

```typescript
const API_BASE = import.meta.env.VITE_API_URL || '';

export async function apiGet<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${API_BASE}${path}`);
  if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  const res = await fetch(url.toString(), {
    headers: { 'X-API-Key': getApiKey() },
  });
  if (!res.ok) throw new ApiError(res.status, await res.text());
  return res.json();
}
```

**Create `dashboard/src/hooks/useWebSocket.ts`:**
- WebSocket connection to `/ws/pipeline`
- Auto-reconnect with exponential backoff
- Message types: `pipeline_progress`, `queue_update`, `new_lead`

### Step 7: Dashboard Pages

**`dashboard/src/pages/Dashboard.tsx`:**
- Pipeline funnel chart (Collected → Judged → Scored → Drafted → Sent)
- Key metrics cards: total leads, approval rate, send rate, avg score
- Recent activity feed
- Quick actions: Run pipeline, View queue

**`dashboard/src/pages/Leads.tsx`:**
- Filterable/sortable table of leads
- Filters: score range, judgment label, date range, query source
- Click row → expand detail panel (post text, author info, judgment, score breakdown, draft)
- Bulk actions: export CSV, mark for re-scoring
- Infinite scroll or pagination

**`dashboard/src/pages/Queue.tsx`:**
- Card-based layout for pending drafts
- Each card shows: original post, author info, score, generated draft
- Actions per card: Approve, Edit (inline text editor), Reject (with reason)
- Bulk approve/reject
- Send button with confirmation modal and dry-run preview
- Real-time updates via WebSocket (new drafts appear, status changes)

**`dashboard/src/pages/Analytics.tsx`:**
- Score distribution histogram (Recharts BarChart)
- Judgment accuracy over time (line chart, requires human corrections)
- Query performance comparison (which queries produce highest scores)
- Conversion funnel (Sankey or stepped bar chart)
- Outcome breakdown pie chart (replies, likes, follows, negative)
- Date range selector

**`dashboard/src/pages/Experiments.tsx`:**
- List active and completed A/B experiments
- Create new experiment form, stop experiment button
- **Reduced scope:** Deep model comparison metrics (latency, accuracy, cost) are handled
  by Langfuse (integrated in T2). This page shows experiment status, links to Langfuse
  traces, and displays summary results from the `/api/experiments/{id}/results` endpoint.
- If Langfuse is configured, embed link to Langfuse dashboard filtered by experiment tag

**`dashboard/src/pages/Settings.tsx`:**
- API key configuration
- Active project selection
- View current project config (read-only)
- Server connection status

### Step 8: Shared Components

**Create these reusable components in `dashboard/src/components/`:**
- `DataTable.tsx` — Generic sortable/filterable table with column definitions
- `ScoreBadge.tsx` — Color-coded score display (red < 40, yellow 40-70, green > 70)
- `JudgmentBadge.tsx` — Pill badge for relevant/irrelevant/maybe
- `DraftCard.tsx` — Card for queue items with action buttons
- `MetricCard.tsx` — Stat card with label, value, trend arrow
- `FunnelChart.tsx` — Pipeline conversion funnel
- `DateRangePicker.tsx` — Date range selector for analytics
- `LoadingSpinner.tsx` — Consistent loading state
- `EmptyState.tsx` — Empty state with illustration and CTA
- `Toast.tsx` — Notification toast for actions

---

## 4. Phase 3 — Integration & Real-Time

### Step 9: WebSocket Backend

**Create `src/signalops/api/websocket.py`:**
- WebSocket endpoint at `/ws/pipeline`
- Broadcast pipeline stage progress during `run all`
- Broadcast queue changes (new draft, approval, send)
- Client connection registry for multi-client support

```python
class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        for connection in self.active_connections:
            await connection.send_json(message)
```

### Step 10: Pipeline Progress Hooks

**Modify orchestrator to emit WebSocket events:**
- Add optional `progress_callback` to `PipelineOrchestrator.__init__`
- Callback receives `{"stage": "collecting", "progress": 0.5, "detail": "Query 2/4"}`
- API endpoint `POST /api/pipeline/run` triggers pipeline with WebSocket progress
- Non-blocking: runs pipeline in background thread/process

### Step 11: Wire Frontend to Backend

- Connect all React pages to API endpoints via `@tanstack/react-query`
- WebSocket hooks for real-time updates
- Optimistic UI updates for approve/reject actions
- Error boundaries on all pages

---

## 5. Phase 4 — Polish & Tests

### Step 12: Backend Tests

**Create `tests/unit/test_api_schemas.py`:**
- Validate all Pydantic response models serialize correctly
- Test pagination logic
- Test edge cases (empty results, null fields)

**Create `tests/unit/test_api_auth.py`:**
- Valid API key accepted
- Invalid/missing API key returns 401
- Rate limiting headers present

**Create `tests/integration/test_api_routes.py`:**
- Use FastAPI TestClient
- Test each endpoint with seeded test data
- Test filtering, pagination, sorting on /leads
- Test approve/edit/reject flow on /queue
- Test stats aggregation accuracy
- Test WebSocket connection and message format

### Step 13: Frontend Tests

- Component tests with Vitest + React Testing Library
- API client tests with MSW (Mock Service Worker)
- E2E smoke test: load dashboard, navigate pages, approve a draft

### Step 14: Documentation

- API reference auto-generated from FastAPI OpenAPI spec
- Dashboard README with setup instructions
- Environment variables documented in `.env.example`

---

## 6. File Manifest

### New Files (Backend)

```
src/signalops/api/
    __init__.py
    app.py                      # FastAPI app factory + main entry
    auth.py                     # API key validation
    deps.py                     # Dependency injection (DB, config, auth)
    schemas.py                  # Pydantic response models
    websocket.py                # WebSocket connection manager
    routes/
        __init__.py
        projects.py             # /api/projects endpoints
        leads.py                # /api/leads endpoints
        queue.py                # /api/queue endpoints
        stats.py                # /api/stats endpoints
        analytics.py            # /api/analytics endpoints
        experiments.py          # /api/experiments endpoints
```

### New Files (Frontend)

```
dashboard/
    package.json
    tsconfig.json
    vite.config.ts
    tailwind.config.ts
    index.html
    src/
        main.tsx
        App.tsx
        index.css
        lib/
            api.ts              # API client
            websocket.ts        # WebSocket client
            utils.ts            # Shared utilities
        hooks/
            useLeads.ts
            useQueue.ts
            useStats.ts
            useAnalytics.ts
            useExperiments.ts
            useWebSocket.ts
        layouts/
            DashboardLayout.tsx
        pages/
            Dashboard.tsx
            Leads.tsx
            Queue.tsx
            Analytics.tsx
            Experiments.tsx
            Settings.tsx
        components/
            DataTable.tsx
            ScoreBadge.tsx
            JudgmentBadge.tsx
            DraftCard.tsx
            MetricCard.tsx
            FunnelChart.tsx
            DateRangePicker.tsx
            LoadingSpinner.tsx
            EmptyState.tsx
            Toast.tsx
            Sidebar.tsx
            TopBar.tsx
            ProjectSelector.tsx
```

### Modified Files

```
pyproject.toml                  # Add fastapi, uvicorn, websockets deps + signalops-api script
src/signalops/storage/database.py  # Add relationship() declarations
```

### New Test Files

```
tests/unit/test_api_schemas.py
tests/unit/test_api_auth.py
tests/integration/test_api_routes.py
```

---

## 7. API Endpoint Reference

### Authentication

All endpoints require `X-API-Key` header. Set via `SIGNALOPS_API_KEY` env var.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects` | List all projects |
| GET | `/api/projects/{id}` | Project detail |
| GET | `/api/projects/{id}/config` | Project config (sanitized) |
| POST | `/api/projects/{id}/activate` | Set active project |
| GET | `/api/leads` | List leads (filterable, paginated) |
| GET | `/api/leads/{id}` | Lead detail with judgment + score + draft |
| GET | `/api/leads/top` | Top N leads by score |
| GET | `/api/queue` | List pending drafts |
| GET | `/api/queue/{id}` | Draft detail |
| POST | `/api/queue/{id}/approve` | Approve draft |
| POST | `/api/queue/{id}/edit` | Edit and approve |
| POST | `/api/queue/{id}/reject` | Reject draft |
| POST | `/api/queue/send` | Send approved drafts |
| POST | `/api/queue/send-preview` | Dry-run preview |
| GET | `/api/stats` | Pipeline stats |
| GET | `/api/stats/timeline` | Stats over time |
| GET | `/api/stats/outcomes` | Outcome breakdown |
| GET | `/api/analytics/score-distribution` | Score histogram |
| GET | `/api/analytics/judge-accuracy` | Precision/recall |
| GET | `/api/analytics/query-performance` | Query comparison |
| GET | `/api/analytics/conversion-funnel` | Pipeline funnel |
| GET | `/api/experiments` | List experiments |
| GET | `/api/experiments/{id}` | Experiment detail |
| POST | `/api/experiments` | Create experiment |
| POST | `/api/experiments/{id}/stop` | Stop experiment |
| WS | `/ws/pipeline` | Real-time pipeline progress |

---

## 8. Testing Plan

### Backend Tests (pytest)

| Test File | Coverage |
|-----------|----------|
| `test_api_schemas.py` | Response model serialization, pagination math, edge cases |
| `test_api_auth.py` | API key valid/invalid/missing, rate limiting |
| `test_api_routes.py` | All endpoints with seeded data, filtering, approve/reject flow |

### Frontend Tests (Vitest)

| Test File | Coverage |
|-----------|----------|
| `DataTable.test.tsx` | Sorting, filtering, pagination, empty state |
| `DraftCard.test.tsx` | Approve/edit/reject actions, loading states |
| `api.test.ts` | API client auth, error handling, retries |
| `Queue.test.tsx` | Full approval workflow, optimistic updates |

### Integration Tests

| Test | Description |
|------|-------------|
| Pipeline → WebSocket | Run pipeline via API, verify WebSocket messages received |
| Queue → Send | Approve via API, send via API, verify audit log |
| Full E2E | API creates project → runs pipeline → approves → sends |

---

## Acceptance Criteria

- [ ] `signalops-api` starts FastAPI server on port 8400
- [ ] All REST endpoints return correct data with proper auth
- [ ] WebSocket broadcasts pipeline progress in real-time
- [ ] React dashboard loads and displays all pages correctly
- [ ] Approve/edit/reject flow works end-to-end through browser
- [ ] Analytics charts render with real data
- [ ] `ruff check` and `mypy --strict` pass on all new Python code
- [ ] All new tests pass
- [ ] API auto-docs available at `/docs` (Swagger UI)
