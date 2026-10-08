# SConnect / SportsHub

Sports networking platform for Players, Coaches, Clubs, Organizers and Referees.

## Current authentication contract

- Server session is the source of truth.
- Protected dashboards are role checked.
- Logged-out visitors are redirected away from role dashboards.
- Public registration excludes Admin.
- User identity is resolved from the active session rather than a hardcoded/demo profile.
- Demo discovery records must never act as login accounts.
- Profile editing must update the authenticated user's database record.

## Local development

```text
python server.py
http://localhost:8000
```

## Project modules

Authentication, profiles, discovery, matching, connections, messaging, trials, tournaments, matches, notifications, reporting and administration.

## Repository note

The repository is being synchronized from the current SConnect project source. Authentication/security work is being committed incrementally and verified before each next feature phase.
