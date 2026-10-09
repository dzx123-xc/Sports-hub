# Architecture completion: rollout and operational requirements

This branch adds foundations while the production process remains on `python server.py`. Do not switch the production entry point until the legacy endpoint compatibility suite has been replaced by end-to-end tests.

## Implemented in this batch

- Legacy player-detail responses now apply `profile_visibility`, `stats_visibility`, and `certs_visibility`; certificate listings filter private certificates.
- Administrator login accepts a six-digit TOTP code when `ADMIN_TOTP_SECRET` is configured. With `ADMIN_TOTP_REQUIRED=true`, login fails closed if the secret is missing.
- FastAPI database readiness route: `GET /health/ready`. `GET /health` remains liveness-only.
- Repository connection boundary, readiness service, Supabase private-storage adapter, persistent job queue schema, and opt-in worker for notification creation and scoring classification.
- Contract/unit tests for TOTP, private storage configuration, privacy checks, queue schema, and router registration.

## Required deployment configuration

### Administrator TOTP
1. Generate a random Base32 secret in a trusted local password manager/authenticator setup. Do not commit it.
2. Add `ADMIN_TOTP_SECRET` to Railway's service secrets.
3. Set `ADMIN_TOTP_REQUIRED=true`.
4. Use the six-digit authenticator code in the admin login request as `totp_code`.
5. Test a valid code, invalid code, missing code, and clock drift in staging before the next production deployment.

If the secret is not set and the required flag is false, legacy admin login remains password-only for compatibility. This is deliberate so the current deployment is not unexpectedly locked out before the secret has been provisioned.

### Private media storage
1. Create a **private** Supabase Storage bucket (not public).
2. Configure `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `SUPABASE_MEDIA_BUCKET` as service secrets.
3. Keep the service-role key server-side only. Never put it in frontend JS.
4. Use `SupabasePrivateStorage.create_signed_url` for short-lived access; do not expose permanent public object URLs.
5. Enforce per-user object paths and upload size/MIME validation in the API route before wiring uploads to the UI.

### Background worker
1. The `background_jobs` table is created by `init_db()`.
2. Configure a separate Railway worker process with start command `python -m app.workers.runner` and `BACKGROUND_WORKER_ENABLED=true`.
3. The worker uses the same `DATABASE_URL` and credentials as the API; deploy it only after staging queue tests pass.
4. Monitor failed jobs and database connectivity. The worker is opt-in and is not started by the web service.

## Not yet complete; do not represent as production-ready

- Full migration of all legacy REST endpoints into FastAPI routers.
- Complete service/repository separation for existing feature logic.
- End-to-end integration coverage for every role and every authorization branch.
- Upload endpoints and per-object ownership checks wired to the private storage adapter.
- Production worker service provisioning, dead-letter/replay operations, and queue concurrency hardening.
- Automated production backup verification and external error/uptime alert delivery.

## Safe release sequence

1. CI and integration tests pass.
2. Provision TOTP and private storage secrets in staging.
3. Run role/ownership/privacy tests against a disposable staging database.
4. Deploy web and worker to staging and verify liveness/readiness, login, profile privacy, certificate visibility, messaging, reports, and queue retries.
5. Confirm a database backup can be restored to a separate test database.
6. Schedule one production release only after the above checks; verify `/health` and `/health/ready` after rollout.

Do not enable the FastAPI entry point in production as part of this foundation-only change.
