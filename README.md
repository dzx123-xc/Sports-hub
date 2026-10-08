SConnect / SportsHub

Full-stack sports networking platform.

Run locally:
1. python server.py
2. open http://localhost:8000

Authentication:
- Database-backed username/email/phone login
- HttpOnly session cookie
- Role-protected dashboards
- Public registration excludes Admin
- Admin credentials are provisioned as the single protected operator account
- Demo seed profiles are not login accounts

Project roles:
Player, Coach, Club, Organizer, Referee, Admin.

The SQLite database is included for local development.
