"""Certificate listing router with visibility enforcement."""
from fastapi import APIRouter, HTTPException, Request

from app.repositories.database import connection
from app.security.privacy import can_view_visibility
from app.security.request_auth import principal

router = APIRouter(prefix="/api/certificates", tags=["certificates"])


@router.get("")
def list_certificates(request: Request, player_id: int | None = None) -> dict:
    viewer = principal(request)
    is_admin = bool(viewer and viewer.get("is_admin"))
    viewer_id = viewer.get("user_id") if viewer else None
    with connection() as conn:
        cursor = conn.cursor()
        if player_id is not None:
            privacy_row = cursor.execute("SELECT certs_visibility FROM privacy_settings WHERE user_id = ?", (player_id,)).fetchone()
            visibility = privacy_row["certs_visibility"] if privacy_row else "public"
            owner = viewer_id == player_id
            connected = False
            if viewer_id and not owner:
                connected = cursor.execute(
                    "SELECT 1 FROM connections WHERE status = 'accepted' AND ((requester_id = ? AND recipient_id = ?) OR (requester_id = ? AND recipient_id = ?)) LIMIT 1",
                    (viewer_id, player_id, player_id, viewer_id),
                ).fetchone() is not None
            if not can_view_visibility(visibility, is_admin=is_admin, is_owner=owner, is_connected=connected):
                raise HTTPException(status_code=404, detail="Certificates are private")
            rows = cursor.execute("SELECT * FROM certificates WHERE player_id = ? ORDER BY id DESC", (player_id,)).fetchall()
        elif is_admin:
            rows = cursor.execute("SELECT c.*, u.full_name AS player_name, u.avatar AS player_avatar FROM certificates c JOIN users u ON u.id = c.player_id ORDER BY c.id DESC").fetchall()
        else:
            rows = cursor.execute("""
                SELECT c.*, u.full_name AS player_name, u.avatar AS player_avatar
                FROM certificates c JOIN users u ON u.id = c.player_id
                LEFT JOIN privacy_settings ps ON ps.user_id = c.player_id
                WHERE COALESCE(ps.certs_visibility, 'public') = 'public'
                ORDER BY c.id DESC
            """).fetchall()
        return {"certificates": [dict(row) for row in rows]}
