"""
SportsConnect SQLite Database Engine and Seed Data
Initializes all relational tables and populates with realistic demo profiles,
matches, tests, certificates, trials, and verifications.
"""

import sqlite3
import hashlib
import hmac
import base64
import json
import os
import secrets
import logging
from datetime import datetime

try:
    import psycopg2
    from psycopg2.extras import DictCursor
except ImportError:
    psycopg2 = None
    DictCursor = None

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "sportsconnect.db")
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USING_POSTGRES = bool(DATABASE_URL)

PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 310_000

def hash_pw(password: str) -> str:
    """Hash passwords using PBKDF2-HMAC-SHA256 with a per-password salt."""
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return "{}${}${}${}".format(PASSWORD_ALGORITHM, PASSWORD_ITERATIONS, base64.urlsafe_b64encode(salt).decode("ascii"), base64.urlsafe_b64encode(digest).decode("ascii"))

def verify_pw(password: str, stored_hash: str) -> bool:
    """Verify PBKDF2 hashes and legacy SHA-256 hashes during migration."""
    if not password or not stored_hash: return False
    if stored_hash.startswith(PASSWORD_ALGORITHM + "$"):
        try:
            algorithm, iterations, salt_b64, digest_b64 = stored_hash.split("$", 3)
            salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
            expected = base64.urlsafe_b64decode(digest_b64.encode("ascii"))
            actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
            return hmac.compare_digest(actual, expected)
        except (ValueError, TypeError): return False
    legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy, stored_hash)

class CompatCursor:
    _LASTROWID_TABLES = {"users", "certificates", "matches", "trials", "reports"}
    def __init__(self, raw_cursor, postgres=False):
        self._cursor, self._postgres, self._lastrowid = raw_cursor, postgres, None
    @staticmethod
    def _replace_placeholders(query): return query.replace("?", "%s")
    def execute(self, query, params=None):
        if not self._postgres: return self._cursor.execute(query, params or ())
        q = query
        if "INSERT OR REPLACE INTO saved_talent" in q.upper():
            q = q.replace("INSERT OR REPLACE INTO saved_talent", "INSERT INTO saved_talent")
            q = q.replace("VALUES (?, ?, ?, ?)", "VALUES (?, ?, ?, ?) ON CONFLICT (user_id, player_id) DO UPDATE SET notes = EXCLUDED.notes, saved_at = EXCLUDED.saved_at")
        q = self._replace_placeholders(q)
        result = self._cursor.execute(q, params or ())
        import re
        m = re.match(r"\s*INSERT\s+INTO\s+([A-Za-z_][A-Za-z0-9_]*)", q, re.I)
        table = m.group(1).lower() if m else None
        if table in self._LASTROWID_TABLES:
            self._cursor.execute("SELECT currval(pg_get_serial_sequence(%s, 'id')) AS id", (table,))
            row = self._cursor.fetchone()
            self._lastrowid = row["id"] if row else None
        return result
    def executemany(self, query, seq_of_params):
        if self._postgres: query = self._replace_placeholders(query)
        return self._cursor.executemany(query, seq_of_params)
    @property
    def lastrowid(self): return self._lastrowid if self._postgres else self._cursor.lastrowid
    def __getattr__(self, name): return getattr(self._cursor, name)

class CompatConnection:
    def __init__(self, raw_connection): self._conn, self._postgres = raw_connection, USING_POSTGRES
    def cursor(self):
        return CompatCursor(self._conn.cursor(cursor_factory=DictCursor), True) if self._postgres else CompatCursor(self._conn.cursor(), False)
    def commit(self): return self._conn.commit()
    def rollback(self): return self._conn.rollback()
    def close(self): return self._conn.close()
    def __enter__(self): self._conn.__enter__(); return self
    def __exit__(self, exc_type, exc_value, traceback): return self._conn.__exit__(exc_type, exc_value, traceback)

def get_db():
    if USING_POSTGRES:
        if psycopg2 is None: raise RuntimeError("psycopg2-binary is required when DATABASE_URL is configured.")
        return CompatConnection(psycopg2.connect(DATABASE_URL, sslmode=os.getenv("DB_SSLMODE", "require"), connect_timeout=10))
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return CompatConnection(conn)

def init_db(force: bool = False):
    if force and not USING_POSTGRES and os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass

    conn = get_db()
    cursor = conn.cursor()

    schema_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL, -- 'Player', 'Coach', 'Club', 'Organizer', 'Admin'
        full_name TEXT NOT NULL,
        avatar TEXT,
        location TEXT,
        state TEXT,
        district TEXT,
        city TEXT,
        village TEXT,
        availability TEXT,
        bio TEXT,
        is_verified INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active', -- 'active', 'suspended'
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS player_profiles (
        user_id INTEGER PRIMARY KEY,
        sport TEXT NOT NULL,
        position TEXT NOT NULL,
        experience_years REAL DEFAULT 1.0,
        age_group TEXT,
        dob TEXT,
        preferred_role TEXT,
        availability TEXT DEFAULT 'Available for Trials', -- 'Available for Trials', 'In Club', 'Not Available'
        rating REAL DEFAULT 8.0,
        classification TEXT DEFAULT 'Rising Talent', -- 'Rising Talent', 'Emerging Player', 'Established Player', 'Elite Player'
        skill_score REAL DEFAULT 80.0,
        performance_score REAL DEFAULT 80.0,
        progress_pct REAL DEFAULT 15.0,
        major_matches INTEGER DEFAULT 0,
        verified_local_matches INTEGER DEFAULT 0,
        consistency_score REAL DEFAULT 85.0,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS coach_profiles (
        user_id INTEGER PRIMARY KEY,
        sport TEXT NOT NULL,
        experience_years REAL DEFAULT 5.0,
        specialization TEXT,
        certifications TEXT,
        current_org TEXT,
        availability TEXT,
        verification_status TEXT DEFAULT 'verified', -- 'verified', 'pending', 'rejected'
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS club_profiles (
        user_id INTEGER PRIMARY KEY,
        sport TEXT NOT NULL,
        club_name TEXT NOT NULL,
        established_year INTEGER,
        home_ground TEXT,
        division TEXT,
        verification_status TEXT DEFAULT 'verified',
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS organizer_profiles (
        user_id INTEGER PRIMARY KEY,
        organization_name TEXT NOT NULL,
        sport TEXT NOT NULL,
        registration_no TEXT,
        verification_status TEXT DEFAULT 'verified',
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS referee_profiles (
        user_id INTEGER PRIMARY KEY,
        sport TEXT NOT NULL,
        level TEXT,
        official_role TEXT,
        experience_years REAL DEFAULT 0,
        certification TEXT,
        availability TEXT,
        verification_status TEXT DEFAULT 'pending',
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS sports_tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        sport TEXT NOT NULL,
        test_name TEXT NOT NULL,
        score REAL NOT NULL,
        max_score REAL DEFAULT 100,
        date_taken TEXT,
        evaluator_name TEXT,
        verified_by TEXT,
        FOREIGN KEY (player_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS certificates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        issuing_org TEXT NOT NULL,
        year INTEGER NOT NULL,
        achievement_text TEXT NOT NULL,
        file_name TEXT,
        file_url TEXT,
        status TEXT DEFAULT 'pending', -- 'pending', 'verified', 'rejected'
        verified_by TEXT,
        verified_at TEXT,
        rejection_reason TEXT,
        created_at TEXT,
        FOREIGN KEY (player_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS tournaments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organizer_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        sport TEXT NOT NULL,
        location TEXT NOT NULL,
        start_date TEXT,
        end_date TEXT,
        age_group TEXT,
        teams_required INTEGER DEFAULT 8,
        deadline TEXT,
        status TEXT DEFAULT 'Active', -- 'Upcoming', 'Active', 'Completed'
        FOREIGN KEY (organizer_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tournament_id INTEGER,
        sport TEXT NOT NULL,
        title TEXT NOT NULL,
        team_a TEXT NOT NULL,
        team_b TEXT NOT NULL,
        match_date TEXT NOT NULL,
        location TEXT NOT NULL,
        result_summary TEXT,
        score_a TEXT,
        score_b TEXT,
        status TEXT DEFAULT 'verified', -- 'verified', 'pending'
        verified_by TEXT,
        FOREIGN KEY (tournament_id) REFERENCES tournaments (id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS match_player_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id INTEGER NOT NULL,
        player_id INTEGER NOT NULL,
        team_name TEXT NOT NULL,
        role_played TEXT NOT NULL,
        stats_json TEXT NOT NULL, -- e.g. {"runs": 72, "balls": 48, "wickets": 0, "overs": 0}
        performance_rating REAL DEFAULT 8.5,
        verified_status TEXT DEFAULT 'verified',
        FOREIGN KEY (match_id) REFERENCES matches (id) ON DELETE CASCADE,
        FOREIGN KEY (player_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS connections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        requester_id INTEGER NOT NULL,
        recipient_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending', -- 'pending', 'accepted', 'declined'
        created_at TEXT,
        FOREIGN KEY (requester_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (recipient_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        recipient_id INTEGER NOT NULL,
        message_text TEXT NOT NULL,
        message_type TEXT DEFAULT 'text', -- 'text', 'trial_invite', 'tournament_invite'
        metadata_json TEXT,
        timestamp TEXT,
        is_read INTEGER DEFAULT 0,
        FOREIGN KEY (sender_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (recipient_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS trials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creator_id INTEGER NOT NULL,
        sport TEXT NOT NULL,
        position TEXT NOT NULL,
        title TEXT NOT NULL,
        trial_date TEXT NOT NULL,
        trial_time TEXT NOT NULL,
        location TEXT NOT NULL,
        requirements TEXT,
        slots INTEGER DEFAULT 10,
        status TEXT DEFAULT 'Open', -- 'Open', 'Completed', 'Cancelled'
        FOREIGN KEY (creator_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS trial_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trial_id INTEGER NOT NULL,
        player_id INTEGER NOT NULL,
        status TEXT DEFAULT 'invited', -- 'invited', 'accepted', 'declined', 'selected'
        evaluation_notes TEXT,
        trial_score REAL,
        created_at TEXT,
        FOREIGN KEY (trial_id) REFERENCES trials (id) ON DELETE CASCADE,
        FOREIGN KEY (player_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS saved_talent (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        player_id INTEGER NOT NULL,
        notes TEXT,
        saved_at TEXT,
        UNIQUE(user_id, player_id),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (player_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL, -- 'Connections', 'Opportunities', 'Matches', 'Verification', 'Performance', 'Reports', 'Messages', 'System'
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        link TEXT,
        is_read INTEGER DEFAULT 0,
        timestamp TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reporter_id INTEGER NOT NULL,
        reported_user_id INTEGER NOT NULL,
        reported_item_type TEXT NOT NULL, -- 'profile', 'certificate', 'match_stats', 'behavior'
        reported_item_id INTEGER,
        report_type TEXT NOT NULL, -- 'fake_profile', 'fake_certificate', 'incorrect_stats', 'impersonation', 'spam', 'other'
        description TEXT NOT NULL,
        evidence_text TEXT,
        status TEXT DEFAULT 'Under Review', -- 'Under Review', 'More Information Needed', 'Resolved', 'Dismissed', 'Escalated'
        admin_notes TEXT,
        created_at TEXT,
        resolved_at TEXT,
        FOREIGN KEY (reporter_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (reported_user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS privacy_settings (
        user_id INTEGER PRIMARY KEY,
        profile_visibility TEXT DEFAULT 'public',
        contact_visibility TEXT DEFAULT 'connections_only',
        stats_visibility TEXT DEFAULT 'public',
        certs_visibility TEXT DEFAULT 'public',
        connections_visibility TEXT DEFAULT 'public',
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_hash TEXT UNIQUE NOT NULL,
        user_id INTEGER,
        role TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """
    if USING_POSTGRES:
        # Translate only SQLite-specific auto-increment declarations.
        postgres_schema = schema_sql.replace(
            "INTEGER PRIMARY KEY AUTOINCREMENT", "BIGSERIAL PRIMARY KEY"
        )
        cursor.execute(postgres_schema)
    else:
        cursor.executescript(schema_sql)

    conn.commit()
    seed_demo_data(conn)
    if USING_POSTGRES:
        _reset_postgres_sequences(conn)
    conn.close()
    print("Database initialized successfully.")

def _reset_postgres_sequences(conn):
    tables = ["users","sports_tests","certificates","tournaments","matches","match_player_stats","connections","messages","trials","trial_applications","saved_talent","notifications","reports","sessions"]
    cursor = conn.cursor()
    for table in tables:
        cursor.execute("SELECT setval(pg_get_serial_sequence(%s, 'id'), COALESCE((SELECT MAX(id) FROM " + table + "), 1), true)", (table,))
    conn.commit()

def seed_demo_data(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        return # Already seeded

    now = datetime.now().isoformat()

    # 1. Users
    users_data = [
        # id=1: Rahul Kumar (Player, Rising Talent)
        (1, 'rahulkumar', 'rahul@sportsconnect.com', '+91 98765 43210', hash_pw('password123'), 'Player', 'Rahul Kumar', '🏏', 'Hyderabad', 'Telangana', 'Hyderabad', 'Passionate top-order batsman with relentless practice ethics. Focus on high conversion rate, explosive gap finding, and disciplined technique.', 1, 'active', now),
        # id=2: Arjun Reddy (Player, Emerging Player)
        (2, 'arjunreddy', 'arjun@sportsconnect.com', '+91 98765 43211', hash_pw('password123'), 'Player', 'Arjun Reddy', '🏏', 'Hyderabad', 'Telangana', 'Secunderabad', 'Dynamic seam-bowling all-rounder with strong middle-order finishing capabilities and athletic boundary fielding.', 1, 'active', now),
        # id=3: Kiran Kumar (Player, Rising Talent)
        (3, 'kirankumar', 'kiran@sportsconnect.com', '+91 98765 43212', hash_pw('password123'), 'Player', 'Kiran Kumar', '🏏', 'Secunderabad', 'Telangana', 'Secunderabad', 'Right-arm medium fast bowler specializing in late outswing and yorkers at death overs. Rising through district trials.', 1, 'active', now),
        # id=4: Sunil Chhetri Jr (Player, Football Rising Talent)
        (4, 'suniljunior', 'sunil@sportsconnect.com', '+91 98765 43213', hash_pw('password123'), 'Player', 'Sunil Varma', '⚽', 'Bengaluru', 'Karnataka', 'Bengaluru Urban', 'Agile center-forward with clinical finishing in tight boxes and sharp link-up play.', 1, 'active', now),
        # id=5: Ananya Sharma (Player, Badminton Rising Talent)
        (5, 'ananyasharma', 'ananya@sportsconnect.com', '+91 98765 43214', hash_pw('password123'), 'Player', 'Ananya Sharma', '🏸', 'Hyderabad', 'Telangana', 'Cyberabad', 'Aggressive singles shuttler with 320 km/h overhead smash and rapid net recovery footwork.', 1, 'active', now),
        # id=6: Coach Vikram Rathore (Coach)
        (6, 'coachvikram', 'coach.vikram@sportsconnect.com', '+91 98765 11111', hash_pw('password123'), 'Coach', 'Vikram Rathore', '🧑‍🏫', 'Hyderabad', 'Telangana', 'Hyderabad', 'BCCI Level 2 Certified Cricket Coach. Head Scout for Deccan Regional Academy. Scouting future national athletes based on scientific skill data.', 1, 'active', now),
        # id=7: Hyderabad Warriors CC (Club)
        (7, 'warriorscc', 'contact@warriorscc.com', '+91 98765 22222', hash_pw('password123'), 'Club', 'Hyderabad Warriors CC', '🛡️', 'Hyderabad', 'Telangana', 'Hyderabad', 'Premier Division 1 Club competing across state leagues. Active scouting program for under-23 batting and all-round prospects.', 1, 'active', now),
        # id=8: Deccan Gladiators FC (Club)
        (8, 'deccangladiator', 'info@deccangladiator.com', '+91 98765 33333', hash_pw('password123'), 'Club', 'Deccan Gladiators FC', '⚽', 'Hyderabad', 'Telangana', 'Gachibowli', 'Top-tier football club cultivating young youth talent through high-intensity tactical conditioning.', 1, 'active', now),
        # id=9: Telangana Youth Sports Council (Organizer)
        (9, 'tysports', 'tournaments@tysports.org', '+91 98765 44444', hash_pw('password123'), 'Organizer', 'Telangana Youth Sports Council', '🏆', 'Hyderabad', 'Telangana', 'Hyderabad', 'Apex organizing body for verified district tournaments, school championships, and talent evaluation leagues.', 1, 'active', now),
    ]

    cursor.executemany("""
    INSERT INTO users (id, username, email, phone, password_hash, role, full_name, avatar, location, state, district, bio, is_verified, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, users_data)

    # 2. Player Profiles
    # Formula reminder: (Skill*0.3) + (MatchPerf*0.3) + (Progress*0.2) + (Exp*0.1) + (Achievements*0.1)
    player_profiles_data = [
        # Rahul Kumar: 0 major matches, 6 verified local matches, skill 88, perf 86, progress +21% -> RISING TALENT
        (1, 'Cricket', 'Batsman', 2.0, 'Under-23', '2004-05-14', 'Top-Order / Opening Batsman', 'Available for Trials', 8.4, 'Rising Talent', 88.0, 86.0, 21.0, 0, 6, 88.0),
        # Arjun Reddy: 22 matches, skill 84, perf 81, progress +15% -> EMERGING PLAYER
        (2, 'Cricket', 'All-rounder', 4.5, 'Open Senior', '2001-08-22', 'Pace Bowling All-rounder', 'In Club', 8.1, 'Emerging Player', 84.0, 81.0, 15.0, 4, 18, 82.0),
        # Kiran Kumar: 1 match major, 5 local, skill 87, perf 85, progress +19% -> RISING TALENT
        (3, 'Cricket', 'Bowler', 1.5, 'Under-21', '2005-02-10', 'Right-arm Fast Bowler', 'Available for Trials', 8.3, 'Rising Talent', 87.0, 85.0, 19.0, 0, 5, 86.0),
        # Sunil Chhetri Jr: Football Forward -> RISING TALENT
        (4, 'Football', 'Forward', 2.0, 'Under-21', '2004-11-18', 'Striker / Center Forward', 'Available for Trials', 8.6, 'Rising Talent', 89.0, 87.0, 24.0, 0, 8, 89.0),
        # Ananya Sharma: Badminton Singles -> RISING TALENT
        (5, 'Badminton', 'Singles', 3.0, 'Under-19', '2006-03-29', 'Singles Shuttler', 'Available for Trials', 8.5, 'Rising Talent', 88.0, 86.0, 22.0, 1, 9, 87.0)
    ]

    cursor.executemany("""
    INSERT INTO player_profiles (user_id, sport, position, experience_years, age_group, dob, preferred_role, availability, rating, classification, skill_score, performance_score, progress_pct, major_matches, verified_local_matches, consistency_score)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, player_profiles_data)

    # 3. Coach Profile
    cursor.execute("""
    INSERT INTO coach_profiles (user_id, sport, experience_years, specialization, certifications, current_org, verification_status)
    VALUES (6, 'Cricket', 12.0, 'Batting Technique & Mental Conditioning', 'BCCI Level 2, ICC Certified High Performance Coach', 'Deccan Regional Academy', 'verified')
    """)

    # 4. Club Profiles
    cursor.execute("""
    INSERT INTO club_profiles (user_id, sport, club_name, established_year, home_ground, division, verification_status)
    VALUES 
    (7, 'Cricket', 'Hyderabad Warriors CC', 2012, 'Rajiv Gandhi International Cricket Annex', 'Division 1 State League', 'verified'),
    (8, 'Football', 'Deccan Gladiators FC', 2016, 'Gachibowli Stadium', 'Telangana State Premier Division', 'verified')
    """)

    # 5. Organizer Profile
    cursor.execute("""
    INSERT INTO organizer_profiles (user_id, organization_name, sport, registration_no, verification_status)
    VALUES (9, 'Telangana Youth Sports Council', 'Multi-Sport', 'TS-SPO-2018-9941', 'verified')
    """)

    # 6. Sports Tests (Structured Sport Assessments)
    # Cricket: Batting Accuracy, Shot Selection, Reaction, Fielding, Running, Bowling Accuracy, Fitness
    tests_data = [
        # Rahul Kumar (Overall Skill: 88/100)
        (1, 'Cricket', 'Batting Accuracy', 91.0, 100, '2026-08-15', 'Coach Vikram Rathore', 'Authorized Evaluator'),
        (1, 'Cricket', 'Shot Selection', 85.0, 100, '2026-08-15', 'Coach Vikram Rathore', 'Authorized Evaluator'),
        (1, 'Cricket', 'Reaction Time', 94.0, 100, '2026-08-15', 'Coach Vikram Rathore', 'Authorized Evaluator'),
        (1, 'Cricket', 'Fielding Agility', 82.0, 100, '2026-08-15', 'Coach Vikram Rathore', 'Authorized Evaluator'),
        (1, 'Cricket', 'Running Between Wickets', 88.0, 100, '2026-08-15', 'Coach Vikram Rathore', 'Authorized Evaluator'),
        (1, 'Cricket', 'Fitness & Stamina', 86.0, 100, '2026-08-15', 'Coach Vikram Rathore', 'Authorized Evaluator'),
        (1, 'Cricket', 'Bowling Accuracy', 62.0, 100, '2026-08-15', 'Coach Vikram Rathore', 'Authorized Evaluator'),

        # Arjun Reddy (Overall Skill: 84/100)
        (2, 'Cricket', 'Batting Accuracy', 82.0, 100, '2026-08-10', 'Coach Vikram Rathore', 'Authorized Evaluator'),
        (2, 'Cricket', 'Shot Selection', 80.0, 100, '2026-08-10', 'Coach Vikram Rathore', 'Authorized Evaluator'),
        (2, 'Cricket', 'Reaction Time', 86.0, 100, '2026-08-10', 'Coach Vikram Rathore', 'Authorized Evaluator'),
        (2, 'Cricket', 'Fielding Agility', 89.0, 100, '2026-08-10', 'Coach Vikram Rathore', 'Authorized Evaluator'),
        (2, 'Cricket', 'Running Between Wickets', 83.0, 100, '2026-08-10', 'Coach Vikram Rathore', 'Authorized Evaluator'),
        (2, 'Cricket', 'Fitness & Stamina', 91.0, 100, '2026-08-10', 'Coach Vikram Rathore', 'Authorized Evaluator'),
        (2, 'Cricket', 'Bowling Accuracy', 86.0, 100, '2026-08-10', 'Coach Vikram Rathore', 'Authorized Evaluator'),

        # Kiran Kumar (Overall Skill: 87/100)
        (3, 'Cricket', 'Batting Accuracy', 64.0, 100, '2026-08-12', 'Coach Vikram Rathore', 'Authorized Evaluator'),
        (3, 'Cricket', 'Shot Selection', 60.0, 100, '2026-08-12', 'Coach Vikram Rathore', 'Authorized Evaluator'),
        (3, 'Cricket', 'Reaction Time', 89.0, 100, '2026-08-12', 'Coach Vikram Rathore', 'Authorized Evaluator'),
        (3, 'Cricket', 'Fielding Agility', 84.0, 100, '2026-08-12', 'Coach Vikram Rathore', 'Authorized Evaluator'),
        (3, 'Cricket', 'Running Between Wickets', 85.0, 100, '2026-08-12', 'Coach Vikram Rathore', 'Authorized Evaluator'),
        (3, 'Cricket', 'Fitness & Stamina', 92.0, 100, '2026-08-12', 'Coach Vikram Rathore', 'Authorized Evaluator'),
        (3, 'Cricket', 'Bowling Accuracy', 94.0, 100, '2026-08-12', 'Coach Vikram Rathore', 'Authorized Evaluator')
    ]

    cursor.executemany("""
    INSERT INTO sports_tests (player_id, sport, test_name, score, max_score, date_taken, evaluator_name, verified_by)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, tests_data)

    # 7. Certificates (Verified, Pending, Rejected)
    certs_data = [
        # Verified Certificate for Rahul Kumar
        (1, 'District Under-19 Championship Trophy - Best Batsman', 'Telangana Cricket Association & TYSC', 2025, 'Awarded Best Batsman across 6 tournament matches with 340 tournament runs and highest strike rate.', 'cert_dist_u19_rahul.pdf', 'certs/dist_u19.pdf', 'verified', 'Chief Sports Verifier (Admin)', '2026-08-01T10:00:00', None, now),
        # Pending Certificate for Rahul Kumar
        (1, 'State Youth Championship Participation Certificate', 'South Zone Sports Federation', 2026, 'Semi-Finalist representing Hyderabad Central District.', 'cert_state_youth_rahul.pdf', 'certs/state_youth.pdf', 'pending', None, None, None, now),
        # Verified Certificate for Arjun Reddy
        (2, 'Inter-College Gold Medal - Best All-Rounder', 'Osmania University Sports Board', 2025, 'Scored 185 runs and took 9 wickets in 4 knockout matches.', 'cert_intercollege_arjun.pdf', 'certs/arjun_gold.pdf', 'verified', 'Chief Sports Verifier (Admin)', '2026-07-20T14:30:00', None, now),
        # Rejected Certificate Example for demo verification trail
        (1, 'Unverified Private Club Tournament Winner', 'Local Weekend Club', 2024, 'Weekend club trophy claims without authorized stamp.', 'fake_club_doc.pdf', 'certs/unverified.pdf', 'rejected', 'Chief Sports Verifier (Admin)', '2026-08-05T12:00:00', 'Missing official seal and registration numbers from sanctioned sports board.', now)
    ]

    cursor.executemany("""
    INSERT INTO certificates (player_id, title, issuing_org, year, achievement_text, file_name, file_url, status, verified_by, verified_at, rejection_reason, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, certs_data)

    # 8. Tournaments
    cursor.execute("""
    INSERT INTO tournaments (id, organizer_id, title, sport, location, start_date, end_date, age_group, teams_required, deadline, status)
    VALUES 
    (1, 9, 'Hyderabad District T20 Championship', 'Cricket', 'Gymkhana Grounds, Secunderabad', '2026-08-20', '2026-08-28', 'Under-23 & Open', 8, '2026-08-15', 'Completed'),
    (2, 9, 'Telangana State Youth Super League', 'Cricket', 'Rajiv Gandhi International Stadium Complex', '2026-09-25', '2026-10-05', 'Under-21', 12, '2026-09-18', 'Active')
    """)

    # 9. Matches (Official Authorized Records)
    cursor.execute("""
    INSERT INTO matches (id, tournament_id, sport, title, team_a, team_b, match_date, location, result_summary, score_a, score_b, status, verified_by)
    VALUES 
    (1, 1, 'Cricket', 'Hyderabad District T20 - Final', 'Warriors XI', 'Rising Stars XI', '2026-08-28', 'Gymkhana Ground, Hyderabad', 'Warriors XI won by 18 runs', '182/4 (20.0 ov)', '164/8 (20.0 ov)', 'verified', 'Telangana Youth Sports Council (Organizer)'),
    (2, 1, 'Cricket', 'Hyderabad District T20 - Semi-Final', 'Warriors XI', 'Deccan Challengers', '2026-08-26', 'Gymkhana Ground, Hyderabad', 'Warriors XI won by 5 wickets', '158/5 (18.4 ov)', '155/7 (20.0 ov)', 'verified', 'Telangana Youth Sports Council (Organizer)'),
    (3, 1, 'Cricket', 'Hyderabad District T20 - Group Stage', 'Rising Stars XI', 'Secunderabad Strikers', '2026-08-22', 'Parade Ground, Secunderabad', 'Rising Stars XI won by 34 runs', '174/6 (20.0 ov)', '140/9 (20.0 ov)', 'verified', 'Telangana Youth Sports Council (Organizer)')
    """)

    # 10. Match Player Statistics with "Played With" & "Played Against"
    match_player_stats_data = [
        # Match 1: Warriors XI vs Rising Stars XI
        # Rahul Kumar (Warriors XI - Batsman)
        (1, 1, 'Warriors XI', 'Opening Batsman', json.dumps({
            "runs": 72, "balls": 48, "fours": 8, "sixes": 3, "strike_rate": 150.0, "out_status": "c & b Sharma"
        }), 9.2, 'verified'),
        # Arjun Reddy (Warriors XI - All-rounder)
        (1, 2, 'Warriors XI', 'Middle-Order All-rounder', json.dumps({
            "runs": 48, "balls": 28, "fours": 4, "sixes": 2, "strike_rate": 171.4, "overs": 4.0, "wickets": 2, "runs_conceded": 29
        }), 8.9, 'verified'),
        # Kiran Kumar (Rising Stars XI - Bowler - Playing against Rahul & Arjun)
        (1, 3, 'Rising Stars XI', 'Opening Bowler', json.dumps({
            "overs": 4.0, "maidens": 0, "wickets": 3, "runs_conceded": 31, "economy": 7.75, "runs": 6, "balls": 4
        }), 8.6, 'verified'),

        # Match 2: Warriors XI vs Deccan Challengers
        # Rahul Kumar: 54 runs (39 balls)
        (2, 1, 'Warriors XI', 'Opening Batsman', json.dumps({
            "runs": 54, "balls": 39, "fours": 6, "sixes": 1, "strike_rate": 138.5, "out_status": "not out"
        }), 8.8, 'verified'),
        # Arjun Reddy: 31 runs (20 balls), 1 wicket
        (2, 2, 'Warriors XI', 'Middle-Order Batsman', json.dumps({
            "runs": 31, "balls": 20, "fours": 3, "sixes": 1, "strike_rate": 155.0, "overs": 3.0, "wickets": 1, "runs_conceded": 22
        }), 8.2, 'verified')
    ]

    cursor.executemany("""
    INSERT INTO match_player_stats (match_id, player_id, team_name, role_played, stats_json, performance_rating, verified_status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, match_player_stats_data)

    # 11. Connections
    cursor.execute("""
    INSERT INTO connections (requester_id, recipient_id, status, created_at)
    VALUES 
    (6, 1, 'accepted', '2026-08-29T11:00:00'), -- Coach Vikram connected with Rahul Kumar
    (7, 1, 'accepted', '2026-08-30T15:20:00'), -- Hyderabad Warriors CC connected with Rahul
    (1, 2, 'accepted', '2026-08-25T09:00:00'), -- Rahul & Arjun teammate connection
    (6, 2, 'accepted', '2026-08-28T16:00:00')  -- Coach Vikram connected with Arjun
    """)

    # 12. Messages
    cursor.execute("""
    INSERT INTO messages (sender_id, recipient_id, message_text, message_type, metadata_json, timestamp, is_read)
    VALUES 
    (6, 1, 'Hello Rahul! I analyzed your verified 72 runs against Rising Stars and your 94/100 reaction test. Exceptional timing against 135km/h deliveries.', 'text', NULL, '2026-08-30T10:15:00', 1),
    (1, 6, 'Thank you Coach Vikram! Really appreciate your guidance. I have been working on my back-foot defense against incoming seam deliveries.', 'text', NULL, '2026-08-30T10:35:00', 1),
    (6, 1, 'Excellent. We are hosting an invitational trial session for the State Super League. I want you to attend this Friday.', 'trial_invite', '{"trial_id": 1, "position": "Top-Order Batsman", "date": "2026-09-20"}', '2026-09-01T14:20:00', 0)
    """)

    # 13. Trials
    cursor.execute("""
    INSERT INTO trials (id, creator_id, sport, position, title, trial_date, trial_time, location, requirements, slots, status)
    VALUES 
    (1, 7, 'Cricket', 'Top-Order Batsman', 'Under-23 State League Selection Trials', '2026-09-20', '09:00 AM', 'Rajiv Gandhi Stadium Annex Ground, Hyderabad', 'Minimum Verified Skill Score 80+, White cricket kit, spikes required.', 12, 'Open'),
    (2, 8, 'Football', 'Center Forward', 'Youth Division 1 Scouting Combine', '2026-09-22', '07:30 AM', 'Gachibowli Stadium Turf, Hyderabad', 'Verified match history or certified regional tests required.', 16, 'Open')
    """)

    # 14. Trial Applications / Invitations
    cursor.execute("""
    INSERT INTO trial_applications (trial_id, player_id, status, evaluation_notes, trial_score, created_at)
    VALUES 
    (1, 1, 'invited', 'Invited based on 94% Smart Match suitability & 88 skill test.', NULL, '2026-09-01T14:20:00'),
    (1, 2, 'accepted', 'Confirmed attendance for all-rounder spot.', 85.0, '2026-09-02T11:00:00')
    """)

    # 15. Saved Talent (Coach / Club bookmarks)
    cursor.execute("""
    INSERT INTO saved_talent (user_id, player_id, notes, saved_at)
    VALUES 
    (6, 1, 'High priority batting talent. Outstanding boundary conversion rate and 91 batting accuracy.', '2026-08-30T12:00:00'),
    (6, 2, 'Solid seam-bowling all-rounder for middle overs acceleration.', '2026-08-30T12:00:00'),
    (6, 3, 'Late swing bowler with 94 bowling accuracy. Watch closely in upcoming state trials.', '2026-08-30T12:00:00'),
    (7, 1, 'Target recruitment for opening batsman spot in upcoming T20 League.', '2026-08-30T12:00:00')
    """)

    # 16. Notifications
    cursor.execute("""
    INSERT INTO notifications (user_id, category, title, message, link, is_read, timestamp)
    VALUES 
    (1, 'Opportunities', '🏏 Trial Invitation Received', 'Hyderabad Warriors CC invited you to the Under-23 State League Selection Trials on 20 September.', '#trials', 0, '2026-09-01T14:20:00'),
    (1, 'Verification', '🟢 Certificate Verified', 'Your District Under-19 Championship Trophy certificate has been verified by the Admin.', '#certificates', 0, '2026-08-01T10:00:00'),
    (1, 'Performance', '🌟 Classified as Rising Talent', 'Congratulations! Your composite score updated to 88.0 and you are featured in Rising Talent.', '#profile', 1, '2026-08-29T12:00:00'),
    (1, 'Connections', '🤝 New Connection', 'Coach Vikram Rathore accepted your connection request.', '#network', 1, '2026-08-29T11:00:00'),
    (6, 'Opportunities', 'New Rising Talent Spotlight', 'Rahul Kumar achieved +21% progress and 88 Skill Score in Hyderabad.', '#scout', 0, '2026-08-29T12:00:00')
    """)

    # 17. Reports (Formal investigation workflow)
    cursor.execute("""
    INSERT INTO reports (id, reporter_id, reported_user_id, reported_item_type, reported_item_id, report_type, description, evidence_text, status, admin_notes, created_at)
    VALUES 
    (1024, 6, 2, 'certificate', 4, 'fake_certificate', 'Suspicious certificate submitted without valid district council verification stamp and altered year.', 'Comparison with official 2024 TCA database records indicates participant was not registered in that bracket.', 'Under Review', 'Initiated audit with South Zone Sports Federation records department. Account remains active during investigation per platform policy.', '2026-09-03T16:00:00')
    """)

    # 18. Privacy Settings
    for uid in range(1, 10):
        cursor.execute("""
        INSERT INTO privacy_settings (user_id, profile_visibility, contact_visibility, stats_visibility, certs_visibility, connections_visibility)
        VALUES (?, 'public', 'connections_only', 'public', 'public', 'public')
        """, (uid,))

    conn.commit()

if __name__ == "__main__":
    init_db(force=True)
