# SportsHub Production Deployment

## Architecture

- GitHub: source control and CI
- Railway: Python web service
- Supabase: PostgreSQL database

## Required Railway variables

```
DATABASE_URL=<Supabase PostgreSQL connection string>
DB_SSLMODE=require
ADMIN_USERNAME=admin_123
ADMIN_PASSWORD=<long random secret>
SESSION_TTL_HOURS=24
COOKIE_SECURE=true
LOG_LEVEL=INFO
```

Railway provides the `PORT` variable automatically. The application listens on `0.0.0.0:$PORT`.

## Start command

```
python server.py
```

## Health check

```
/health
```

Expected response:

```json
{"status":"ok","database":"postgresql"}
```

## Supabase

Create the PostgreSQL project first and copy its PostgreSQL connection string into Railway as `DATABASE_URL`.

The application creates its tables automatically on first startup. No SQLite database file is required.

## Security

Never commit:

- `.env`
- Supabase database passwords
- Railway secrets
- `sportsconnect.db`
- production database dumps

The admin account is not stored in the application database. Its username and password come from Railway variables.

## Local development

Without `DATABASE_URL`, the project keeps a SQLite compatibility mode for local testing.

With `DATABASE_URL` configured, the same application uses PostgreSQL.
