SPORTHUB ROLE DASHBOARD REPLACEMENT

Replace these existing files:
1. app.js
2. style.css

Add these new files in the SAME folder as index.html:
3. dashboard.js
4. player-dashboard.html
5. coach-dashboard.html
6. organizer-dashboard.html
7. referee-dashboard.html

index.html does NOT need to be replaced for the new role dashboards to work.

LOGIN FLOW
- Player login -> player-dashboard.html
- Coach login -> coach-dashboard.html
- Organizer login -> organizer-dashboard.html
- Referee login -> referee-dashboard.html

IMPORTANT
All files must be in the same folder.
The dashboard pages use the existing sports-background.png.
Registration/login data is stored in browser localStorage, so use the same browser where the account was registered.
If an old Player session is visible, log out once and then log in again using the correct role.
