"""
SportsConnect Full-Stack Server
Provides RESTful APIs for the sports networking ecosystem and serves UI assets.
Built with Python 3 standard library plus PostgreSQL support via psycopg2.
"""

import http.server
import socketserver
import json
import urllib.parse
import os
import mimetypes
import secrets
import hashlib
import logging
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from database import DB_PATH, get_db, hash_pw, verify_pw, init_db, USING_POSTGRES
from app.security.totp import verify_totp
from app.security.privacy import can_view_visibility

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("sportsconnect")

PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _utcnow_naive():
    """Return UTC now as naive ISO-compatible time for existing DB timestamps.

    Session timestamps have historically been stored as naive UTC ISO strings.
    Build the instant with an aware UTC datetime, then remove tzinfo only at the
    storage boundary to keep comparisons compatible with existing rows.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)

# Admin credentials are deployment secrets, never source-code credentials.
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin_123")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    logger.warning("ADMIN_PASSWORD is not configured; admin login is disabled.")

SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "24"))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true" if os.getenv("RAILWAY_ENVIRONMENT_NAME") else "false")
COOKIE_SECURE_FLAG = "; Secure" if COOKIE_SECURE.lower() in ("1", "true", "yes") else ""

_RATE_LIMITS = defaultdict(deque)
_RATE_LIMIT_LOCK = threading.Lock()

def _client_ip(handler):
    # Trust the direct peer by default; do not trust user-supplied forwarded headers.
    return handler.client_address[0] if handler.client_address else "unknown"

def _rate_limit_allowed(handler, bucket, limit, window_seconds):
    now = time.monotonic()
    key = (bucket, _client_ip(handler))
    with _RATE_LIMIT_LOCK:
        events = _RATE_LIMITS[key]
        while events and now - events[0] >= window_seconds:
            events.popleft()
        if len(events) >= limit:
            return False
        events.append(now)
        return True

PROTECTED_ROLE_PAGES = {
    '/player-dashboard.html': 'Player',
    '/coach-dashboard.html': 'Coach',
    '/club-dashboard.html': 'Club',
    '/organizer-dashboard.html': 'Organizer',
    '/referee-dashboard.html': 'Referee',
}

def _cookie_value(handler, name):
    for part in handler.headers.get('Cookie', '').split(';'):
        part = part.strip()
        if part.startswith(name + '='):
            return urllib.parse.unquote(part.split('=', 1)[1])
    return None

def _token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def current_user_id(handler):
    token = _cookie_value(handler, 'sc_session')
    if not token: return None
    conn = get_db()
    try:
        row = conn.cursor().execute("SELECT user_id FROM sessions WHERE token_hash = ? AND role = 'user' AND expires_at > ?", (_token_hash(token), _utcnow_naive().isoformat())).fetchone()
        return int(row["user_id"]) if row and row["user_id"] is not None else None
    finally:
        conn.close()

def issue_user_session(user_id):
    token = secrets.token_urlsafe(32)
    now = _utcnow_naive()
    expires = now + timedelta(hours=SESSION_TTL_HOURS)
    conn = get_db()
    try:
        conn.cursor().execute("INSERT INTO sessions (token_hash, user_id, role, expires_at, created_at) VALUES (?, ?, 'user', ?, ?)", (_token_hash(token), int(user_id), expires.isoformat(), now.isoformat()))
        conn.commit()
    finally:
        conn.close()
    return token

def issue_admin_session():
    token = secrets.token_urlsafe(32)
    now = _utcnow_naive()
    expires = now + timedelta(hours=SESSION_TTL_HOURS)
    conn = get_db()
    try:
        conn.cursor().execute("INSERT INTO sessions (token_hash, user_id, role, expires_at, created_at) VALUES (?, NULL, 'admin', ?, ?)", (_token_hash(token), expires.isoformat(), now.isoformat()))
        conn.commit()
    finally:
        conn.close()
    return token

def clear_user_session(handler):
    token = _cookie_value(handler, 'sc_session')
    if token:
        conn = get_db()
        try:
            conn.cursor().execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))
            conn.commit()
        finally:
            conn.close()

def is_admin_request(handler):
    token = _cookie_value(handler, 'sc_admin_session')
    if not token: return False
    conn = get_db()
    try:
        row = conn.cursor().execute("SELECT 1 FROM sessions WHERE token_hash = ? AND role = 'admin' AND expires_at > ?", (_token_hash(token), _utcnow_naive().isoformat())).fetchone()
        return bool(row)
    finally:
        conn.close()
def calculate_player_classification(skill_score, perf_score, progress_pct, major_matches, achievements_count=1):
    """
    Scoring model:
    - Skill/Test Score: 30%
    - Match Performance: 30%
    - Progress/Improvement: 20%
    - Competitive Experience: 10%
    - Verified Achievements: 10%
    Experience does NOT dominate talent classification.
    """
    exp_factor = min(100.0, (major_matches / 10.0) * 100.0)
    achieve_factor = min(100.0, achievements_count * 40.0)
    progress_index = min(100.0, 70.0 + progress_pct)
    composite = (skill_score * 0.30) + (perf_score * 0.30) + (progress_index * 0.20) + (exp_factor * 0.10) + (achieve_factor * 0.10)

    # Rising Talent: High potential with limited major competitive experience
    if skill_score >= 80.0 and perf_score >= 78.0 and progress_pct >= 14.0 and major_matches <= 3:
        classification = "Rising Talent"
    elif composite >= 88.0 and major_matches >= 12:
        classification = "Elite Player"
    elif composite >= 78.0 and major_matches >= 6:
        classification = "Established Player"
    else:
        classification = "Emerging Player"

    return classification, round(composite, 1)

def smart_match(player, criteria):
    """
    Computes a smart match score (0-100%) and itemized checklist.
    Criteria: sport, role/position, location, min_skill, availability
    """
    score = 0
    max_possible = 100
    reasons = []

    # Sport match (30%)
    req_sport = criteria.get('sport')
    if req_sport:
        if player['sport'].lower() == req_sport.lower():
            score += 30
            reasons.append(f"Same sport: {player['sport']}")
        else:
            return 0, [] # Must match sport

    # Role/Position match (20%)
    req_role = criteria.get('position')
    if req_role:
        if req_role.lower() in player['position'].lower() or player['position'].lower() in req_role.lower():
            score += 20
            reasons.append(f"Same role: {player['position']}")
        else:
            score += 5
    else:
        score += 20

    # Location match (15%)
    req_loc = criteria.get('location')
    if req_loc:
        if req_loc.lower() in (player['location'] or '').lower():
            score += 15
            reasons.append(f"Same location: {player['location']}")
        else:
            score += 5
    else:
        score += 15

    # Skill Score meets requirement (15%)
    min_skill = float(criteria.get('min_skill', 0))
    if player['skill_score'] >= min_skill:
        score += 15
        reasons.append(f"Skill score meets requirement ({player['skill_score']:.0f}+)")
    else:
        score += max(0, int(15 - (min_skill - player['skill_score'])))

    # Availability (10%)
    if 'available' in player['availability'].lower():
        score += 10
        reasons.append("Available for trials / signing")
    else:
        score += 2

    # Recent performance / Progress (5%)
    if player['performance_score'] >= 80:
        score += 5
        reasons.append("Strong recent performance")

    # Rising talent boost (5%)
    if player['classification'] == 'Rising Talent':
        score += 5
        reasons.append("🌟 Verified Rising Talent")

    final_pct = min(98, max(50, score))
    return final_pct, reasons

class SportsConnectHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def end_headers(self):
        # Frontend and API are served from the same origin; wildcard CORS is unnecessary.
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def send_json(self, data, status=200, cookies=None):
        body = json.dumps(data, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        if cookies:
            for cookie in cookies:
                self.send_header('Set-Cookie', cookie)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def parse_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length).decode('utf-8')
        try:
            return json.loads(raw)
        except Exception:
            return urllib.parse.parse_qs(raw)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path in ('/health', '/health/ready'):
            try:
                health_conn = get_db()
                health_conn.cursor().execute("SELECT 1").fetchone()
                health_conn.close()
                return self.send_json({"status": "ok", "database": "postgresql" if USING_POSTGRES else "sqlite"})
            except Exception:
                logger.exception("Health check failed")
                return self.send_json({"status": "error"}, 503)
        
        if path.startswith('/api/'):
            if path.startswith('/api/admin/') and not is_admin_request(self):
                return self.send_json({'error': 'Admin authorization required.'}, 403)
            return self.handle_api_get(path, qs)

        if path == '/admin-portal.html' and not is_admin_request(self):
            self.send_response(302)
            self.send_header('Location', '/index.html')
            self.end_headers()
            return

        # Role dashboards are server-protected as well as client-guarded.
        if path in PROTECTED_ROLE_PAGES:
            uid = current_user_id(self)
            if not uid:
                self.send_response(302)
                self.send_header('Location', '/index.html')
                self.end_headers()
                return
            with get_db() as auth_conn:
                row = auth_conn.execute('SELECT role, status FROM users WHERE id = ?', (uid,)).fetchone()
            if not row or row['status'] == 'suspended' or row['role'] != PROTECTED_ROLE_PAGES[path]:
                self.send_response(302)
                self.send_header('Location', '/index.html')
                self.end_headers()
                return

        # Serve static assets
        if path == '/' or path == '':
            self.path = '/index.html'
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        # Reject cross-origin browser mutations. SameSite cookies remain an additional layer.
        origin = self.headers.get('Origin')
        if origin:
            origin_parts = urllib.parse.urlparse(origin)
            if not origin_parts.netloc or origin_parts.netloc.lower() != self.headers.get('Host', '').lower():
                return self.send_json({'error': 'Cross-origin request blocked.'}, 403)

        # Lightweight per-process abuse throttling for sensitive public endpoints.
        if path == '/api/auth/login' and not _rate_limit_allowed(self, 'login', 10, 600):
            return self.send_json({'error': 'Too many login attempts. Try again in 10 minutes.'}, 429)
        if path == '/api/auth/register' and not _rate_limit_allowed(self, 'register', 5, 600):
            return self.send_json({'error': 'Too many registration attempts. Try again later.'}, 429)

        if path.startswith('/api/'):
            if path.startswith('/api/admin/') and not is_admin_request(self):
                return self.send_json({'error': 'Admin authorization required.'}, 403)
            return self.handle_api_post(path, qs)

        self.send_response(404)
        self.end_headers()

    def handle_api_get(self, path, qs):
        conn = get_db()
        cursor = conn.cursor()

        try:
            # Admin: show users with at least one unexpired authenticated session.
            if path == '/api/admin/active-users':
                now_iso = _utcnow_naive().isoformat()
                cursor.execute("DELETE FROM sessions WHERE expires_at <= ?", (now_iso,))
                conn.commit()
                cursor.execute("""
                SELECT u.id, u.username, u.full_name, u.email, u.phone, u.role,
                       u.location, u.state, u.district, u.city, u.status,
                       MAX(s.created_at) AS login_at,
                       MAX(s.expires_at) AS session_expires_at,
                       COUNT(s.id) AS active_sessions
                FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.role = 'user' AND s.user_id IS NOT NULL
                  AND s.expires_at > ? AND u.status = 'active'
                GROUP BY u.id, u.username, u.full_name, u.email, u.phone, u.role,
                         u.location, u.state, u.district, u.city, u.status
                ORDER BY MAX(s.created_at) DESC
                """, (now_iso,))
                active_users = [dict(row) for row in cursor.fetchall()]
                return self.send_json({"active_users": active_users, "count": len(active_users), "checked_at": now_iso})

            # 1. Auth Me - server session is authoritative.
            if path == '/api/auth/me':
                user_id = current_user_id(self)
                if not user_id:
                    return self.send_json({"error": "Authentication required."}, 401)

                cursor.execute("""
                SELECT u.id, u.username, u.email, u.phone, u.role, u.full_name, u.avatar,
                       u.location, u.state, u.district, u.city, u.village, u.availability,
                       u.bio, u.is_verified, u.status
                FROM users u WHERE u.id = ?
                """, (user_id,))
                user = cursor.fetchone()
                if not user:
                    clear_user_session(self)
                    return self.send_json({"error": "Session user not found."}, 401)

                user_dict = dict(user)
                role_table = {
                    'Player': ('player_profiles', 'player_profile'),
                    'Coach': ('coach_profiles', 'coach_profile'),
                    'Club': ('club_profiles', 'club_profile'),
                    'Organizer': ('organizer_profiles', 'organizer_profile'),
                    'Referee': ('referee_profiles', 'referee_profile'),
                }
                if user_dict['role'] in role_table:
                    table, key = role_table[user_dict['role']]
                    row = cursor.execute(f"SELECT * FROM {table} WHERE user_id = ?", (user_id,)).fetchone()
                    if row:
                        user_dict[key] = dict(row)

                return self.send_json({"user": user_dict})

            # Email existence check used by the email-first sign-in flow.
            if path == '/api/auth/check-email':
                email = str(qs.get('email', [''])[0]).strip().lower()
                if not email:
                    return self.send_json({'error': 'Email required'}, 400)
                cursor.execute('SELECT id, username, role, status FROM users WHERE lower(email) = ?', (email,))
                user = cursor.fetchone()
                return self.send_json({'exists': bool(user), 'user': dict(user) if user else None})

            # 2. Get Players (Advanced Search & Rising Talent)
            elif path == '/api/players':
                sport = qs.get('sport', [None])[0]
                position = qs.get('position', [None])[0]
                location = qs.get('location', [None])[0]
                classification = qs.get('classification', [None])[0]
                min_skill = float(qs.get('min_skill', [0])[0])
                availability = qs.get('availability', [None])[0]
                search = qs.get('q', [None])[0]

                query = """
                SELECT u.id, u.username, u.full_name, u.avatar, u.location, u.bio, u.is_verified,
                       p.sport, p.position, p.experience_years, p.age_group, p.preferred_role,
                       p.availability, p.rating, p.classification, p.skill_score, p.performance_score,
                       p.progress_pct, p.major_matches, p.verified_local_matches
                FROM users u
                JOIN player_profiles p ON u.id = p.user_id
                LEFT JOIN privacy_settings ps ON ps.user_id = u.id
                WHERE u.status = 'active'
                """
                params = []
                viewer_id = current_user_id(self)
                viewer_is_admin = is_admin_request(self)
                if not viewer_is_admin:
                    if viewer_id:
                        query += """ AND (
                            COALESCE(ps.profile_visibility, 'public') = 'public'
                            OR u.id = ?
                            OR (COALESCE(ps.profile_visibility, 'public') = 'connections_only' AND EXISTS (
                                SELECT 1 FROM connections c
                                WHERE c.status = 'accepted'
                                  AND ((c.requester_id = ? AND c.recipient_id = u.id)
                                    OR (c.requester_id = u.id AND c.recipient_id = ?))
                            ))
                        )"""
                        params.extend([viewer_id, viewer_id, viewer_id])
                    else:
                        query += " AND COALESCE(ps.profile_visibility, 'public') = 'public'"
                if sport and sport != 'All':
                    query += " AND p.sport = ?"
                    params.append(sport)
                if position and position != 'All':
                    query += " AND p.position LIKE ?"
                    params.append(f"%{position}%")
                if location:
                    query += " AND (u.location LIKE ? OR u.district LIKE ? OR u.state LIKE ?)"
                    params.extend([f"%{location}%", f"%{location}%", f"%{location}%"])
                if classification and classification != 'All':
                    query += " AND p.classification = ?"
                    params.append(classification)
                if min_skill > 0:
                    query += " AND p.skill_score >= ?"
                    params.append(min_skill)
                if availability and availability != 'All':
                    query += " AND p.availability LIKE ?"
                    params.append(f"%{availability}%")
                if search:
                    query += " AND (u.full_name LIKE ? OR u.username LIKE ? OR p.sport LIKE ? OR p.position LIKE ?)"
                    params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])

                query += " ORDER BY p.classification = 'Rising Talent' DESC, p.skill_score DESC"
                cursor.execute(query, params)
                players = [dict(row) for row in cursor.fetchall()]
                return self.send_json({"players": players})

            # 3. Get Single Player Detailed Sports Resume
            elif path.startswith('/api/players/'):
                player_id = int(path.split('/')[-1])
                cursor.execute("""
                SELECT u.id, u.username, u.full_name, u.avatar, u.location, u.state, u.district, u.bio, u.is_verified,
                       p.sport, p.position, p.experience_years, p.age_group, p.dob, p.preferred_role,
                       p.availability, p.rating, p.classification, p.skill_score, p.performance_score,
                       p.progress_pct, p.major_matches, p.verified_local_matches, p.consistency_score
                FROM users u
                JOIN player_profiles p ON u.id = p.user_id
                WHERE u.id = ?
                """, (player_id,))
                player = cursor.fetchone()
                if not player:
                    return self.send_json({"error": "Player not found"}, 404)
                viewer_id = current_user_id(self)
                viewer_is_admin = is_admin_request(self)
                cursor.execute(
                    "SELECT profile_visibility, stats_visibility, certs_visibility FROM privacy_settings WHERE user_id = ?",
                    (player_id,),
                )
                privacy_row = cursor.fetchone()
                privacy = dict(privacy_row) if privacy_row else {
                    'profile_visibility': 'public', 'stats_visibility': 'public', 'certs_visibility': 'public'
                }
                is_owner = bool(viewer_id and str(viewer_id) == str(player_id))
                is_connected = False
                if viewer_id and not is_owner:
                    cursor.execute(
                        "SELECT 1 FROM connections WHERE status = 'accepted' AND ((requester_id = ? AND recipient_id = ?) OR (requester_id = ? AND recipient_id = ?)) LIMIT 1",
                        (viewer_id, player_id, player_id, viewer_id),
                    )
                    is_connected = cursor.fetchone() is not None
                if not can_view_visibility(privacy['profile_visibility'], is_admin=viewer_is_admin, is_owner=is_owner, is_connected=is_connected):
                    return self.send_json({"error": "Player profile is private."}, 404)
                player_data = dict(player)

                if can_view_visibility(privacy['stats_visibility'], is_admin=viewer_is_admin, is_owner=is_owner, is_connected=is_connected):
                    cursor.execute("SELECT * FROM sports_tests WHERE player_id = ? ORDER BY date_taken DESC", (player_id,))
                    player_data['tests'] = [dict(r) for r in cursor.fetchall()]
                else:
                    player_data['tests'] = []
                    for key in ('rating', 'skill_score', 'performance_score', 'progress_pct', 'major_matches',
                                'verified_local_matches', 'consistency_score'):
                        player_data[key] = None

                if can_view_visibility(privacy['certs_visibility'], is_admin=viewer_is_admin, is_owner=is_owner, is_connected=is_connected):
                    cursor.execute("SELECT * FROM certificates WHERE player_id = ? ORDER BY year DESC", (player_id,))
                    player_data['certificates'] = [dict(r) for r in cursor.fetchall()]
                else:
                    player_data['certificates'] = []

                # Match history follows the same stats visibility policy.
                if can_view_visibility(privacy['stats_visibility'], is_admin=viewer_is_admin, is_owner=is_owner, is_connected=is_connected):
                    cursor.execute("""
                    SELECT m.id AS match_id, m.title, m.sport, m.team_a, m.team_b, m.match_date, m.location,
                           m.result_summary, m.status AS match_status, m.verified_by,
                           mps.team_name, mps.role_played, mps.stats_json, mps.performance_rating, mps.verified_status
                    FROM match_player_stats mps JOIN matches m ON mps.match_id = m.id
                    WHERE mps.player_id = ? ORDER BY m.match_date DESC
                    """, (player_id,))
                    player_data['matches'] = []
                    for row in cursor.fetchall():
                        item = dict(row)
                        try:
                            item['stats'] = json.loads(item.get('stats_json') or '{}')
                        except (TypeError, ValueError):
                            item['stats'] = {}
                        player_data['matches'].append(item)
                else:
                    player_data['matches'] = []
                return self.send_json({"player": player_data})

            # 4. Certificates
            elif path == '/api/certificates':
                viewer_id = current_user_id(self)
                viewer_is_admin = is_admin_request(self)
                requested_player = qs.get('player_id', [None])[0]
                if requested_player:
                    try:
                        requested_player_id = int(requested_player)
                    except (TypeError, ValueError):
                        return self.send_json({"error": "Invalid player_id."}, 400)
                    cursor.execute("SELECT certs_visibility FROM privacy_settings WHERE user_id = ?", (requested_player_id,))
                    privacy_row = cursor.fetchone()
                    visibility = privacy_row['certs_visibility'] if privacy_row else 'public'
                    own = bool(viewer_id and str(viewer_id) == str(requested_player_id))
                    connected = False
                    if viewer_id and not own:
                        cursor.execute("SELECT 1 FROM connections WHERE status = 'accepted' AND ((requester_id = ? AND recipient_id = ?) OR (requester_id = ? AND recipient_id = ?)) LIMIT 1", (viewer_id, requested_player_id, requested_player_id, viewer_id))
                        connected = cursor.fetchone() is not None
                    if not can_view_visibility(visibility, is_admin=viewer_is_admin, is_owner=own, is_connected=connected):
                        return self.send_json({"error": "Certificates are private."}, 404)
                    cursor.execute("SELECT * FROM certificates WHERE player_id = ? ORDER BY id DESC", (requested_player_id,))
                elif viewer_is_admin:
                    cursor.execute("SELECT c.*, u.full_name AS player_name, u.avatar AS player_avatar FROM certificates c JOIN users u ON c.player_id = u.id ORDER BY c.id DESC")
                else:
                    cursor.execute("""
                    SELECT c.*, u.full_name AS player_name, u.avatar AS player_avatar
                    FROM certificates c JOIN users u ON c.player_id = u.id
                    LEFT JOIN privacy_settings ps ON ps.user_id = c.player_id
                    WHERE COALESCE(ps.certs_visibility, 'public') = 'public'
                    ORDER BY c.id DESC
                    """)
                certs = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"certificates": certs})

            # 5. Matches & Tournaments
            elif path == '/api/matches':
                cursor.execute("""
                SELECT m.*, t.title as tournament_name
                FROM matches m
                LEFT JOIN tournaments t ON m.tournament_id = t.id
                ORDER BY m.match_date DESC
                """)
                matches = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"matches": matches})

            elif path == '/api/tournaments':
                cursor.execute("""
                SELECT t.*, u.full_name as organizer_name
                FROM tournaments t
                JOIN users u ON t.organizer_id = u.id
                ORDER BY t.start_date DESC
                """)
                tournaments = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"tournaments": tournaments})

            # 6. Trials
            elif path == '/api/trials':
                cursor.execute("""
                SELECT tr.*, u.full_name as host_name, u.role as host_role
                FROM trials tr
                JOIN users u ON tr.creator_id = u.id
                ORDER BY tr.trial_date ASC
                """)
                trials = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"trials": trials})

            # 7. Connections
            elif path == '/api/connections':
                user_id = current_user_id(self)
                if not user_id:
                    return self.send_json({"error": "Authentication required."}, 401)
                cursor.execute("""
                SELECT c.id, c.status, c.created_at,
                       CASE WHEN c.requester_id = ? THEN c.recipient_id ELSE c.requester_id END AS other_user_id,
                       u.full_name, u.role, u.avatar, u.location
                FROM connections c
                JOIN users u ON (CASE WHEN c.requester_id = ? THEN c.recipient_id ELSE c.requester_id END) = u.id
                WHERE (c.requester_id = ? OR c.recipient_id = ?)
                ORDER BY c.created_at DESC
                """, (user_id, user_id, user_id, user_id))
                connections = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"connections": connections})

            # 8. Messages
            elif path == '/api/messages':
                user_id = current_user_id(self)
                other_id = qs.get('other_id', [None])[0]
                if not user_id:
                    return self.send_json({"error": "Authentication required."}, 401)
                if other_id:
                    cursor.execute("""
                    SELECT m.*, u.full_name as sender_name, u.avatar as sender_avatar
                    FROM messages m
                    JOIN users u ON m.sender_id = u.id
                    WHERE (m.sender_id = ? AND m.recipient_id = ?) OR (m.sender_id = ? AND m.recipient_id = ?)
                    ORDER BY m.timestamp ASC
                    """, (user_id, other_id, other_id, user_id))
                else:
                    cursor.execute("""
                    SELECT m.*, u.full_name as sender_name, u.avatar as sender_avatar
                    FROM messages m
                    JOIN users u ON m.sender_id = u.id
                    WHERE m.sender_id = ? OR m.recipient_id = ?
                    ORDER BY m.timestamp DESC
                    """, (user_id, user_id))
                messages = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"messages": messages})

            # 9. Notifications
            elif path == '/api/notifications':
                user_id = current_user_id(self)
                if not user_id:
                    return self.send_json({"error": "Authentication required."}, 401)
                cursor.execute("""
                SELECT * FROM notifications WHERE user_id = ? ORDER BY timestamp DESC LIMIT 30
                """, (user_id,))
                notifs = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"notifications": notifs})

            # 10. Saved Talent
            elif path == '/api/saved-talent':
                user_id = current_user_id(self)
                if not user_id:
                    return self.send_json({"error": "Authentication required."}, 401)
                cursor.execute("""
                SELECT st.id as bookmark_id, st.notes, st.saved_at,
                       u.id, u.full_name, u.avatar, u.location,
                       p.sport, p.position, p.classification, p.rating, p.skill_score, p.progress_pct, p.availability
                FROM saved_talent st
                JOIN users u ON st.player_id = u.id
                JOIN player_profiles p ON u.id = p.user_id
                WHERE st.user_id = ?
                ORDER BY st.saved_at DESC
                """, (user_id,))
                saved = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"saved": saved})

            # 11. Reports (Admin / User)
            elif path == '/api/reports':
                user_id = current_user_id(self)
                is_admin = is_admin_request(self)
                if is_admin:
                    cursor.execute("""
                    SELECT r.*, 
                           u_rep.full_name as reporter_name, u_rep.role as reporter_role,
                           u_tgt.full_name as reported_user_name, u_tgt.role as reported_user_role
                    FROM reports r
                    JOIN users u_rep ON r.reporter_id = u_rep.id
                    JOIN users u_tgt ON r.reported_user_id = u_tgt.id
                    ORDER BY r.id DESC
                    """)
                elif user_id:
                    cursor.execute("""
                    SELECT r.*, u_tgt.full_name as reported_user_name
                    FROM reports r
                    JOIN users u_tgt ON r.reported_user_id = u_tgt.id
                    WHERE r.reporter_id = ?
                    ORDER BY r.id DESC
                    """, (user_id,))
                else:
                    return self.send_json({"error": "Authentication required."}, 401)
                reports = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"reports": reports})

            # 12. Admin Stats & Verification Queues
            elif path == '/api/admin/session':
                return self.send_json({"success": True, "user": {"id": 0, "username": ADMIN_USERNAME, "role": "Admin", "full_name": "SportsConnect Administrator"}})

            elif path == '/api/admin/users':
                cursor.execute("""
                    SELECT u.id, u.username, u.email, u.phone, u.role, u.full_name, u.avatar,
                           u.location, u.state, u.district, u.status, u.is_verified, u.created_at,
                           COALESCE(
                               (SELECT p.sport FROM player_profiles p WHERE p.user_id = u.id),
                               (SELECT c.sport FROM coach_profiles c WHERE c.user_id = u.id),
                               (SELECT cl.sport FROM club_profiles cl WHERE cl.user_id = u.id),
                               (SELECT o.sport FROM organizer_profiles o WHERE o.user_id = u.id),
                               (SELECT r.sport FROM referee_profiles r WHERE r.user_id = u.id),
                               ''
                           ) AS sport_or_org,
                           COALESCE(
                               (SELECT cl.club_name FROM club_profiles cl WHERE cl.user_id = u.id),
                               (SELECT o.organization_name FROM organizer_profiles o WHERE o.user_id = u.id),
                               ''
                           ) AS organization_name
                    FROM users u
                    WHERE u.role != 'Admin'
                    ORDER BY u.created_at DESC, u.id DESC
                """)
                return self.send_json({"users": [dict(r) for r in cursor.fetchall()]})

            elif path == '/api/admin/stats':
                stats = {}
                cursor.execute("SELECT COUNT(*) FROM users")
                stats['total_users'] = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'Player'")
                stats['total_players'] = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'Coach'")
                stats['total_coaches'] = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'Club'")
                stats['total_clubs'] = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'Organizer'")
                stats['total_organizers'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM certificates WHERE status = 'pending'")
                stats['pending_certificates'] = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM coach_profiles WHERE verification_status = 'pending'")
                stats['pending_coach_verifications'] = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM club_profiles WHERE verification_status = 'pending'")
                stats['pending_club_verifications'] = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM organizer_profiles WHERE verification_status = 'pending'")
                stats['pending_organizer_verifications'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM reports WHERE status = 'Under Review' OR status = 'More Information Needed'")
                stats['open_reports'] = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM tournaments WHERE status = 'Active'")
                stats['active_tournaments'] = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM player_profiles WHERE classification = 'Rising Talent'")
                stats['rising_talent_count'] = cursor.fetchone()[0]

                return self.send_json({"stats": stats})

            elif path == '/api/admin/rising-talent':
                cursor.execute("""
                SELECT u.id, u.full_name, u.avatar, u.location,
                       p.sport, p.position, p.skill_score, p.performance_score, p.progress_pct,
                       p.major_matches, p.verified_local_matches, p.rating, p.classification,
                       (SELECT COUNT(*) FROM certificates WHERE player_id = u.id AND status = 'verified') as verified_certs_count
                FROM users u
                JOIN player_profiles p ON u.id = p.user_id
                WHERE p.classification = 'Rising Talent' OR p.skill_score >= 80
                ORDER BY p.skill_score DESC
                """)
                talent = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"rising_talent": talent})

            else:
                return self.send_json({"error": "Endpoint not found"}, 404)

        except Exception:
            conn.rollback()
            logger.exception("Unhandled GET API error: %s", path)
            return self.send_json({"error": "Internal server error."}, 500)
        finally:
            conn.close()

    def handle_api_post(self, path, qs):
        body = self.parse_body()
        conn = get_db()
        cursor = conn.cursor()

        try:
            # 1. Update authenticated profile
            if path == '/api/profile':
                user_id = current_user_id(self)
                if not user_id:
                    return self.send_json({'error': 'Authentication required.'}, 401)

                user = cursor.execute('SELECT id, role FROM users WHERE id = ?', (user_id,)).fetchone()
                if not user:
                    return self.send_json({'error': 'Authenticated user not found.'}, 401)

                allowed_user = ['full_name','email','phone','location','state','district','city','village','availability','bio']
                changes = {}
                for field in allowed_user:
                    if field in body:
                        value = body.get(field)
                        if value is not None:
                            changes[field] = str(value).strip()

                if 'full_name' in changes and not changes['full_name']:
                    return self.send_json({'error': 'Full name cannot be empty.'}, 400)

                if 'email' in changes:
                    email = changes['email'].lower()
                    other = cursor.execute('SELECT id FROM users WHERE email = ? AND id != ?', (email, user_id)).fetchone()
                    if other:
                        return self.send_json({'error': 'Email already registered.'}, 409)
                    changes['email'] = email

                if changes:
                    assignments = ', '.join(f'{k} = ?' for k in changes)
                    cursor.execute(f'UPDATE users SET {assignments} WHERE id = ?', (*changes.values(), user_id))

                role = user['role']
                role_fields = {
                    'Player': ('player_profiles', ['sport','position','experience_years','age_group','preferred_role','availability']),
                    'Coach': ('coach_profiles', ['sport','experience_years','specialization','certifications','current_org']),
                    'Club': ('club_profiles', ['sport','club_name','established_year','home_ground','division']),
                    'Organizer': ('organizer_profiles', ['organization_name','sport','registration_no']),
                    'Referee': ('referee_profiles', ['sport','level','official_role','experience_years','certification','availability'])
                }
                if role in role_fields:
                    table, fields = role_fields[role]
                    role_values = {k: body[k] for k in fields if k in body and body[k] is not None}
                    if 'availability' in role_values:
                        role_values['availability'] = str(role_values['availability']).strip()
                    if role_values:
                        assignments = ', '.join(f'{k} = ?' for k in role_values)
                        cursor.execute(f'UPDATE {table} SET {assignments} WHERE user_id = ?', (*role_values.values(), user_id))

                conn.commit()
                # Reuse /api/auth/me representation after update by redirecting through a small in-process query.
                row = cursor.execute('SELECT id, username, email, phone, role, full_name, avatar, location, state, district, city, village, availability, bio, is_verified, status FROM users WHERE id = ?', (user_id,)).fetchone()
                result = dict(row)
                table_map = {'Player':'player_profiles','Coach':'coach_profiles','Club':'club_profiles','Organizer':'organizer_profiles','Referee':'referee_profiles'}
                if role in table_map:
                    prow = cursor.execute(f'SELECT * FROM {table_map[role]} WHERE user_id = ?', (user_id,)).fetchone()
                    if prow: result[role.lower() + '_profile'] = dict(prow)
                return self.send_json({'success': True, 'user': result})

            # 2. Login
            if path == '/api/auth/login':
                identifier = str(body.get('identifier', '')).strip()
                password = str(body.get('password', ''))

                if not identifier or not password:
                    return self.send_json({"error": "Identifier and password required"}, 400)

                # Admin is a separate protected identity. No database/demo admin can authenticate.
                if identifier.lower() == ADMIN_USERNAME.lower() or identifier.lower() == 'admin@sportsconnect.com':
                    if ADMIN_PASSWORD and identifier.lower() == ADMIN_USERNAME.lower() and password == ADMIN_PASSWORD:
                        totp_secret = os.getenv('ADMIN_TOTP_SECRET', '').strip()
                        if totp_secret and not verify_totp(totp_secret, body.get('totp_code', '')):
                            return self.send_json({'error': 'A valid administrator authenticator code is required.'}, 401)
                        if not totp_secret and os.getenv('ADMIN_TOTP_REQUIRED', '').lower() in ('1', 'true', 'yes'):
                            logger.error("ADMIN_TOTP_REQUIRED is enabled but ADMIN_TOTP_SECRET is missing")
                            return self.send_json({'error': 'Administrator MFA is not configured. Contact the platform operator.'}, 503)
                        token = issue_admin_session()
                        admin_user = {
                            'id': 0, 'username': ADMIN_USERNAME, 'email': 'admin@sportsconnect.local',
                            'phone': '', 'role': 'Admin', 'full_name': 'SportsConnect Administrator',
                            'avatar': '🛡️', 'location': 'Platform Headquarters', 'status': 'active', 'is_verified': 1
                        }
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Set-Cookie', f'sc_admin_session={token}; Path=/; HttpOnly; SameSite=Lax{COOKIE_SECURE_FLAG}; Max-Age={SESSION_TTL_HOURS*3600}')
                        payload = json.dumps({'success': True, 'user': admin_user}).encode('utf-8')
                        self.send_header('Content-Length', str(len(payload)))
                        self.end_headers()
                        self.wfile.write(payload)
                        return
                    return self.send_json({'error': 'Invalid Admin credentials.'}, 401)

                cursor.execute("""
                SELECT id, username, email, phone, password_hash, role, full_name, avatar, location, status
                FROM users
                WHERE lower(email) = ? OR phone = ? OR lower(username) = ?
                """, (identifier.lower(), identifier, identifier.lower()))
                user = cursor.fetchone()
                if not user or not verify_pw(password, user["password_hash"]):
                    return self.send_json({"error": "Invalid credentials. If this email is new, create a new account.", "account_exists": False if '@' in identifier else None}, 401)

                # Seamlessly upgrade an old SHA-256 password after a successful login.
                if not str(user["password_hash"]).startswith("pbkdf2_sha256$"):
                    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_pw(password), user["id"]))
                    conn.commit()

                user_dict = dict(user)
                if user_dict['role'] == 'Admin':
                    return self.send_json({'error': 'Admin accounts are restricted to the authorized administrator.'}, 403)
                if user_dict['status'] == 'suspended':
                    return self.send_json({"error": "Account has been suspended. Please contact integrity support."}, 403)
                del user_dict['password_hash']
                token = issue_user_session(user_dict['id'])
                return self.send_json(
                    {"success": True, "user": user_dict},
                    200,
                    [f'sc_session={urllib.parse.quote(token)}; Path=/; HttpOnly; SameSite=Lax{COOKIE_SECURE_FLAG}; Max-Age={SESSION_TTL_HOURS*3600}']
                )

            # Admin logout invalidates the server-side admin session token.
            elif path == '/api/auth/logout':
                clear_user_session(self)
                admin_token = _cookie_value(self, 'sc_admin_session')
                if admin_token:
                    conn2 = get_db()
                    try:
                        conn2.cursor().execute("DELETE FROM sessions WHERE token_hash = ? AND role = 'admin'", (_token_hash(admin_token),))
                        conn2.commit()
                    finally:
                        conn2.close()
                return self.send_json(
                    {'success': True},
                    200,
                    [
                        f'sc_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax{COOKIE_SECURE_FLAG}',
                        f'sc_admin_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax{COOKIE_SECURE_FLAG}'
                    ]
                )

            # 3. Register
            elif path == '/api/auth/register':
                role = body.get('role', 'Player')
                if role not in ('Player', 'Coach', 'Club', 'Organizer', 'Referee'):
                    return self.send_json({'error': 'Invalid account role.'}, 400)
                username = body.get('username', '').strip().lower()
                if username == ADMIN_USERNAME.lower() or username == 'admin':
                    return self.send_json({'error': 'Admin accounts cannot be created through public registration.'}, 403)
                email = body.get('email', '').strip().lower()
                phone = body.get('phone', '').strip()
                password = body.get('password', '')
                full_name = body.get('full_name', '').strip()
                location = body.get('location', 'Hyderabad')
                state = body.get('state', '')
                district = body.get('district', '')
                city = body.get('city', '')
                village = body.get('village', '')
                sport = body.get('sport', 'Cricket')
                availability = body.get('availability', '')

                if not username or not email or not phone or not password or not full_name:
                    return self.send_json({"error": "All required fields must be filled."}, 400)
                import re
                if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{8,}$', password):
                    return self.send_json({"error": "Password must be at least 8 characters and include uppercase, lowercase, number, and special character."}, 400)
                cursor.execute("SELECT id FROM users WHERE username = ? OR email = ? OR phone = ?", (username, email, phone))
                if cursor.fetchone():
                    return self.send_json({"error": "Username, Email or Phone already registered."}, 409)

                now = datetime.now().isoformat()
                cursor.execute("""
                INSERT INTO users (username, email, phone, password_hash, role, full_name, avatar, location, state, district, city, village, availability, bio, is_verified, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', ?)
                """, (username, email, phone, hash_pw(password), role, full_name, '🏃' if role=='Player' else '👤', location, state, district, city, village, availability, 'SportsConnect Member', now))
                user_id = cursor.lastrowid

                # Create profile based on role
                if role == 'Player':
                    pos = body.get('position', 'Batsman')
                    exp = float(body.get('experience_years', 1.0))
                    age = body.get('age_group', 'Under-21')
                    cursor.execute("""
                    INSERT INTO player_profiles (user_id, sport, position, experience_years, age_group, preferred_role, availability, rating, classification, skill_score, performance_score, progress_pct, major_matches, verified_local_matches)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 8.0, 'Rising Talent', 82.0, 80.0, 16.0, 0, 1)
                    """, (user_id, sport, pos, exp, age, pos, availability))
                elif role == 'Coach':
                    cursor.execute("""
                    INSERT INTO coach_profiles (user_id, sport, experience_years, specialization, certifications, current_org, verification_status)
                    VALUES (?, ?, 3.0, 'Head Coach', 'State Certified', 'Regional Club', 'pending')
                    """, (user_id, sport))
                elif role == 'Club':
                    cursor.execute("""
                    INSERT INTO club_profiles (user_id, sport, club_name, established_year, home_ground, division, verification_status)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending')
                    """, (
                        user_id, sport, full_name,
                        int(body.get('established_year') or 2020),
                        body.get('home_ground') or 'Local Stadium',
                        body.get('division') or 'District League'
                    ))
                elif role == 'Organizer':
                    cursor.execute("""
                    INSERT INTO organizer_profiles (user_id, organization_name, sport, registration_no, verification_status)
                    VALUES (?, ?, ?, 'ORG-PENDING', 'pending')
                    """, (user_id, full_name, sport))
                elif role == 'Referee':
                    cursor.execute("""
                    INSERT INTO referee_profiles (user_id, sport, level, official_role, experience_years, certification, availability, verification_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
                    """, (user_id, sport, body.get('refereeing_level',''), body.get('position',''), float(body.get('experience_years') or 0), body.get('certification',''), availability))

                # Preserve structured availability for coach/other profiles where the schema supports it
                if role == 'Coach':
                    cursor.execute("UPDATE coach_profiles SET current_org = ? WHERE user_id = ?", (body.get('current_team','') or None, user_id))

                # Default privacy
                cursor.execute("""
                INSERT INTO privacy_settings (user_id, profile_visibility, contact_visibility, stats_visibility, certs_visibility, connections_visibility)
                VALUES (?, 'public', 'connections_only', 'public', 'public', 'public')
                """, (user_id,))

                conn.commit()
                # Return the complete newly-created user so the frontend can establish
                # the real session immediately instead of falling back to demo Rahul.
                cursor.execute("""
                    SELECT id, username, email, phone, role, full_name, avatar, location,
                           state, district, city, village, availability, bio, is_verified, status
                    FROM users WHERE id = ?
                """, (user_id,))
                created_user = dict(cursor.fetchone())
                if role == 'Player':
                    cursor.execute("SELECT * FROM player_profiles WHERE user_id = ?", (user_id,))
                    profile = cursor.fetchone()
                    if profile:
                        created_user.update({
                            'sport': profile['sport'],
                            'position': profile['position'],
                            'skill_level': body.get('skill_level', ''),
                            'rating': profile['rating'],
                            'classification': profile['classification'],
                            'skill_score': profile['skill_score'],
                            'performance_score': profile['performance_score'],
                            'progress_pct': profile['progress_pct'],
                            'major_matches': profile['major_matches'],
                            'verified_local_matches': profile['verified_local_matches']
                        })
                conn.commit()
                session_token = issue_user_session(user_id)
                return self.send_json({"success": True, "user_id": user_id, "user": created_user, "message": "Account created successfully."}, 200, [f'sc_session={urllib.parse.quote(session_token)}; Path=/; HttpOnly; SameSite=Lax{COOKIE_SECURE_FLAG}; Max-Age={SESSION_TTL_HOURS*3600}'])

            # 3. Smart Matching Engine
            elif path == '/api/matching':
                criteria = body # {sport, position, location, min_skill, availability}
                req_sport = criteria.get('sport', 'Cricket')

                cursor.execute("""
                SELECT u.id, u.full_name, u.avatar, u.location,
                       p.sport, p.position, p.classification, p.rating, p.skill_score, p.performance_score, p.progress_pct, p.availability
                FROM users u
                JOIN player_profiles p ON u.id = p.user_id
                WHERE u.status = 'active' AND p.sport = ?
                """, (req_sport,))
                candidates = [dict(r) for r in cursor.fetchall()]

                matched_results = []
                for candidate in candidates:
                    match_pct, reasons = smart_match(candidate, criteria)
                    matched_results.append({
                        "player": candidate,
                        "match_pct": match_pct,
                        "reasons": reasons
                    })

                matched_results.sort(key=lambda x: x['match_pct'], reverse=True)
                return self.send_json({"matches": matched_results})

            # 4. Upload / Submit Certificate
            elif path == '/api/certificates':
                player_id = int(body.get('player_id') or 0)
                auth_id = current_user_id(self)
                if not auth_id and not is_admin_request(self):
                    return self.send_json({"error": "Authentication required."}, 401)
                if not is_admin_request(self) and player_id != auth_id:
                    return self.send_json({"error": "You may only manage your own certificates."}, 403)
                title = body.get('title')
                issuing_org = body.get('issuing_org')
                year = int(body.get('year', 2025))
                achievement_text = body.get('achievement_text', '')
                file_name = body.get('file_name', 'certificate_upload.pdf')

                if not player_id or not title or not issuing_org:
                    return self.send_json({"error": "Player, Title and Issuing Organization required"}, 400)

                now = datetime.now().isoformat()
                cursor.execute("""
                INSERT INTO certificates (player_id, title, issuing_org, year, achievement_text, file_name, file_url, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                """, (player_id, title, issuing_org, year, achievement_text, file_name, f"/certs/{file_name}", now))
                cert_id = cursor.lastrowid

                # Notify admin & user
                cursor.execute("""
                INSERT INTO notifications (user_id, category, title, message, link, timestamp)
                VALUES (?, 'Verification', '🟡 Certificate Submitted', 'Your certificate has entered the verification queue.', '#certificates', ?)
                """, (player_id, now))

                conn.commit()
                return self.send_json({"success": True, "certificate_id": cert_id, "status": "pending"})

            # 5. Admin Certificate Verification (Verify / Reject)
            elif path.startswith('/api/certificates/') and path.endswith('/verify'):
                if not is_admin_request(self):
                    return self.send_json({'error': 'Admin authorization required.'}, 403)
                cert_id = int(path.split('/')[-2])
                action = body.get('action') # 'verify' or 'reject'
                reason = body.get('reason', '')
                admin_name = 'Platform Admin'
                if action not in ('verify', 'reject'):
                    return self.send_json({'error': "Action must be 'verify' or 'reject'."}, 400)
                if action == 'reject' and not str(reason).strip():
                    return self.send_json({'error': 'A rejection reason is required.'}, 400)

                status = 'verified' if action == 'verify' else 'rejected'
                now = datetime.now().isoformat()

                cursor.execute("""
                UPDATE certificates 
                SET status = ?, verified_by = ?, verified_at = ?, rejection_reason = ?
                WHERE id = ?
                """, (status, admin_name, now, reason if status == 'rejected' else None, cert_id))

                # Fetch player to update classification and notify
                cursor.execute("SELECT player_id, title FROM certificates WHERE id = ?", (cert_id,))
                row = cursor.fetchone()
                if row:
                    p_id, c_title = row[0], row[1]
                    notif_icon = '🟢' if status == 'verified' else '❌'
                    notif_msg = f"Your certificate '{c_title}' has been verified!" if status == 'verified' else f"Your certificate '{c_title}' was rejected: {reason}"
                    cursor.execute("""
                    INSERT INTO notifications (user_id, category, title, message, link, timestamp)
                    VALUES (?, 'Verification', ?, ?, '#certificates', ?)
                    """, (p_id, f"{notif_icon} Certificate {status.capitalize()}", notif_msg, now))

                    # Recalculate classification
                    cursor.execute("""
                    SELECT skill_score, performance_score, progress_pct, major_matches,
                           (SELECT COUNT(*) FROM certificates WHERE player_id = ? AND status = 'verified')
                    FROM player_profiles WHERE user_id = ?
                    """, (p_id, p_id))
                    p_info = cursor.fetchone()
                    if p_info:
                        new_cls, new_comp = calculate_player_classification(p_info[0], p_info[1], p_info[2], p_info[3], p_info[4])
                        cursor.execute("UPDATE player_profiles SET classification = ? WHERE user_id = ?", (new_cls, p_id))

                conn.commit()
                return self.send_json({"success": True, "status": status})

            # 6. Official Match Submission (By Organizer/Club)
            elif path == '/api/matches':
                auth_id = current_user_id(self)
                if not auth_id:
                    return self.send_json({"error": "Authentication required."}, 401)
                auth_row = cursor.execute("SELECT role, full_name FROM users WHERE id = ?", (auth_id,)).fetchone()
                if not auth_row or auth_row["role"] not in ("Organizer", "Club") and not is_admin_request(self):
                    return self.send_json({"error": "Only organizers, clubs, or admins may submit official matches."}, 403)
                organizer_name = auth_row["full_name"] if auth_row else "Authorized Organizer"
                sport = body.get('sport', 'Cricket')
                title = body.get('title')
                team_a = body.get('team_a')
                team_b = body.get('team_b')
                match_date = body.get('match_date', datetime.now().strftime('%Y-%m-%d'))
                location = body.get('location', 'Stadium')
                result_summary = body.get('result_summary', '')
                score_a = body.get('score_a', '')
                score_b = body.get('score_b', '')
                players_stats = body.get('players_stats', []) # list of {player_id, team_name, role_played, stats_json, rating}

                cursor.execute("""
                INSERT INTO matches (sport, title, team_a, team_b, match_date, location, result_summary, score_a, score_b, status, verified_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'verified', ?)
                """, (sport, title, team_a, team_b, match_date, location, result_summary, score_a, score_b, organizer_name))
                match_id = cursor.lastrowid

                for ps in players_stats:
                    p_id = ps['player_id']
                    stats_json = json.dumps(ps.get('stats', {}))
                    rating = float(ps.get('rating', 8.5))
                    cursor.execute("""
                    INSERT INTO match_player_stats (match_id, player_id, team_name, role_played, stats_json, performance_rating, verified_status)
                    VALUES (?, ?, ?, ?, ?, ?, 'verified')
                    """, (match_id, p_id, ps['team_name'], ps['role_played'], stats_json, rating))

                    # Update player verified local match count
                    cursor.execute("""
                    UPDATE player_profiles 
                    SET verified_local_matches = verified_local_matches + 1,
                        performance_score = ROUND(CAST((performance_score * 0.8) + (? * 0.2) AS numeric), 1)
                    WHERE user_id = ?
                    """, (rating * 10, p_id))

                    # Notify player
                    now = datetime.now().isoformat()
                    cursor.execute("""
                    INSERT INTO notifications (user_id, category, title, message, link, timestamp)
                    VALUES (?, 'Matches', '🟢 Verified Match Added', ?, '#matches', ?)
                    """, (p_id, f"Official match scorecard recorded: {title}. Stats verified by {organizer_name}.", now))

                conn.commit()
                return self.send_json({"success": True, "match_id": match_id})

            # 7. Post Trial & Trial Application
            elif path == '/api/trials':
                creator_id = int(body.get('creator_id') or 0)
                auth_id = current_user_id(self)
                if not auth_id:
                    return self.send_json({"error": "Authentication required."}, 401)
                if creator_id != auth_id:
                    return self.send_json({"error": "You may only create trials for your own account."}, 403)
                sport = body.get('sport', 'Cricket')
                position = body.get('position', 'Batsman')
                title = body.get('title')
                trial_date = body.get('trial_date')
                trial_time = body.get('trial_time')
                location = body.get('location')
                requirements = body.get('requirements', '')
                slots = int(body.get('slots', 10))

                cursor.execute("""
                INSERT INTO trials (creator_id, sport, position, title, trial_date, trial_time, location, requirements, slots, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open')
                """, (creator_id, sport, position, title, trial_date, trial_time, location, requirements, slots))
                trial_id = cursor.lastrowid
                conn.commit()
                return self.send_json({"success": True, "trial_id": trial_id})

            elif path == '/api/trials/invite':
                trial_id = body.get('trial_id')
                player_id = body.get('player_id')
                creator_id = current_user_id(self)
                if not creator_id:
                    return self.send_json({"error": "Authentication required."}, 401)

                cursor.execute("SELECT title, trial_date, location, creator_id FROM trials WHERE id = ?", (trial_id,))
                t = cursor.fetchone()
                if not t:
                    return self.send_json({"error": "Trial not found."}, 404)
                if int(t["creator_id"]) != int(creator_id):
                    return self.send_json({"error": "You may only invite players to your own trials."}, 403)
                now = datetime.now().isoformat()

                cursor.execute("""
                INSERT INTO trial_applications (trial_id, player_id, status, created_at)
                VALUES (?, ?, 'invited', ?)
                """, (trial_id, player_id, now))

                # Notify player
                cursor.execute("""
                INSERT INTO notifications (user_id, category, title, message, link, timestamp)
                VALUES (?, 'Opportunities', '🏏 Trial Invitation', ?, '#trials', ?)
                """, (player_id, f"You have been invited to trial: {t[0]} on {t[1]} at {t[2]}.", now))

                conn.commit()
                return self.send_json({"success": True, "message": "Player invited for trial."})

            elif path == '/api/trials/respond':
                auth_id = current_user_id(self)
                app_id = body.get('application_id')
                trial_id = body.get('trial_id')
                player_id = body.get('player_id')
                response_status = str(body.get('status') or '').strip().lower() # 'accepted' or 'declined'

                if not auth_id:
                    return self.send_json({"error": "Authentication required."}, 401)
                if response_status not in ("accepted", "declined"):
                    return self.send_json({"error": "Invalid trial response status."}, 400)

                if app_id:
                    cursor.execute("SELECT player_id FROM trial_applications WHERE id = ?", (app_id,))
                    application = cursor.fetchone()
                    if not application:
                        return self.send_json({"error": "Trial application not found."}, 404)
                    if int(application["player_id"]) != int(auth_id):
                        return self.send_json({"error": "You can only respond to your own trial applications."}, 403)
                    cursor.execute("UPDATE trial_applications SET status = ? WHERE id = ?", (response_status, app_id))
                elif trial_id and player_id:
                    if int(player_id) != int(auth_id):
                        return self.send_json({"error": "You can only respond to your own trial applications."}, 403)
                    cursor.execute(
                        "UPDATE trial_applications SET status = ? WHERE trial_id = ? AND player_id = ?",
                        (response_status, trial_id, player_id),
                    )
                else:
                    return self.send_json({"error": "Application or trial/player identifiers are required."}, 400)

                if cursor.rowcount == 0:
                    return self.send_json({"error": "Trial application not found."}, 404)
                conn.commit()
                return self.send_json({"success": True, "status": response_status})

            # 8. Connections & Messages
            elif path == '/api/connections':
                requester_id = current_user_id(self)
                recipient_id = body.get('recipient_id')
                if not requester_id:
                    return self.send_json({"error": "Authentication required."}, 401)

                now = datetime.now().isoformat()
                cursor.execute("""
                INSERT INTO connections (requester_id, recipient_id, status, created_at)
                VALUES (?, ?, 'pending', ?)
                """, (requester_id, recipient_id, now))

                # Notify recipient
                cursor.execute("SELECT full_name FROM users WHERE id = ?", (requester_id,))
                req_name = cursor.fetchone()[0]
                cursor.execute("""
                INSERT INTO notifications (user_id, category, title, message, link, timestamp)
                VALUES (?, 'Connections', '🤝 Connection Request', ?, '#network', ?)
                """, (recipient_id, f"{req_name} sent you a connection request.", now))

                conn.commit()
                return self.send_json({"success": True, "message": "Connection request sent."})

            elif path == '/api/connections/respond':
                auth_id = current_user_id(self)
                conn_id = body.get('connection_id')
                status = str(body.get('status') or '').strip().lower() # 'accepted' or 'declined'

                if not auth_id:
                    return self.send_json({"error": "Authentication required."}, 401)
                if status not in ("accepted", "declined"):
                    return self.send_json({"error": "Invalid connection response status."}, 400)

                cursor.execute(
                    "SELECT requester_id, recipient_id, status FROM connections WHERE id = ?",
                    (conn_id,),
                )
                connection = cursor.fetchone()
                if not connection:
                    return self.send_json({"error": "Connection request not found."}, 404)
                if int(connection["recipient_id"]) != int(auth_id):
                    return self.send_json({"error": "Only the connection recipient can respond to this request."}, 403)
                if connection["status"] != "pending":
                    return self.send_json({"error": "Connection request is no longer pending."}, 409)

                cursor.execute("UPDATE connections SET status = ? WHERE id = ?", (status, conn_id))
                conn.commit()
                return self.send_json({"success": True, "status": status})

            elif path == '/api/messages':
                sender_id = current_user_id(self)
                recipient_id = body.get('recipient_id')
                if not sender_id:
                    return self.send_json({"error": "Authentication required."}, 401)
                try:
                    recipient_id = int(recipient_id)
                except (TypeError, ValueError):
                    return self.send_json({"error": "A valid recipient_id is required."}, 400)
                if recipient_id == int(sender_id):
                    return self.send_json({"error": "You cannot message your own account."}, 400)
                recipient = cursor.execute("SELECT id, status FROM users WHERE id = ?", (recipient_id,)).fetchone()
                if not recipient or recipient['status'] != 'active':
                    return self.send_json({"error": "Recipient account not found or inactive."}, 404)
                message_text = str(body.get('message_text') or '').strip()
                msg_type = body.get('message_type', 'text')
                metadata = body.get('metadata', None)
                if not message_text or len(message_text) > 5000:
                    return self.send_json({"error": "Message must contain 1–5000 characters."}, 400)
                if msg_type not in ('text', 'trial_invite', 'tournament_invite'):
                    return self.send_json({"error": "Invalid message type."}, 400)

                now = datetime.now().isoformat()
                cursor.execute("""
                INSERT INTO messages (sender_id, recipient_id, message_text, message_type, metadata_json, timestamp, is_read)
                VALUES (?, ?, ?, ?, ?, ?, 0)
                """, (sender_id, recipient_id, message_text, msg_type, json.dumps(metadata) if metadata else None, now))

                # Notify
                cursor.execute("SELECT full_name FROM users WHERE id = ?", (sender_id,))
                s_name = cursor.fetchone()[0]
                cursor.execute("""
                INSERT INTO notifications (user_id, category, title, message, link, timestamp)
                VALUES (?, 'Messages', '💬 New Message', ?, '#messages', ?)
                """, (recipient_id, f"New message from {s_name}: {message_text[:40]}...", now))

                conn.commit()
                return self.send_json({"success": True, "timestamp": now})

            # 9. Bookmark / Save Talent
            elif path == '/api/saved-talent':
                user_id = current_user_id(self)
                player_id = body.get('player_id')
                if not user_id:
                    return self.send_json({"error": "Authentication required."}, 401)
                notes = body.get('notes', 'Saved from talent search')
                action = body.get('action', 'save') # 'save' or 'unsave'

                if action == 'unsave':
                    cursor.execute("DELETE FROM saved_talent WHERE user_id = ? AND player_id = ?", (user_id, player_id))
                else:
                    now = datetime.now().isoformat()
                    cursor.execute("""
                    INSERT OR REPLACE INTO saved_talent (user_id, player_id, notes, saved_at)
                    VALUES (?, ?, ?, ?)
                    """, (user_id, player_id, notes, now))

                conn.commit()
                return self.send_json({"success": True, "action": action})

            # 10. Report System
            elif path == '/api/reports':
                reporter_id = current_user_id(self)
                reported_user_id = body.get('reported_user_id')
                if not reporter_id:
                    return self.send_json({"error": "Authentication required."}, 401)
                try:
                    reported_user_id = int(reported_user_id)
                except (TypeError, ValueError):
                    return self.send_json({"error": "A valid reported_user_id is required."}, 400)
                if reported_user_id == int(reporter_id):
                    return self.send_json({"error": "You cannot report your own account."}, 400)
                target = cursor.execute("SELECT id FROM users WHERE id = ?", (reported_user_id,)).fetchone()
                if not target:
                    return self.send_json({"error": "Reported account not found."}, 404)
                item_type = body.get('reported_item_type', 'profile')
                item_id = body.get('reported_item_id')
                report_type = body.get('report_type', 'fake_profile')
                description = str(body.get('description') or '').strip()
                evidence = str(body.get('evidence_text') or '').strip()
                if not description or len(description) > 5000:
                    return self.send_json({"error": "Report description must contain 1–5000 characters."}, 400)
                if item_type not in ('profile', 'certificate', 'match_stats', 'behavior'):
                    return self.send_json({"error": "Invalid reported item type."}, 400)
                if report_type not in ('fake_profile', 'fake_certificate', 'incorrect_stats', 'impersonation', 'spam', 'other'):
                    return self.send_json({"error": "Invalid report type."}, 400)

                now = datetime.now().isoformat()
                cursor.execute("""
                INSERT INTO reports (reporter_id, reported_user_id, reported_item_type, reported_item_id, report_type, description, evidence_text, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Under Review', ?)
                """, (reporter_id, reported_user_id, item_type, item_id, report_type, description, evidence, now))
                report_id = cursor.lastrowid

                # Notify user of submission
                cursor.execute("""
                INSERT INTO notifications (user_id, category, title, message, link, timestamp)
                VALUES (?, 'Reports', '🚨 Report Submitted (#{})', 'Your report is Under Review by the platform integrity team.', '#reports', ?)
                """.format(report_id), (reporter_id, now))

                conn.commit()
                return self.send_json({"success": True, "report_id": report_id, "status": "Under Review"})

            elif path.startswith('/api/admin/reports/') and path.endswith('/action'):
                report_id = int(path.split('/')[-2])
                action = body.get('action') # 'dismiss', 'more_info', 'escalate', 'resolve', 'suspend_user', 'reject_cert'
                admin_notes = body.get('admin_notes', '')

                status_map = {
                    'dismiss': 'Dismissed',
                    'more_info': 'More Information Needed',
                    'escalate': 'Escalated',
                    'resolve': 'Resolved',
                    'suspend_user': 'Resolved',
                    'reject_cert': 'Resolved'
                }
                new_status = status_map.get(action, 'Resolved')
                now = datetime.now().isoformat()

                cursor.execute("""
                UPDATE reports 
                SET status = ?, admin_notes = ?, resolved_at = ?
                WHERE id = ?
                """, (new_status, admin_notes, now, report_id))

                if action == 'suspend_user':
                    cursor.execute("SELECT reported_user_id FROM reports WHERE id = ?", (report_id,))
                    u_id = cursor.fetchone()[0]
                    cursor.execute("UPDATE users SET status = 'suspended' WHERE id = ?", (u_id,))

                conn.commit()
                return self.send_json({"success": True, "status": new_status})

            # 11. Admin User Status (Suspend / Activate / Verify)
            elif path.startswith('/api/admin/users/') and path.endswith('/status'):
                user_id = int(path.split('/')[-2])
                status = body.get('status', 'active')
                is_verified = int(body.get('is_verified', 1))

                cursor.execute("UPDATE users SET status = ?, is_verified = ? WHERE id = ?", (status, is_verified, user_id))
                conn.commit()
                return self.send_json({"success": True, "user_id": user_id, "status": status, "is_verified": is_verified})

            else:
                return self.send_json({"error": "Endpoint not found"}, 404)

        except Exception:
            conn.rollback()
            logger.exception("Unhandled POST API error: %s", path)
            return self.send_json({"error": "Internal server error."}, 500)
        finally:
            conn.close()

def run_server():
    init_db(force=False)

    # Remove obsolete database Admin records. The real admin identity is environment-only.
    conn = get_db()
    try:
        conn.cursor().execute("DELETE FROM users WHERE role = 'Admin' OR lower(username) IN ('admin', 'admin@sportsconnect.com')")
        conn.commit()
    finally:
        conn.close()

    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer((HOST, PORT), SportsConnectHandler) as httpd:
        logger.info("SportsConnect Platform Server running on %s:%s", HOST, PORT)
        logger.info("Database backend: %s", "Supabase PostgreSQL" if USING_POSTGRES else "local SQLite")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server shutting down.")

if __name__ == "__main__":
    run_server()
