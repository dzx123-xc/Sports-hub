# SConnect Security

## Authentication
Protected dashboards must be accessible only through a valid server-side session.

The browser must not be treated as the source of truth for identity. Client storage is only a presentation cache.

## Roles
Public registration supports Player, Coach, Club, Organizer and Referee. Admin is never publicly registerable.

## Admin
The platform has a single protected Admin account. Admin authorization is enforced server-side.

## Privacy
Do not commit real passwords, API keys, session tokens or production secrets. Development credentials should be supplied through local environment/configuration when appropriate.

## Data isolation
Every profile, connection, message, trial, match and administrative action must be associated with a database user ID and authorization checked on the server.
