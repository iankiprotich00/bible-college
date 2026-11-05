#!/usr/bin/env python3
"""Cornerstone Bible College: login database helper (SQLite, standard library only).

Run `python3 portal_db.py` to rebuild portal.db with demo data and see a short demo.
Import it (`import portal_db`) to use register_student() and login() from your own server code.
"""
import hashlib, hmac, os, re, secrets, sqlite3
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "portal.db")
SCHEMA = os.path.join(HERE, "schema.sql")
MAX_FAILS, LOCK_MINUTES, SESSION_HOURS = 5, 15, 12
GENERIC = "These details or the password are incorrect."

def _fmt(t): return t.strftime("%Y-%m-%d %H:%M:%S")
def now(): return _fmt(datetime.now(timezone.utc))
def later(**kw): return _fmt(datetime.now(timezone.utc) + timedelta(**kw))

def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ---- passwords: salted PBKDF2, never stored in plain text ----
def hash_pw(pw, iters=200_000):
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, iters)
    return f"pbkdf2_sha256${iters}${salt.hex()}${h.hex()}"

def check_pw(pw, stored):
    _, iters, salt, h = stored.split("$")
    test = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), int(iters))
    return hmac.compare_digest(test.hex(), h)

# ---- accounts ----
def register_student(conn, name, email, id_number, registration_number, year, password):
    email = email.strip().lower()
    reg = registration_number.replace(" ", "").upper()
    if not name.strip(): return False, "Enter your full name."
    if not re.match(r"^\S+@\S+\.\S+$", email): return False, "Enter a valid email address."
    if not id_number.strip(): return False, "Enter your ID number."
    if not reg: return False, "Enter your student registration number."
    if year not in (1, 2, 3, 4): return False, "Year of study must be 1 to 4."
    if len(password) < 8: return False, "Use a password with at least 8 characters."
    try:
        with conn:
            cur = conn.execute("INSERT INTO users(role,email,password_hash,full_name) VALUES('student',?,?,?)",
                               (email, hash_pw(password), name.strip()))
            conn.execute("INSERT INTO students(user_id,id_number,registration_number,year_of_study) VALUES(?,?,?,?)",
                         (cur.lastrowid, id_number.strip(), reg, year))
    except sqlite3.IntegrityError as e:
        msg = str(e)
        if "users.email" in msg: return False, "An account with this email already exists."
        if "id_number" in msg: return False, "An account with this ID number already exists."
        return False, "An account with this registration number already exists."
    return True, "Account created."

def _find(conn, portal, method, ident):
    if portal == "tutor":
        return conn.execute("SELECT * FROM users WHERE role IN ('tutor','admin') AND email=?", (ident,)).fetchone()
    if method == "email":
        return conn.execute("SELECT * FROM users WHERE role='student' AND email=?", (ident,)).fetchone()
    col = "id_number" if method == "id_number" else "registration_number"
    if method == "registration_number": ident = ident.replace(" ", "")
    return conn.execute(f"SELECT u.* FROM users u JOIN students s ON s.user_id=u.id WHERE s.{col}=?", (ident,)).fetchone()

def login(conn, portal, method, identifier, password, ip=None, user_agent=None):
    """Returns (ok, message, session_token). Every attempt is recorded in login_events."""
    identifier = identifier.strip()
    if portal == "tutor": method = "email"
    row = _find(conn, portal, method, identifier)
    def log(ok, reason, uid=None):
        conn.execute("INSERT INTO login_events(user_id,portal,method,identifier,success,reason,ip_address,user_agent) VALUES(?,?,?,?,?,?,?,?)",
                     (uid, portal, method, identifier, int(ok), reason, ip, user_agent))
    def fail(reason, msg=GENERIC, uid=None):
        log(False, reason, uid); conn.commit(); return False, msg, None
    if not row: return fail("unknown user")
    uid = row["id"]
    if row["status"] != "active": return fail("account " + row["status"], "This account is not active. Contact the registrar.", uid)
    if row["locked_until"] and row["locked_until"] > now(): return fail("account locked", "Too many attempts. Try again later.", uid)
    if not check_pw(password, row["password_hash"]):
        fails, locked = row["failed_attempts"] + 1, None
        if fails >= MAX_FAILS: fails, locked = 0, later(minutes=LOCK_MINUTES)
        conn.execute("UPDATE users SET failed_attempts=?, locked_until=? WHERE id=?", (fails, locked, uid))
        return fail("bad password", GENERIC, uid)
    token = secrets.token_urlsafe(32)
    conn.execute("UPDATE users SET failed_attempts=0, locked_until=NULL, last_login_at=? WHERE id=?", (now(), uid))
    conn.execute("INSERT INTO sessions(user_id,portal,token_hash,expires_at) VALUES(?,?,?,?)",
                 (uid, portal, hashlib.sha256(token.encode()).hexdigest(), later(hours=SESSION_HOURS)))
    log(True, None, uid); conn.commit()
    return True, "Logged in.", token

def check_session(conn, token):
    h = hashlib.sha256(token.encode()).hexdigest()
    return conn.execute("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.revoked=0 AND s.expires_at>?",
                        (h, now())).fetchone()

def logout(conn, token):
    conn.execute("UPDATE sessions SET revoked=1 WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),)); conn.commit()

UPLOAD_DIR = os.path.join(HERE, "uploads")        # submitted assignment files are stored here

def change_password(conn, user_id, current, new, token):
    """Change your own password. Signs out every other device. Returns (ok, message)."""
    row = conn.execute("SELECT password_hash FROM users WHERE id=?", (user_id,)).fetchone()
    if not row or not check_pw(current, row["password_hash"]): return False, "Your current password is not right."
    if len(new) < 8: return False, "Use a new password with at least 8 characters."
    if new == current: return False, "Choose a password different from the current one."
    conn.execute("UPDATE users SET password_hash=?, must_change_password=0, failed_attempts=0, locked_until=NULL WHERE id=?", (hash_pw(new), user_id))
    conn.execute("UPDATE sessions SET revoked=1 WHERE user_id=? AND token_hash<>?", (user_id, hashlib.sha256(token.encode()).hexdigest()))
    conn.commit()
    return True, "Password changed."

def create_admin(conn, name, email, password):
    """Make a college administrator account (bursar / registrar). Returns (ok, message)."""
    email = email.strip().lower()
    if not name.strip(): return False, "Enter a name."
    if not re.match(r"^\S+@\S+\.\S+$", email): return False, "Enter a valid email address."
    if len(password) < 8: return False, "Use a password with at least 8 characters."
    try:
        conn.execute("INSERT INTO users(role,email,password_hash,full_name) VALUES('admin',?,?,?)", (email, hash_pw(password), name.strip()))
        conn.commit()
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."
    return True, "Administrator account created."

def profile(conn, u):
    """What the web page needs to know about a logged-in person."""
    out = {"role": u["role"], "name": u["full_name"], "email": u["email"], "mustChange": bool(u["must_change_password"])}
    prev = conn.execute("SELECT created_at FROM login_events WHERE user_id=? AND success=1 ORDER BY id DESC LIMIT 1 OFFSET 1",
                        (u["id"],)).fetchone()
    out["previousLogin"] = prev[0] if prev else None
    if u["role"] == "student":
        s = conn.execute("SELECT * FROM students WHERE user_id=?", (u["id"],)).fetchone()
        out.update(idNumber=s["id_number"], regNumber=s["registration_number"], year=s["year_of_study"])
    elif u["role"] == "tutor":
        out["staffNumber"] = conn.execute("SELECT staff_number FROM tutors WHERE user_id=?", (u["id"],)).fetchone()[0]
        out["courses"] = [r[0] for r in conn.execute("SELECT course_code FROM tutor_courses WHERE tutor_id=?", (u["id"],))]
    return out

def set_year(conn, user_id, year):
    if year not in (1, 2, 3, 4): return False
    conn.execute("UPDATE students SET year_of_study=? WHERE user_id=?", (year, user_id)); conn.commit()
    return True

# ---- demo data (matches the prototype's sample tutors, students and courses) ----
SCHEMA_VERSION = 3
USER_COLUMNS = {"must_change_password": "INTEGER NOT NULL DEFAULT 0"}
PAYMENT_COLUMNS = {"reviewed_by": "INTEGER", "reviewed_at": "TEXT"}
ASSIGNMENT_COLUMNS = {"kind": "TEXT NOT NULL DEFAULT 'assignment'"}
COURSE_COLUMNS = {"description": "TEXT NOT NULL DEFAULT ''", "tuition_fee": "INTEGER NOT NULL DEFAULT 0",
                  "class_time": "TEXT NOT NULL DEFAULT ''", "room": "TEXT NOT NULL DEFAULT ''",
                  "exam_at": "TEXT", "exam_venue": "TEXT NOT NULL DEFAULT ''"}

def migrate(conn):
    """Bring any portal.db (new, or made by an earlier version) up to the current design.
    Safe to run repeatedly. Existing accounts and login records are kept."""
    for table, cols in (("courses", COURSE_COLUMNS), ("assignments", ASSIGNMENT_COLUMNS),
                        ("users", USER_COLUMNS), ("payments", PAYMENT_COLUMNS)):
        have = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        for col, ddl in cols.items():                  # an older table needs the new columns before the schema runs
            if have and col not in have:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")
    conn.executescript(open(SCHEMA, encoding="utf-8").read())
    import portal_seed
    portal_seed.seed_reference(conn)
    conn.execute("INSERT OR IGNORE INTO schema_version(version,note) VALUES(?,?)", (SCHEMA_VERSION, "staff tools, file storage, password changes"))
    conn.commit()

def needs_upgrade(conn):
    """True if this database was made by an older version of the portal."""
    try:
        v = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    except sqlite3.OperationalError:
        return True
    return (v or 0) < SCHEMA_VERSION

def backup_database():
    """Copy portal.db to portal.db.backup-<time> (never overwriting an earlier backup). Returns the new file's path."""
    import shutil
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path, n = f"{DB}.backup-{stamp}", 1
    while os.path.exists(path):
        n += 1
        path = f"{DB}.backup-{stamp}-{n}"
    shutil.copy2(DB, path)
    return path

def build():
    """Create a brand-new portal.db with demo data (this deletes any existing one)."""
    import portal_seed
    if os.path.exists(DB): os.remove(DB)
    conn = connect()
    migrate(conn)
    portal_seed.seed_people(conn)
    portal_seed.seed_reference(conn)                   # now that tutors exist, add their lecture notes
    portal_seed.seed_demo(conn)
    return conn

def demo(conn):
    ua = "demo-seed"
    login(conn, "student", "email", "joy.wanjiru@students.cornerstone.example", "student1234", "127.0.0.1", ua)
    login(conn, "student", "id_number", "30110002", "student1234", "127.0.0.1", ua)
    login(conn, "student", "registration_number", "cbc/2026/0103", "student1234", "127.0.0.1", ua)
    login(conn, "student", "email", "joy.wanjiru@students.cornerstone.example", "wrong-password", "127.0.0.1", ua)
    login(conn, "student", "email", "nobody@students.cornerstone.example", "x", "127.0.0.1", ua)
    login(conn, "tutor", "email", "amani@cornerstone.example", "tutor1234", "127.0.0.1", ua)
    login(conn, "tutor", "email", "ruth@cornerstone.example", "badpass", "127.0.0.1", ua)
    conn.execute("DELETE FROM sessions"); conn.commit()   # demo sessions aren't kept

if __name__ == "__main__":
    c = build(); demo(c)
    print("Built", DB)
    for t in ("users", "students", "tutors", "courses", "login_events"):
        print(f"  {t}: {c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]} rows")
    print("\nLogin history:")
    for r in c.execute("SELECT * FROM v_login_history"):
        print(f"  {r['created_at']}  {r['portal']:<7} {r['person']:<20} via {r['method']:<20} {'OK' if r['success'] else 'FAILED (' + r['reason'] + ')'}")
