#!/usr/bin/env python3
"""Upgrade an existing portal.db to the current design (version 2) without losing accounts or login records.

Usage:  python3 upgrade_database.py
It first saves a backup copy next to portal.db, then adds the new tables and the starting content.
Running it again is harmless. (The server also does this automatically each time it starts.)
"""
import os, sys
import portal_db as p

if not os.path.exists(p.DB):
    sys.exit("No portal.db found here. Start the server once (python3 server.py) and it will create one.")
print("Backup saved:", os.path.basename(p.backup_database()))
conn = p.connect()
p.migrate(conn)
print("Database is now at version", conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0])
for t in ("users", "students", "tutors", "courses", "enrolments", "lecture_notes", "assignments", "submissions", "marks",
          "payments", "accommodation_requests", "announcements", "site_content", "login_events"):
    print(f"  {t:24}{conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]} rows")
