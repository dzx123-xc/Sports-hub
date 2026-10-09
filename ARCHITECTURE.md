# SportsHub target architecture

This document records the target architecture shown in the approved architecture diagram and distinguishes it from the currently deployed implementation.

## Target request path

1. **Client:** public landing/auth pages, discovery, a shared dashboard shell for Player, Coach, Club, Organizer and Referee, and a restricted admin portal.
2. **FastAPI backend:** authentication/session handling, server-side role checks, rate limiting and CSRF protection; feature routers call service-layer functions.
3. **Services and repositories:** business rules (including scoring and verification) live in services. Repositories are the only application layer that executes database queries.
4. **Data and jobs:** Supabase PostgreSQL, private file storage for avatars/videos, and a worker for scoring and notifications.
5. **Delivery:** CI checks, Railway staging/production, and health/error/backup monitoring.

## Current state (verified against the repository)

- Production currently starts `server.py`, a Python standard-library HTTP server with REST handlers and static-file serving.
- `database.py` provides the SQLite/local and PostgreSQL/Supabase adapter.
- Session tokens are random values; only their SHA-256 hashes are stored in the sessions table. Passwords use PBKDF2-HMAC-SHA256.
- The five role dashboard pages and admin portal already exist.
- A health endpoint exists in the legacy server.
- FastAPI routers, a dedicated service/repository boundary, file-storage adapter, job worker, enforced CSRF/rate-limit middleware, and admin TOTP 2FA are **not yet fully implemented**.

## Migration phases

- **Phase 1 — foundation (this change):** introduce a separate FastAPI application entry point and testable health endpoint without changing the live Railway start command. Document the target boundaries and add CI coverage.
- **Phase 2 — security:** add tested cookie/session settings, CSRF protection, rate limiting, and admin TOTP 2FA. Keep authorization checks server-side.
- **Phase 3 — modular backend:** migrate endpoint groups into routers and move business rules into services; repositories become the only layer that queries the database.
- **Phase 4 — data and async work:** add a configurable private file-storage adapter and a separate worker for idempotent scoring/notification jobs.
- **Phase 5 — cutover:** run compatibility/integration tests against Supabase, configure Railway health checks and staging, then change the production start command only after a reviewed release.

## Safety constraints

- Do not deploy the FastAPI entry point until the existing endpoints and browser flows have been migrated and tested.
- Never put secrets or demo credentials in source control.
- Do not claim file storage, background jobs, CSRF/rate limiting, or 2FA are active until implemented and tested.
