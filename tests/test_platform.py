"""
SportsConnect Platform Verification Tests
Validates authentication, dynamic classification, smart matching,
certificate verification, match recording, trials, and reporting workflow.
"""

import os
import sys
import unittest
import json
import sqlite3

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, get_db, hash_pw, DB_PATH
from server import calculate_player_classification, smart_match

class TestSportsConnectPlatform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db(force=True)

    def test_01_user_seeding_and_auth(self):
        """Verify seeded users exist and password hashing works correctly."""
        conn = get_db()
        cursor = conn.cursor()

        # Check Rahul Kumar (Player)
        cursor.execute("SELECT id, role, password_hash FROM users WHERE username = 'rahulkumar'")
        user = cursor.fetchone()
        self.assertIsNotNone(user, "Rahul Kumar user must exist")
        self.assertEqual(user['role'], 'Player')
        self.assertTrue(__import__('database').verify_pw('password123', user['password_hash']))

        # Check Coach Vikram
        cursor.execute("SELECT id, role FROM users WHERE username = 'coachvikram'")
        coach = cursor.fetchone()
        self.assertIsNotNone(coach)
        self.assertEqual(coach['role'], 'Coach')

        # Admin is now an environment-only identity and must not be seeded into the database.
        cursor.execute("SELECT id FROM users WHERE role = 'Admin'")
        self.assertIsNone(cursor.fetchone())
        conn.close()

    def test_02_rising_talent_classification_model(self):
        """
        Verify Rising Talent algorithm:
        High skill + high performance + high progress with limited major experience
        MUST classify as 'Rising Talent'.
        """
        # Rahul Kumar's profile metrics: skill 88, perf 86, progress +21%, 0 major matches
        classification, score = calculate_player_classification(88.0, 86.0, 21.0, 0, achievements_count=2)
        self.assertEqual(classification, "Rising Talent", "Must classify as Rising Talent when skill & progress are high despite low experience")
        self.assertGreaterEqual(score, 75.0)

        # Player with lots of experience (15 matches) and high skill -> Elite
        elite_class, elite_score = calculate_player_classification(92.0, 90.0, 10.0, 16, achievements_count=5)
        self.assertEqual(elite_class, "Elite Player")

        # Player with medium stats -> Emerging
        emerging_class, _ = calculate_player_classification(70.0, 72.0, 8.0, 2, achievements_count=1)
        self.assertEqual(emerging_class, "Emerging Player")

    def test_03_smart_matching_engine(self):
        """Verify smart match recommendation score and explanation checklist."""
        player = {
            "sport": "Cricket",
            "position": "Batsman",
            "location": "Hyderabad",
            "skill_score": 88.0,
            "performance_score": 86.0,
            "availability": "Available for Trials",
            "classification": "Rising Talent"
        }
        criteria = {
            "sport": "Cricket",
            "position": "Batsman",
            "location": "Hyderabad",
            "min_skill": 80.0
        }
        score, reasons = smart_match(player, criteria)
        self.assertGreaterEqual(score, 90, f"Expected high match percentage, got {score}")
        self.assertTrue(any("Same sport" in r for r in reasons))
        self.assertTrue(any("Same role" in r for r in reasons))
        self.assertTrue(any("Same location" in r for r in reasons))
        self.assertTrue(any("Skill score meets requirement" in r for r in reasons))
        self.assertTrue(any("Rising Talent" in r for r in reasons))

    def test_04_certificate_verification_integrity(self):
        """Verify certificates cannot be self-verified and must pass through admin queue."""
        conn = get_db()
        cursor = conn.cursor()

        # Check pending certificate for Rahul Kumar
        cursor.execute("SELECT id, status, verified_by FROM certificates WHERE player_id = 1 AND status = 'pending'")
        pending_cert = cursor.fetchone()
        self.assertIsNotNone(pending_cert, "Pending certificate must exist in queue")
        self.assertIsNone(pending_cert['verified_by'])

        # Check verified certificate
        cursor.execute("SELECT id, status, verified_by FROM certificates WHERE player_id = 1 AND status = 'verified'")
        verified_cert = cursor.fetchone()
        self.assertIsNotNone(verified_cert)
        self.assertIsNotNone(verified_cert['verified_by'])
        conn.close()

    def test_05_verified_match_records_and_teammates(self):
        """Verify match history contains verified status and links teammates ('Played With')."""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT m.title, m.status, m.verified_by, mps.player_id, mps.stats_json
        FROM matches m
        JOIN match_player_stats mps ON m.id = mps.match_id
        WHERE mps.player_id = 1
        """)
        match_stats = cursor.fetchall()
        self.assertGreaterEqual(len(match_stats), 1)
        first_match = match_stats[0]
        self.assertEqual(first_match['status'], 'verified')
        stats = json.loads(first_match['stats_json'])
        self.assertEqual(stats['runs'], 72)

        # Check that Teammate Arjun Reddy played in the same match
        cursor.execute("""
        SELECT mps.player_id, u.full_name
        FROM match_player_stats mps
        JOIN users u ON mps.player_id = u.id
        WHERE mps.match_id = 1 AND mps.player_id = 2
        """)
        teammate = cursor.fetchone()
        self.assertIsNotNone(teammate)
        self.assertEqual(teammate['full_name'], 'Arjun Reddy')
        conn.close()

    def test_06_report_investigation_workflow(self):
        """Verify Report #1024 exists with 'Under Review' status and does not auto-punish user."""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT id, status, reporter_id, reported_user_id FROM reports WHERE id = 1024")
        report = cursor.fetchone()
        self.assertIsNotNone(report)
        self.assertEqual(report['status'], 'Under Review')

        # The reported user (Arjun Reddy, id=2) must still be active!
        cursor.execute("SELECT status FROM users WHERE id = ?", (report['reported_user_id'],))
        user_status = cursor.fetchone()['status']
        self.assertEqual(user_status, 'active', "Reported user must NOT be automatically suspended without investigation")
        conn.close()

if __name__ == "__main__":
    unittest.main()
