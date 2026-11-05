"""Staff tools for the administrator (bursar, registrar, accommodation office).

Every function here is only reachable by an account whose role is 'admin' (see portal_api.py).
"""
import os
import re
import secrets
import sqlite3
from datetime import datetime
import portal_db as p
import portal_data as d
import portal_catalog as cat
from portal_data import ApiError, _rows, _text


def _temp_password():
    return secrets.token_urlsafe(9)


# =====================================================================  overview, payments, rooms, announcements
def overview(conn):
    one = lambda sql: conn.execute(sql).fetchone()[0]
    pend = conn.execute("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM payments WHERE status='recorded'").fetchone()
    return {"students": one("SELECT COUNT(*) FROM users WHERE role='student' AND status='active'"),
            "tutors": one("SELECT COUNT(*) FROM users WHERE role='tutor' AND status='active'"),
            "courses": one("SELECT COUNT(*) FROM courses"), "enrolments": one("SELECT COUNT(*) FROM enrolments"),
            "pendingPayments": {"count": pend[0], "amount": pend[1]},
            "pendingRooms": one("SELECT COUNT(*) FROM accommodation_requests WHERE status='requested'"),
            "collected": one("SELECT COALESCE(SUM(amount),0) FROM payments WHERE status='confirmed'"),
            "outstanding": one("SELECT COALESCE(SUM(balance),0) FROM v_fee_balance WHERE balance>0")}


def payments(conn):
    return {"payments": _rows(conn.execute("""SELECT p.id,u.full_name AS student,s.registration_number AS reg,p.amount,p.method,p.reference,p.status,
        p.paid_at AS paidAt,p.reviewed_at AS reviewedAt,(SELECT balance FROM v_fee_balance b WHERE b.student_id=p.student_id) AS balance
        FROM payments p JOIN students s ON s.user_id=p.student_id JOIN users u ON u.id=p.student_id
        ORDER BY CASE p.status WHEN 'recorded' THEN 0 ELSE 1 END, p.id DESC"""))}


def set_payment_status(conn, admin_id, payment_id, status):
    if status not in ("confirmed", "rejected", "recorded"):
        raise ApiError(400, "Choose confirmed, rejected or recorded.")
    if not conn.execute("SELECT 1 FROM payments WHERE id=?", (payment_id,)).fetchone():
        raise ApiError(404, "Payment not found.")
    conn.execute("UPDATE payments SET status=?, reviewed_by=?, reviewed_at=? WHERE id=?", (status, admin_id, p.now(), payment_id))
    return payments(conn)


def accommodation(conn):
    return {"requests": _rows(conn.execute("""SELECT a.student_id AS student,u.full_name AS name,s.registration_number AS reg,s.year_of_study AS year,
        r.name AS room,r.fee_per_term AS fee,a.status,a.requested_at AS requestedAt FROM accommodation_requests a
        JOIN students s ON s.user_id=a.student_id JOIN users u ON u.id=a.student_id JOIN room_types r ON r.id=a.room_type_id
        ORDER BY CASE a.status WHEN 'requested' THEN 0 ELSE 1 END, a.requested_at"""))}


def set_accommodation_status(conn, student_id, status):
    if status not in ("approved", "declined", "requested"):
        raise ApiError(400, "Choose approved, declined or requested.")
    if not conn.execute("SELECT 1 FROM accommodation_requests WHERE student_id=?", (student_id,)).fetchone():
        raise ApiError(404, "Request not found.")
    conn.execute("UPDATE accommodation_requests SET status=?, updated_at=? WHERE student_id=?", (status, p.now(), student_id))
    return accommodation(conn)


def announce(conn, admin_id, title, body, course):
    title, body = _text(title, "a title", 200), _text(body, "a message", 2000)
    code = None
    if course:
        code = d._course(conn, course)["code"]
    d.post_announcement(conn, title, body, admin_id, code)
    return {"posted": True}


# =====================================================================  people
def people(conn):
    students = _rows(conn.execute("""SELECT u.id,u.full_name AS name,u.email,u.status,s.id_number AS idNumber,s.registration_number AS reg,
        s.year_of_study AS year,u.last_login_at AS lastLogin,(SELECT COUNT(*) FROM enrolments e WHERE e.student_id=u.id) AS units
        FROM users u JOIN students s ON s.user_id=u.id ORDER BY u.full_name"""))
    tutors = _rows(conn.execute("""SELECT u.id,u.full_name AS name,u.email,u.status,t.staff_number AS staff,u.last_login_at AS lastLogin
        FROM users u JOIN tutors t ON t.user_id=u.id ORDER BY u.full_name"""))
    for t in tutors:
        t["courses"] = [r[0] for r in conn.execute("SELECT course_code FROM tutor_courses WHERE tutor_id=? ORDER BY course_code", (t["id"],))]
    admins = _rows(conn.execute("SELECT id,full_name AS name,email,status,last_login_at AS lastLogin FROM users WHERE role='admin' ORDER BY full_name"))
    return {"students": students, "tutors": tutors, "admins": admins}


def create_student(conn, data):
    pw = str(data.get("password") or "").strip() or _temp_password()
    try:
        year = int(data.get("year", 1))
    except (TypeError, ValueError):
        year = 0
    ok, msg = p.register_student(conn, str(data.get("name", "")), str(data.get("email", "")), str(data.get("idNumber", "")),
                                 str(data.get("regNumber", "")), year, pw)
    if not ok:
        raise ApiError(400, msg)
    conn.execute("UPDATE users SET must_change_password=1 WHERE email=?", (str(data.get("email", "")).strip().lower(),))
    return {"tempPassword": pw}


def create_tutor(conn, data):
    name = _text(data.get("name"), "a name", 120)
    email = _text(data.get("email"), "an email address", 200).lower()
    if not re.match(r"^\S+@\S+\.\S+$", email):
        raise ApiError(400, "Enter a valid email address.")
    staff = _text(data.get("staff"), "a staff number", 20, False) or None
    codes = [str(c).upper() for c in (data.get("courses") or [])]
    for c in codes:
        d._course(conn, c)
    pw = str(data.get("password") or "").strip() or _temp_password()
    if len(pw) < 8:
        raise ApiError(400, "Use a password with at least 8 characters.")
    try:
        uid = conn.execute("INSERT INTO users(role,email,password_hash,full_name,must_change_password) VALUES('tutor',?,?,?,1)", (email, p.hash_pw(pw), name)).lastrowid
        conn.execute("INSERT INTO tutors(user_id,staff_number) VALUES(?,?)", (uid, staff))
    except sqlite3.IntegrityError as e:
        raise ApiError(400, "That staff number is already in use." if "staff_number" in str(e) else "An account with this email already exists.")
    for c in codes:
        conn.execute("INSERT OR IGNORE INTO tutor_courses(tutor_id,course_code) VALUES(?,?)", (uid, c))
    return {"tempPassword": pw}


def _person(conn, user_id):
    row = conn.execute("SELECT id,role FROM users WHERE id=?", (user_id,)).fetchone()
    if not row:
        raise ApiError(404, "Account not found.")
    return row


def set_status(conn, admin_id, user_id, status):
    if status not in ("active", "suspended"):
        raise ApiError(400, "Choose active or suspended.")
    _person(conn, user_id)
    if user_id == admin_id:
        raise ApiError(400, "You can\u2019t suspend your own account.")
    conn.execute("UPDATE users SET status=? WHERE id=?", (status, user_id))
    if status == "suspended":
        conn.execute("UPDATE sessions SET revoked=1 WHERE user_id=?", (user_id,))
    return people(conn)


def reset_password(conn, admin_id, user_id):
    _person(conn, user_id)
    pw = _temp_password()
    conn.execute("UPDATE users SET password_hash=?, must_change_password=1, failed_attempts=0, locked_until=NULL WHERE id=?", (p.hash_pw(pw), user_id))
    conn.execute("UPDATE sessions SET revoked=1 WHERE user_id=?", (user_id,))
    return {"tempPassword": pw}


def set_tutor_courses(conn, tutor_id, codes):
    row = _person(conn, tutor_id)
    if row["role"] != "tutor":
        raise ApiError(400, "That account isn\u2019t a tutor.")
    codes = [d._course(conn, c)["code"] for c in (codes or [])]
    conn.execute("DELETE FROM tutor_courses WHERE tutor_id=?", (tutor_id,))
    for c in codes:
        conn.execute("INSERT OR IGNORE INTO tutor_courses(tutor_id,course_code) VALUES(?,?)", (tutor_id, c))
    return people(conn)


# =====================================================================  courses and coursework
def _int(value, field, lo, hi):
    try:
        v = int(value)
    except (TypeError, ValueError):
        raise ApiError(400, f"Enter a whole number for {field}.")
    if not lo <= v <= hi:
        raise ApiError(400, f"The {field} must be between {lo} and {hi}.")
    return v


def save_course(conn, data):
    code = str(data.get("code") or "").strip().upper()
    if not re.fullmatch(r"[A-Z]{2}\d{3}", code):
        raise ApiError(400, "A course code is two letters and three digits, like OT101.")
    title = _text(data.get("title"), "a title", 120)
    credits = _int(data.get("credits"), "credits", 1, 10)
    fee = _int(data.get("fee"), "fee", 0, 10_000_000)
    desc = _text(data.get("description"), "a description", 500, False)
    room = _text(data.get("room"), "a room", 60, False)
    venue = _text(data.get("examVenue"), "an exam venue", 60, False)
    exam = str(data.get("examAt") or "").strip() or None
    if exam:
        try:
            datetime.strptime(exam, "%Y-%m-%d %H:%M")
        except ValueError:
            raise ApiError(400, "Write the exam date and time like 2026-12-07 09:00.")
    sessions = sorted({(_int(x[0], "day", 0, 4), _int(x[1], "class period", 0, len(cat.BANDS) - 1)) for x in (data.get("sessions") or [])})
    when = cat.when_text(sessions)
    exists = conn.execute("SELECT 1 FROM courses WHERE code=?", (code,)).fetchone()
    if exists:
        conn.execute("""UPDATE courses SET title=?,credits=?,description=?,tuition_fee=?,class_time=?,room=?,exam_at=?,exam_venue=? WHERE code=?""",
                     (title, credits, desc, fee, when, room, exam, venue, code))
    else:
        conn.execute("""INSERT INTO courses(code,title,credits,description,tuition_fee,class_time,room,exam_at,exam_venue) VALUES(?,?,?,?,?,?,?,?,?)""",
                     (code, title, credits, desc, fee, when, room, exam, venue))
    conn.execute("DELETE FROM class_sessions WHERE course_code=?", (code,))
    for day, band in sessions:
        conn.execute("INSERT INTO class_sessions(course_code,day,band,start_time,end_time) VALUES(?,?,?,?,?)", (code, day, band, cat.BANDS[band][0], cat.BANDS[band][1]))
    return {"created": not exists, "code": code}


def save_coursework(conn, data):
    course = d._course(conn, data.get("course"))["code"]
    title = _text(data.get("title"), "a title", 200)
    desc = _text(data.get("description"), "a description", 1000, False)
    due = str(data.get("due") or "").strip()
    try:
        datetime.strptime(due, "%Y-%m-%d")
    except ValueError:
        raise ApiError(400, "Write the due date like 2026-11-20.")
    pts = _int(data.get("max"), "marks", 1, 100)
    kind = str(data.get("kind") or "assignment")
    if kind not in cat.KINDS:
        raise ApiError(400, "Choose a kind of coursework.")
    cid = str(data.get("id") or "").strip()
    if cid:
        row = conn.execute("SELECT course_code FROM assignments WHERE id=?", (cid,)).fetchone()
        if not row or row["course_code"] != course:
            raise ApiError(404, "That coursework item doesn\u2019t exist in this course.")
        conn.execute("UPDATE assignments SET title=?,description=?,due_date=?,max_marks=?,kind=? WHERE id=?", (title, desc, due, pts, kind, cid))
    else:
        n = 1
        while conn.execute("SELECT 1 FROM assignments WHERE id=?", (course.lower() + "-" + str(n),)).fetchone():
            n += 1
        cid = course.lower() + "-" + str(n)
        conn.execute("INSERT INTO assignments(id,course_code,title,description,due_date,max_marks,kind) VALUES(?,?,?,?,?,?,?)", (cid, course, title, desc, due, pts, kind))
    return {"id": cid}


def delete_coursework(conn, cid):
    row = conn.execute("SELECT course_code FROM assignments WHERE id=?", (str(cid or ""),)).fetchone()
    if not row:
        raise ApiError(404, "Coursework item not found.")
    paths = [r[0] for r in conn.execute("""SELECT f.stored_path FROM submission_files f JOIN submissions s ON s.id=f.submission_id
                                           WHERE s.assignment_id=? AND f.stored_path IS NOT NULL""", (cid,))]
    conn.execute("DELETE FROM marks WHERE course_code=? AND assessment=?", (row["course_code"], cid))
    conn.execute("DELETE FROM assignments WHERE id=?", (cid,))          # submissions and their file records go with it
    for rel in paths:
        try:
            os.remove(d._upload_path(rel))
        except OSError:
            pass
    return {"deleted": True}
