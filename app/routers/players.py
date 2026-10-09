"""Player detail feature router; kept parallel to the legacy API during migration."""
from fastapi import APIRouter, HTTPException, Request

from app.repositories.database import connection
from app.security.privacy import can_view_visibility
from app.security.request_auth import principal

router = APIRouter(prefix="/api/players", tags=["players"])


@router.get("/{player_id}")
def get_player(player_id: int, request: Request) -> dict:
    viewer = principal(request)
    with connection() as conn:
        cursor = conn.cursor()
        row = cursor.execute("""
            SELECT u.id, u.username, u.full_name, u.avatar, u.location, u.state, u.district, u.bio, u.is_verified,
                   p.sport, p.position, p.experience_years, p.age_group, p.dob, p.preferred_role, p.availability,
                   p.rating, p.classification, p.skill_score, p.performance_score, p.progress_pct,
                   p.major_matches, p.verified_local_matches, p.consistency_score
            FROM users u JOIN player_profiles p ON p.user_id = u.id WHERE u.id = ?
        """, (player_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Player not found")
        privacy_row = cursor.execute(
            "SELECT profile_visibility, stats_visibility, certs_visibility FROM privacy_settings WHERE user_id = ?",
            (player_id,),
        ).fetchone()
        privacy = dict(privacy_row) if privacy_row else {
            "profile_visibility": "public", "stats_visibility": "public", "certs_visibility": "public"
        }
        viewer_id = viewer.get("user_id") if viewer else None
        is_owner = viewer_id == player_id
        connected = False
        if viewer_id and not is_owner:
            connected = cursor.execute(
                "SELECT 1 FROM connections WHERE status = 'accepted' AND ((requester_id = ? AND recipient_id = ?) OR (requester_id = ? AND recipient_id = ?)) LIMIT 1",
                (viewer_id, player_id, player_id, viewer_id),
            ).fetchone() is not None
        is_admin = bool(viewer and viewer.get("is_admin"))
        if not can_view_visibility(privacy["profile_visibility"], is_admin=is_admin, is_owner=is_owner, is_connected=connected):
            raise HTTPException(status_code=404, detail="Player profile is private")
        result = dict(row)
        can_view_stats = can_view_visibility(privacy["stats_visibility"], is_admin=is_admin, is_owner=is_owner, is_connected=connected)
        if can_view_stats:
            result["tests"] = [dict(x) for x in cursor.execute(
                "SELECT * FROM sports_tests WHERE player_id = ? ORDER BY date_taken DESC", (player_id,)
            ).fetchall()]
            result["matches"] = [dict(x) for x in cursor.execute("""
                SELECT m.id AS match_id, m.title, m.sport, m.team_a, m.team_b, m.match_date,
                       m.location, m.result_summary, m.status AS match_status, m.verified_by,
                       mps.team_name, mps.role_played, mps.stats_json, mps.performance_rating, mps.verified_status
                FROM match_player_stats mps JOIN matches m ON mps.match_id = m.id
                WHERE mps.player_id = ? ORDER BY m.match_date DESC
            """, (player_id,)).fetchall()]
        else:
            result["tests"] = []
            result["matches"] = []
            for key in ("rating", "skill_score", "performance_score", "progress_pct", "major_matches",
                        "verified_local_matches", "consistency_score"):
                result[key] = None
        if can_view_visibility(privacy["certs_visibility"], is_admin=is_admin, is_owner=is_owner, is_connected=connected):
            result["certificates"] = [dict(x) for x in cursor.execute(
                "SELECT * FROM certificates WHERE player_id = ? ORDER BY year DESC", (player_id,)
            ).fetchall()]
        else:
            result["certificates"] = []
        return {"player": result}
