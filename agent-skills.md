# Agent Skills — CSE362 Room Booking System

Reference guide for AI coding agents working on this project.

---

## Project Overview

A room booking system with a **Python/FastAPI backend** and a **Svelte 5/SvelteKit frontend**. The frontend compiles into `backend/app/static/` via `adapter-static`, so a single Uvicorn process serves both the API and the SPA.

```
CSE362/
  backend/        Python FastAPI backend
  frontend/       Svelte 5 + SvelteKit SPA
  .github/        CI/CD workflows
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend runtime | Python 3.13+, FastAPI, Uvicorn |
| ORM | SQLModel (SQLAlchemy async) |
| Database | SQLite via aiosqlite |
| Auth | fastapi-users (JWT Bearer tokens) |
| Frontend framework | Svelte 5 (runes mode) + SvelteKit |
| UI components | shadcn-svelte (bits-ui primitives) |
| Styling | TailwindCSS 4 |
| Data tables | TanStack Table v8 (`@tanstack/table-core`) |
| Icons | Lucide (`@lucide/svelte`) |
| Theme | mode-watcher (light/dark/system) |
| Avatars | multiavatar (deterministic SVG) |
| Build | Vite 7, adapter-static |

---

## Backend

### Directory Structure

```
backend/
  app/
    __init__.py
    main.py              # FastAPI app, lifespan, catch-all SPA route
    database.py          # Async engine + get_session dependency
    env.py               # Environment variable loading (dotenv)
    seed.py              # Idempotent seed: rooms + timeslots for Feb/Mar/Apr 2026
    models/
      __init__.py        # Re-exports all models
      user.py            # User (extends SQLModelBaseUserDB), UserRole enum
      room.py            # Room (name, capacity)
      booking.py         # Booking, TimeSlot, BookingStatus, TimeslotStatus, RecurrenceFrequency
      notification.py    # Notification, NotificationType
    schemas/
      user.py            # UserRead, UserCreate, UserUpdate, AdminUserUpdate
      room.py            # RoomRead, RoomBasicRead, TimeSlotRead
    routes/
      auth.py            # /api/auth/* — login, register, me, avatar, admin user update
      rooms.py           # /api/rooms/* — list rooms, get room, available dates
      bookings.py        # /api/bookings/* — submit, list, admin actions (approve/deny/cancel)
      notifications.py   # /api/notifications/*
    services/
      auth.py            # auth_backend, current_active_user, require_admin, fastapi_users
      user_manager.py    # UserManager, register_superuser
      room_service.py    # get_rooms_with_availability, get_available_dates, get_room
      booking_service.py # submit_booking, approve/deny/cancel_booking, get_*_bookings
      notification_service.py
      avatar_service.py  # Deterministic SVG avatar via multiavatar
    static/              # Built SPA output (gitignored, populated by frontend build)
  tests/                 # pytest async tests
  .env                   # Environment variables (not committed to production)
  pyproject.toml
  pytest.ini
```

### Environment Variables

Required in `.env` or as OS environment variables:

```env
SUPER_USER_NAME="admin"
SUPER_USER_EMAIL="admin@example.com"
SUPER_USER_PASSWORD="password"
JWT_SECRET="your_secret_here"
DATABASE_URL="sqlite+aiosqlite:///./app.db"
```

These are asserted at import time in `app/env.py`. Missing any of them causes an immediate crash.

### Running the Backend

```bash
cd backend
uv run fastapi dev          # Development (hot reload)
uv run fastapi run          # Production
```

### Key Patterns

**Authentication**: Uses `fastapi-users` with JWT Bearer strategy. Key dependencies:
- `current_active_user` — requires valid token, returns `User`
- `require_admin` — requires `role == "admin"`
- Token is sent as `Authorization: Bearer <token>` header

**Database sessions**: All route handlers receive `AsyncSession` via `Depends(get_session)`. Some services use `session.run_sync()` to run synchronous SQLModel code within the async session.

**Booking lifecycle**:
```
AVAILABLE slot → hold() → HELD slot (booking status: PENDING)
  → approve → book() → BOOKED slot (booking status: APPROVED)
  → deny    → release() → AVAILABLE slot (booking status: DENIED)
  → cancel (from APPROVED) → release() → AVAILABLE slot (booking status: CANCELLED)
```

**Seed data**: `app/seed.py` runs on startup (idempotent). Creates 10 rooms and ~5000 timeslots across Feb/Mar/Apr 2026. Uses `random.Random(2026)` for deterministic output.

**Avatar endpoint**: `GET /api/auth/avatar` — requires auth, returns deterministic SVG based on user ID via multiavatar. The frontend fetches this as a blob URL since `<img>` tags can't send Bearer tokens.

### Testing

```bash
cd backend
uv run pytest                # Run all tests
uv run pytest tests/test_route_rooms.py -v   # Run specific file
```

- `asyncio_mode = auto` in `pytest.ini` — no need to mark tests with `@pytest.mark.asyncio` in most cases
- Tests use in-memory SQLite with `StaticPool`
- Override `get_session` and `current_active_user` via `app.dependency_overrides`
- Always clean up overrides: `app.dependency_overrides.clear()`

**Test file conventions**:
- `test_model_*.py` — model validation and methods
- `test_service_*.py` — service layer (business logic)
- `test_route_*.py` — HTTP endpoint tests via `httpx.AsyncClient`

### Adding a New Feature (Backend)

1. **Model** in `app/models/` — add fields, update `__init__.py` exports
2. **Schema** in `app/schemas/` (or inline in route file for simple cases)
3. **Service** in `app/services/` — business logic, no HTTP concerns
4. **Route** in `app/routes/` — thin layer calling services, include in `app/main.py`
5. **Tests** in `tests/` — service-level + route-level tests
6. Delete `app.db` if schema changed (no Alembic migrations; `create_all` only creates new tables)

---

## Frontend

### Directory Structure

```
frontend/
  src/
    lib/
      api.ts                     # apiFetch wrapper (token injection, 401 handling)
      utils.ts                   # cn() helper for class merging
      state/
        auth.svelte.ts           # AuthState singleton (user, token, avatar, login/logout/register)
        dashboard.svelte.ts      # DashboardState (selected date, rooms, available dates)
      components/
        ui/                      # shadcn-svelte primitives (button, card, table, calendar, etc.)
        nav-user.svelte          # User dropdown for sidebar context
        nav-user-header.svelte   # User dropdown for standalone header (no sidebar)
        date-picker.svelte       # Calendar with available-date highlighting
        calendars.svelte         # Sidebar bookings summary list
        room-list.svelte         # TanStack data table for rooms
        room-table/
          sort-button.svelte     # Reusable sortable column header
          actions.svelte         # Room row 3-dot menu
        booking-table/
          actions.svelte         # Booking row 3-dot menu
    routes/
      +layout.svelte             # Auth guards, sidebar (dashboard), header (other pages)
      +layout.ts                 # SSR disabled, prerender enabled
      +error.svelte              # Error page (404, etc.)
      +page.svelte               # Dashboard — room data table
      login/                     # Login form
      logout/                    # Logout confirmation
      account/                   # User profile + theme toggle
      bookings/                  # Bookings data table
      bookingdetails/[id]/       # Single booking detail view
      book/[roomId]/[date]/      # Book a room — slot selection + submit
      admin/                     # Admin panel (superuser only)
      notifications/             # Notifications page
```

### Running the Frontend

```bash
cd frontend
bun install         # or npm install
bun run dev         # Development server (proxies /api to backend)
bun run build       # Build SPA into ../backend/app/static/
bun run check       # Type check (svelte-check)
```

The Vite dev server proxies `/api/*` to `http://127.0.0.1:8000` (configured in `vite.config.ts`). Run the backend simultaneously.

### Key Patterns

**Auth state** (`src/lib/state/auth.svelte.ts`):
- Singleton `auth` instance using Svelte 5 `$state` runes
- Token stored in `localStorage`, synced via private setter
- `isAuthenticated` requires both token AND verified user object
- `isLoading` starts `true` — layout blocks rendering until token is verified
- Avatar fetched as blob URL (auth endpoint returns SVG, `<img>` can't send Bearer tokens)
- `api.ts` uses callback registration (`setTokenGetter`, `setOnUnauthorized`) to avoid circular imports

**API helper** (`src/lib/api.ts`):
- `apiFetch<T>(path, options)` — attaches Bearer token, parses JSON, handles 401 auto-logout
- No circular dependency with auth — uses registered callbacks

**Route guards** (`+layout.svelte`):
- Three path categories: `PUBLIC_PATHS` (no auth needed), `GUEST_ONLY_PATHS` (redirect authenticated users away), protected (everything else)
- `beforeNavigate` intercepts client-side navigation
- `$effect` handles direct URL visits and reactive auth changes
- `/admin` additionally requires `auth.isSuperuser`
- `/logout` is public but NOT guest-only (authenticated users can reach it)

**Layout structure**:
- **Dashboard (`/`)**: Full sidebar (NavUser header + DatePicker + My Bookings list) + Sidebar.Inset content
- **Other authenticated pages**: No sidebar. Full-width layout with header (NavUserHeader on desktop, hamburger sheet on mobile) + breadcrumb
- **Public pages**: No sidebar, no header, just the page content

**Dashboard state** (`src/lib/state/dashboard.svelte.ts`):
- `selectedDate` — selected calendar date
- `rooms` — fetched rooms with timeslots for that date
- `availableDates` — Set of ISO date strings with available rooms
- DatePicker calls `dashboard.selectDate()` and `dashboard.loadAvailableDates()`
- Room list table derives from `dashboard.rooms`, filtering out rooms with 0 available slots

**Data tables** (TanStack Table):
- Use `createSvelteTable` from `$lib/components/ui/data-table`
- Column definitions use `renderComponent` (for Svelte components) and `renderSnippet` (for raw HTML)
- Standard pattern: `$state` for pagination/sorting/filters/visibility, table state getters, `on*Change` updaters
- Reusable `sort-button.svelte` for sortable column headers

**Component library**: shadcn-svelte components live in `src/lib/components/ui/`. They are bits-ui primitives with Tailwind styling. Do not modify these directly — they are generated via `shadcn-svelte` CLI.

### Prerendering and Dynamic Routes

The root `+layout.ts` sets `prerender = true` and `ssr = false` globally. This means `adapter-static` tries to generate HTML for every route at build time.

**Dynamic routes with parameters** (e.g., `[id]`, `[roomId]`) **cannot be prerendered** because the build crawler doesn't know what parameter values to use. You MUST add a `+page.ts` file in the dynamic route directory to opt out:

```ts
// src/routes/your-route/[param]/+page.ts
export const prerender = false;
```

Without this, the build will fail with:
```
Error: The following routes were marked as prerenderable, but were not prerendered
because they were not found while crawling your app
```

These routes are instead handled at runtime by the SPA's `fallback: 'index.html'` (configured in `svelte.config.js`).

**Current dynamic routes with `prerender = false`:**
- `src/routes/book/[roomId]/[date]/+page.ts`
- `src/routes/bookingdetails/[id]/+page.ts`

### Adding a New Page

1. Create `src/routes/your-page/+page.svelte`
2. **If the route has dynamic params** (e.g., `[id]`): add a `+page.ts` with `export const prerender = false;`
3. If it needs auth (default): it's automatically protected by the layout guard
4. If it should be public: add to `PUBLIC_PATHS` in `+layout.svelte`
5. If authenticated users should NOT see it: also add to `GUEST_ONLY_PATHS`
6. Add to `PAGE_NAMES` in `+layout.svelte` for the breadcrumb, or handle in `pageName()` for dynamic routes (e.g., `if (pathname.startsWith("/your-route/")) return "Your Page";`)
7. For dynamic routes: use `[param]` directory naming (e.g., `bookingdetails/[id]/+page.svelte`), access via `page.params.id`

### Adding a Data Table Page

Follow the pattern in `bookings/+page.svelte`:

1. Define your row type interface
2. Fetch data in `$effect` → transform into flat row objects
3. Define `columns: ColumnDef<YourRow>[]` array
4. Create table state (`pagination`, `sorting`, `columnFilters`, `columnVisibility`)
5. Call `createSvelteTable({ ... })`
6. Render using the standard `Table.*` + `FlexRender` template

### Type Checking

```bash
cd frontend
bun run check     # Must show 0 errors before committing
```

The LSP may show stale errors in the editor — always trust `svelte-check` over inline diagnostics.

---

## CI/CD

### GitHub Actions

**`.github/workflows/ci.yml`** — Runs on push/PR to `main`/`dev`:
- Sets up Python + uv
- Creates mock static file (frontend not built in CI)
- Runs `uv run pytest` with dummy env vars

**`.github/workflows/release.yml`** — Runs on `v*` tag push:
- Builds frontend with Bun
- Runs backend tests
- Exports `requirements.txt`
- Packages `app/` + `requirements.txt` into `app-release.zip`
- Creates GitHub Release

Both workflows inject dummy environment variables for the test step:
```yaml
env:
  SUPER_USER_NAME: "testadmin"
  SUPER_USER_EMAIL: "admin@test.com"
  SUPER_USER_PASSWORD: "testpassword"
  JWT_SECRET: "ci_test_secret"
  DATABASE_URL: "sqlite+aiosqlite:///./test.db"
```

### Local CI Testing (with act + podman)

```bash
systemctl --user start podman.socket
nix develop --command act push \
  --container-daemon-socket "unix:///run/user/$(id -u)/podman/podman.sock" \
  -W .github/workflows/ci.yml
```

---

## Database

- **Engine**: SQLite via aiosqlite (async)
- **Schema management**: `SQLModel.metadata.create_all` on startup — creates missing tables but does NOT alter existing ones
- **If you add/rename columns**: Delete `backend/app.db` and restart. It will be recreated with the correct schema and seeded automatically.
- **`app.db` is gitignored** — it's a local development artifact

### Models Summary

| Model | Table | Key Fields |
|-------|-------|-----------|
| `User` | `user` | id (UUID), email, name, hashed_password, role (student/teacher/admin), is_superuser, is_active |
| `Room` | `room` | id (int), name (unique), capacity |
| `TimeSlot` | `timeslot` | id, room_id (FK), slot_date, start_time, end_time, status (available/held/booked), booking_id (FK) |
| `Booking` | `booking` | id, userID (FK), roomID (FK), status (pending/approved/denied/cancelled), recurrenceFrequency, recurrenceEndDate, createdAt |
| `Notification` | `notification` | id, user_id (FK), booking_id (FK), type, read, created_at |

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/login` | None | Login (form-urlencoded: username, password) |
| POST | `/api/auth/register` | None | Register (JSON: email, password, name) |
| GET | `/api/auth/me` | Bearer | Current user profile |
| GET | `/api/auth/avatar` | Bearer | User's SVG avatar |
| PATCH | `/api/auth/users/{id}` | Admin | Update user role/active status |
| GET | `/api/rooms?date=YYYY-MM-DD` | Bearer | Rooms with timeslots for date |
| GET | `/api/rooms/dates?year=N&month=N` | Bearer | Dates with available slots in month |
| GET | `/api/rooms/{id}` | Bearer | Single room details |
| POST | `/api/bookings` | Bearer | Submit booking (room_id, date, slot_ids, recurrence) |
| GET | `/api/bookings` | Bearer | User's bookings (admin sees all, optionally `?status=`) |
| PATCH | `/api/bookings/{id}` | Admin | Approve/deny/cancel booking |
| GET | `/api/notifications` | Bearer | User's notifications |
| PATCH | `/api/notifications/{id}/read` | Bearer | Mark notification as read |
| GET | `/api/health` | None | Health check |

---

## Common Tasks

### Reset the database
```bash
cd backend && rm -f app.db && uv run fastapi dev
```

### Run all checks
```bash
cd backend && uv run pytest
cd frontend && bun run check
```

### Add a new UI component (shadcn-svelte)
```bash
cd frontend && bunx shadcn-svelte@latest add <component-name>
```

### Add a Python dependency
```bash
cd backend && uv add <package-name>
```
