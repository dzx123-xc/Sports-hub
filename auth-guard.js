/*
 * SConnect protected-page guard.
 * Server-side authorization is authoritative; this script provides a fast
 * browser-side redirect while the server/API checks the same session.
 */
(function () {
  const requiredRoleByPage = {
    "player-dashboard.html": "Player",
    "coach-dashboard.html": "Coach",
    "club-dashboard.html": "Club",
    "organizer-dashboard.html": "Organizer",
    "referee-dashboard.html": "Referee",
    "admin-portal.html": "Admin"
  };

  const page = location.pathname.split("/").pop();
  const requiredRole = requiredRoleByPage[page];
  if (!requiredRole) return;

  fetch("/api/auth/me", {
    credentials: "same-origin",
    cache: "no-store"
  })
    .then(async (response) => {
      if (!response.ok) throw new Error("unauthorized");
      const payload = await response.json();
      const user = payload.user;
      if (!user || user.role !== requiredRole) throw new Error("forbidden");
      window.SPORTS_CONNECT_CURRENT_USER = user;
      window.dispatchEvent(new CustomEvent("sportsconnect:authenticated", {
        detail: user
      }));
    })
    .catch(() => {
      window.location.replace("/");
    });
})();
