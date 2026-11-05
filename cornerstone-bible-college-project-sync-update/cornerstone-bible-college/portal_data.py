"""Data access for every portal page: one function per thing a page needs.

Each function takes an open database connection and the id of the signed-in person, checks that the person is
allowed to do it, and returns plain dictionaries ready to send as JSON. Problems raise ApiError(status, message).
"""
import base64
import binascii
import os
import re
import uuid
import portal_db as p

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_UPLOAD_TOTAL = 30 * 1024 * 1024       # all files in one submission together
UPLOAD_DIR = p.UPLOAD_DIR
IN_CLASS = ("quiz", "practical")        # coursework held in class: marked by the tutor, no file to upload
PAY_METHODS = ("Bank transfer", "Mobile money", "Cash at the bursar\u2019s office")


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status, self.message = status, message


def _rows(cur):
    return [dict(r) for r in cur.fetchall()]


def _text(value, field, maxlen, required=True):
    t = str(value if value is not None else "").strip()
    if required and not t:
        raise ApiError(400, f"Enter {field}.")
    if len(t) > maxlen:
        raise ApiError(400, f"The {field} is too long (limit {maxlen} characters).")
    return t


def _course(conn, code):
    code = str(code or "").strip().upper()
    row = conn.execute("SELECT * FROM courses WHERE code=?", (code,)).fetchone()
    if not row:
        raise ApiError(404, "That course doesn\u2019t exist.")
    return row


def _setting(conn, key):
    return int(conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()[0])


# =====================================================================  courses and enrolment
def _sessions(conn, code):
    return _rows(conn.execute("SELECT day,band,start_time AS start,end_time AS end FROM class_sessions WHERE course_code=? ORDER BY day,band", (code,)))


def list_courses(conn):
    out = _rows(conn.execute("SELECT code,title,credits,description,tuition_fee,class_time,room,exam_at,exam_venue FROM courses ORDER BY code"))
    for c in out:
        c["sessions"] = _sessions(conn, c["code"])
        c["tutors"] = [r[0] for r in conn.execute(
            "SELECT u.full_name FROM tutor_courses t JOIN users u ON u.id=t.tutor_id WHERE t.course_code=? ORDER BY u.full_name", (c["code"],))]
    return out


def enrolled_codes(conn, sid):
    return [r[0] for r in conn.execute("SELECT course_code FROM enrolments WHERE student_id=? ORDER BY course_code", (sid,))]


def enrol(conn, sid, code):
    c = _course(conn, code)
    conn.execute("INSERT OR IGNORE INTO enrolments(student_id,course_code) VALUES(?,?)", (sid, c["code"]))
    return enrolled_codes(conn, sid)


def drop(conn, sid, code):
    c = _course(conn, code)
    conn.execute("DELETE FROM enrolments WHERE student_id=? AND course_code=?", (sid, c["code"]))   # notes and marks are kept
    return enrolled_codes(conn, sid)


def _require_enrolled(conn, sid, code):
    if code not in enrolled_codes(conn, sid):
        raise ApiError(403, "Enrol in this course first.")


def schedule(conn, sid):
    """Timetable and exam dates for the courses the student is enrolled in."""
    rows = _rows(conn.execute("""SELECT c.code,c.title,c.class_time,c.room,c.exam_at,c.exam_venue FROM enrolments e
                                 JOIN courses c ON c.code=e.course_code WHERE e.student_id=? ORDER BY c.code""", (sid,)))
    for r in rows:
        r["tutors"] = [x[0] for x in conn.execute("SELECT u.full_name FROM tutor_courses t JOIN users u ON u.id=t.tutor_id WHERE t.course_code=?", (r["code"],))]
        r["sessions"] = _sessions(conn, r["code"])
    return rows


# =====================================================================  catalogue and the student's whole state
def catalog(conn):
    """Everything the pages need to know about every course. Public: it is the same list shown on the welcome page."""
    import portal_catalog as cat
    courses = list_courses(conn)
    work = {}
    for r in _rows(conn.execute("SELECT id,course_code,title,description,due_date AS due,max_marks AS max,kind FROM assignments ORDER BY due_date,id")):
        work.setdefault(r.pop("course_code"), []).append(r)
    for c in courses:
        c["coursework"] = work.get(c["code"], [])
    return {"courses": courses, "bands": [list(b) for b in cat.BANDS]}


def student_state(conn, user):
    """One call that returns what a student's screens show, so a phone can sync everything at once."""
    sid = user["id"]
    codes = enrolled_codes(conn, sid)
    notes = {c: _rows(conn.execute("SELECT id,title,scripture_ref AS ref,body,created_at AS postedAt FROM lecture_notes WHERE course_code=? ORDER BY id", (c,))) for c in codes}
    subs = {}
    for c in codes:
        for a in conn.execute("SELECT id FROM assignments WHERE course_code=?", (c,)):
            s = _submission(conn, sid, a["id"])
            if s:
                subs[a["id"]] = s
    return {"enrolled": codes, "notes": notes, "submissions": subs, "results": results(conn, sid), "fees": fees(conn, sid),
            "accommodation": accommodation(conn, sid), "news": announcements(conn, user),
            "content": {sec: content(conn, sec) for sec in ("library", "chapel", "about", "help")}}


# =====================================================================  course page
def course_detail(conn, sid, code):
    c = _course(conn, code)
    _require_enrolled(conn, sid, c["code"])
    detail = {k: c[k] for k in c.keys()}
    detail["tutors"] = [r[0] for r in conn.execute("SELECT u.full_name FROM tutor_courses t JOIN users u ON u.id=t.tutor_id WHERE t.course_code=?", (c["code"],))]
    notes = _rows(conn.execute("SELECT id,title,scripture_ref AS ref,body,created_at AS postedAt FROM lecture_notes WHERE course_code=? ORDER BY id", (c["code"],)))
    assignments = _rows(conn.execute("SELECT id,title,description,due_date AS due,max_marks AS maxMarks,kind FROM assignments WHERE course_code=? ORDER BY due_date,id", (c["code"],)))
    for a in assignments:
        a["submission"] = _submission(conn, sid, a["id"])
    return {"course": detail, "lectureNotes": notes, "assignments": assignments, "myNotes": my_notes(conn, sid, c["code"])}


# =====================================================================  a student's own notes
def my_notes(conn, sid, code=None):
    sql = "SELECT id,course_code AS course,title,scripture_ref AS ref,body,created_at AS createdAt,updated_at AS updatedAt FROM student_notes WHERE student_id=?"
    args = [sid]
    if code:
        sql += " AND course_code=?"
        args.append(str(code).upper())
    return _rows(conn.execute(sql + " ORDER BY id DESC", args))


def add_note(conn, sid, code, title, ref, body):
    c = _course(conn, code)
    _require_enrolled(conn, sid, c["code"])
    title, ref, body = _text(title, "a title", 200), _text(ref, "reference", 100, False), _text(body, "note", 20000)
    cur = conn.execute("INSERT INTO student_notes(student_id,course_code,title,scripture_ref,body) VALUES(?,?,?,?,?)", (sid, c["code"], title, ref, body))
    return {"id": cur.lastrowid, "notes": my_notes(conn, sid, c["code"])}


def update_note(conn, sid, note_id, title, ref, body):
    row = conn.execute("SELECT course_code FROM student_notes WHERE id=? AND student_id=?", (note_id, sid)).fetchone()
    if not row:
        raise ApiError(404, "Note not found.")
    title, ref, body = _text(title, "a title", 200), _text(ref, "reference", 100, False), _text(body, "note", 20000)
    conn.execute("UPDATE student_notes SET title=?,scripture_ref=?,body=?,updated_at=? WHERE id=?", (title, ref, body, p.now(), note_id))
    return {"notes": my_notes(conn, sid, row["course_code"])}


def delete_note(conn, sid, note_id):
    row = conn.execute("SELECT course_code FROM student_notes WHERE id=? AND student_id=?", (note_id, sid)).fetchone()
    if not row:
        raise ApiError(404, "Note not found.")
    conn.execute("DELETE FROM student_notes WHERE id=?", (note_id,))
    return {"notes": my_notes(conn, sid, row["course_code"])}


# =====================================================================  assignments and submissions
def _submission(conn, sid, assignment_id):
    s = conn.execute("SELECT id,comment,submitted_at AS submittedAt FROM submissions WHERE assignment_id=? AND student_id=?", (assignment_id, sid)).fetchone()
    if not s:
        return None
    out = dict(s)
    out["files"] = _files(conn, s["id"])
    del out["id"]
    return out


def _files(conn, submission_id):
    rows = _rows(conn.execute("SELECT id,file_name AS name,size_bytes AS size,(stored_path IS NOT NULL) AS stored FROM submission_files WHERE submission_id=? ORDER BY id", (submission_id,)))
    for r in rows:
        r["stored"] = bool(r["stored"])
    return rows


def _upload_path(rel):
    base = os.path.realpath(UPLOAD_DIR)
    full = os.path.realpath(os.path.join(base, rel))
    if os.path.commonpath([base, full]) != base:
        raise ApiError(400, "Bad file path.")
    return full


def _safe_name(name):
    return re.sub(r"[^A-Za-z0-9._ -]", "_", name)[:120] or "file"


def submit(conn, sid, assignment_id, comment, files):
    a = conn.execute("SELECT * FROM assignments WHERE id=?", (str(assignment_id or ""),)).fetchone()
    if not a:
        raise ApiError(404, "That assignment doesn\u2019t exist.")
    _require_enrolled(conn, sid, a["course_code"])
    if a["kind"] in IN_CLASS:
        raise ApiError(400, "This is done in class, so there is nothing to submit. Your tutor enters your mark.")
    if not isinstance(files, list) or not 1 <= len(files) <= 10:
        raise ApiError(400, "Attach between 1 and 10 files before submitting.")
    clean, total = [], 0
    for f in files:
        if not isinstance(f, dict):
            raise ApiError(400, "Bad file details.")
        name = re.sub(r"[\x00-\x1f]", "", os.path.basename(str(f.get("name", "")).replace("\\", "/"))).strip()
        if not name or len(name) > 255:
            raise ApiError(400, "A file has no usable name.")
        raw = None
        if f.get("data") is not None:                    # the file's contents, sent as base64
            try:
                raw = base64.b64decode(str(f["data"]), validate=True)
            except (binascii.Error, ValueError):
                raise ApiError(400, f"{name} could not be read. Try attaching it again.")
            size = len(raw)
        else:                                            # older clients send only the name and size
            try:
                size = int(f.get("size", 0))
            except (TypeError, ValueError):
                size = -1
        if not 0 <= size <= MAX_FILE_BYTES:
            raise ApiError(400, f"{name} is over 10 MB.")
        total += size
        if total > MAX_UPLOAD_TOTAL:
            raise ApiError(400, "These files add up to more than 30 MB. Submit fewer or smaller files.")
        clean.append((name, size, raw))
    comment = _text(comment, "comment", 2000, False)
    old = conn.execute("SELECT id FROM submissions WHERE assignment_id=? AND student_id=?", (a["id"], sid)).fetchone()
    old_paths = []
    if old:                                              # resubmitting replaces the earlier submission and its files
        old_paths = [r[0] for r in conn.execute("SELECT stored_path FROM submission_files WHERE submission_id=?", (old["id"],)) if r[0]]
        conn.execute("DELETE FROM submission_files WHERE submission_id=?", (old["id"],))
        conn.execute("UPDATE submissions SET comment=?, submitted_at=? WHERE id=?", (comment, p.now(), old["id"]))
        sub_id = old["id"]
    else:
        sub_id = conn.execute("INSERT INTO submissions(assignment_id,student_id,comment) VALUES(?,?,?)", (a["id"], sid, comment)).lastrowid
    for name, size, raw in clean:
        rel = None
        if raw is not None:
            rel = f"{a['id']}/{sid}/{uuid.uuid4().hex}_{_safe_name(name)}"
            full = _upload_path(rel)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "wb") as fh:
                fh.write(raw)
        conn.execute("INSERT INTO submission_files(submission_id,file_name,size_bytes,stored_path) VALUES(?,?,?,?)", (sub_id, name, size, rel))
    for rel in old_paths:
        try:
            os.remove(_upload_path(rel))
        except OSError:
            pass
    return {"submission": _submission(conn, sid, a["id"])}


def get_file(conn, user, file_id):
    """Who may open a submitted file: the student who sent it, a tutor of that course, or an administrator."""
    row = conn.execute("""SELECT f.file_name, f.stored_path, s.student_id, a.course_code FROM submission_files f
                          JOIN submissions s ON s.id=f.submission_id JOIN assignments a ON a.id=s.assignment_id WHERE f.id=?""", (file_id,)).fetchone()
    if not row:
        raise ApiError(404, "File not found.")
    role = user["role"]
    ok = role == "admin" or (role == "student" and row["student_id"] == user["id"]) or (
        role == "tutor" and conn.execute("SELECT 1 FROM tutor_courses WHERE tutor_id=? AND course_code=?", (user["id"], row["course_code"])).fetchone())
    if not ok:
        raise ApiError(403, "You can\u2019t open this file.")
    if not row["stored_path"]:
        raise ApiError(404, "Only this file\u2019s name was recorded, so there is nothing to download.")
    full = _upload_path(row["stored_path"])
    if not os.path.isfile(full):
        raise ApiError(404, "The file is missing from the server.")
    return row["file_name"], full


# =====================================================================  grading and the result slip
def _band(pct, pass_mark, conn):
    if pct >= _setting(conn, "grade_a"): return "A", 4
    if pct >= _setting(conn, "grade_b"): return "B", 3
    if pct >= _setting(conn, "grade_c"): return "C", 2
    if pct >= pass_mark: return "D", 1
    return "F", 0


def calc(conn, scores, assignments, year):
    """scores: {assessment: number}. Only parts that have a mark count, so totals are provisional until the final exam."""
    earned = avail = 0
    for a in assignments:
        if scores.get(a["id"]) is not None:
            earned += scores[a["id"]]
            avail += a["max_marks"]
    w_cw, w_mid, w_fin = _setting(conn, "weight_coursework"), _setting(conn, "weight_mid"), _setting(conn, "weight_final")
    num = den = 0
    if avail:
        num += earned / avail * 100 * w_cw
        den += w_cw
    if scores.get("mid") is not None:
        num += scores["mid"] * w_mid
        den += w_mid
    if scores.get("final") is not None:
        num += scores["final"] * w_fin
        den += w_fin
    if not den:
        return None
    pct = num / den
    pass_mark = conn.execute("SELECT pass_mark FROM pass_marks WHERE year=?", (year,)).fetchone()[0]
    letter, points = _band(pct, pass_mark, conn)
    return {"percent": round(pct, 2), "grade": letter, "points": points, "final": scores.get("final") is not None}


def results(conn, sid):
    year = conn.execute("SELECT year_of_study FROM students WHERE user_id=?", (sid,)).fetchone()[0]
    pass_mark = conn.execute("SELECT pass_mark FROM pass_marks WHERE year=?", (year,)).fetchone()[0]
    out, credits, wsum, pts, fails = [], 0, 0.0, 0, 0
    for code in enrolled_codes(conn, sid):
        c = conn.execute("SELECT * FROM courses WHERE code=?", (code,)).fetchone()
        asg = _rows(conn.execute("SELECT id,title,max_marks,due_date,kind FROM assignments WHERE course_code=? ORDER BY due_date,id", (code,)))
        published = conn.execute("SELECT published_at FROM course_publications WHERE course_code=?", (code,)).fetchone()
        scores = {r["assessment"]: r["published_score"] for r in conn.execute(
            "SELECT assessment,published_score FROM marks WHERE student_id=? AND course_code=? AND published_score IS NOT NULL", (sid, code))} if published else {}
        parts = [{"id": a["id"], "title": a["title"], "max": a["max_marks"], "kind": a["kind"], "score": scores.get(a["id"])} for a in asg]
        parts.append({"id": "mid", "title": "Mid-semester exam", "max": 100, "score": scores.get("mid")})
        parts.append({"id": "final", "title": "End-of-term exam", "max": 100, "score": scores.get("final"), "examAt": c["exam_at"], "venue": c["exam_venue"]})
        r = calc(conn, scores, asg, year)
        entry = {"code": code, "title": c["title"], "credits": c["credits"], "level": int(re.sub(r"\D", "", code)[0] + "00"),
                 "published": bool(published), "assessments": parts,
                 "percent": r["percent"] if r else None, "grade": r["grade"] if r else None,
                 "provisional": not (r and r["final"])}
        if r:
            credits += c["credits"]; wsum += r["percent"] * c["credits"]; pts += r["points"] * c["credits"]
            fails += r["grade"] == "F"
        out.append(entry)
    return {"year": year, "passMark": pass_mark, "courses": out,
            "summary": {"credits": credits, "average": round(wsum / credits, 2) if credits else None,
                        "gpa": round(pts / credits, 2) if credits else None, "failedCourses": fails}}


# =====================================================================  fees and payments
def fees(conn, sid):
    lines = _rows(conn.execute("SELECT description,amount FROM v_fee_lines WHERE student_id=?", (sid,)))
    bal = dict(conn.execute("SELECT charged,paid,balance FROM v_fee_balance WHERE student_id=?", (sid,)).fetchone())
    pays = _rows(conn.execute("SELECT id,amount,method,reference,status,paid_at AS paidAt FROM payments WHERE student_id=? ORDER BY id DESC", (sid,)))
    return {"lines": lines, "payments": pays, **bal}


def record_payment(conn, sid, amount, method, reference):
    try:
        amount = int(round(float(amount)))
    except (TypeError, ValueError):
        raise ApiError(400, "Enter an amount greater than zero.")
    if not 0 < amount <= 10_000_000:
        raise ApiError(400, "Enter an amount greater than zero.")
    if method not in PAY_METHODS:
        raise ApiError(400, "Choose a payment method.")
    conn.execute("INSERT INTO payments(student_id,amount,method,reference) VALUES(?,?,?,?)", (sid, amount, method, _text(reference, "reference", 100, False)))
    return fees(conn, sid)


# =====================================================================  accommodation
def accommodation(conn, sid):
    rooms = _rows(conn.execute("SELECT id,name,fee_per_term AS fee FROM room_types ORDER BY fee_per_term"))
    req = conn.execute("SELECT room_type_id AS room,status,requested_at AS requestedAt FROM accommodation_requests WHERE student_id=?", (sid,)).fetchone()
    return {"rooms": rooms, "request": dict(req) if req else None}


def request_room(conn, sid, room_id):
    if not conn.execute("SELECT 1 FROM room_types WHERE id=?", (str(room_id or ""),)).fetchone():
        raise ApiError(404, "That room type doesn\u2019t exist.")
    conn.execute("""INSERT INTO accommodation_requests(student_id,room_type_id,status) VALUES(?,?, 'requested')
                    ON CONFLICT(student_id) DO UPDATE SET room_type_id=excluded.room_type_id, status='requested', updated_at=?""",
                 (sid, room_id, p.now()))
    return accommodation(conn, sid)


def cancel_room(conn, sid):
    conn.execute("DELETE FROM accommodation_requests WHERE student_id=?", (sid,))
    return accommodation(conn, sid)


# =====================================================================  announcements (the bell)
def post_announcement(conn, title, body, posted_by=None, course=None):
    conn.execute("INSERT INTO announcements(title,body,course_code,posted_by) VALUES(?,?,?,?)", (title, body, course, posted_by))


def _visible_courses(conn, user):
    if user["role"] == "student":
        return enrolled_codes(conn, user["id"])
    return [r[0] for r in conn.execute("SELECT course_code FROM tutor_courses WHERE tutor_id=?", (user["id"],))]


def announcements(conn, user):
    codes = _visible_courses(conn, user)
    marks = ",".join("?" * len(codes))
    where = "a.course_code IS NULL" + (f" OR a.course_code IN ({marks})" if codes else "")
    rows = _rows(conn.execute(f"""SELECT a.id,a.title,a.body,a.course_code AS course,a.posted_at AS postedAt,
                                  (r.user_id IS NOT NULL) AS read FROM announcements a
                                  LEFT JOIN announcement_reads r ON r.announcement_id=a.id AND r.user_id=?
                                  WHERE {where} ORDER BY a.posted_at DESC, a.id DESC""", [user["id"], *codes]))
    for r in rows:
        r["read"] = bool(r["read"])
    return {"announcements": rows, "unread": sum(not r["read"] for r in rows)}


def mark_announcements_read(conn, user):
    for a in announcements(conn, user)["announcements"]:
        if not a["read"]:
            conn.execute("INSERT OR IGNORE INTO announcement_reads(user_id,announcement_id) VALUES(?,?)", (user["id"], a["id"]))
    return announcements(conn, user)


# =====================================================================  information pages and the dashboard
def content(conn, section):
    if section not in ("library", "chapel", "about", "help"):
        raise ApiError(404, "Page not found.")
    return _rows(conn.execute("SELECT title,body,contact_email AS email FROM site_content WHERE section=? ORDER BY position", (section,)))


def dashboard(conn, user):
    sid = user["id"]
    return {"enrolled": len(enrolled_codes(conn, sid)),
            "submitted": conn.execute("SELECT COUNT(*) FROM submissions WHERE student_id=?", (sid,)).fetchone()[0],
            "unread": announcements(conn, user)["unread"]}


# =====================================================================  tutor: courses and lecture notes
def _tutor_course(conn, tid, code):
    c = _course(conn, code)
    if not conn.execute("SELECT 1 FROM tutor_courses WHERE tutor_id=? AND course_code=?", (tid, c["code"])).fetchone():
        raise ApiError(403, "You don\u2019t teach this course.")
    return c


def tutor_courses(conn, tid):
    return _rows(conn.execute("""SELECT c.code,c.title,c.credits,c.description,
                                 (SELECT COUNT(*) FROM enrolments e WHERE e.course_code=c.code) AS students
                                 FROM tutor_courses t JOIN courses c ON c.code=t.course_code WHERE t.tutor_id=? ORDER BY c.code""", (tid,)))


def tutor_notes(conn, tid, code):
    c = _tutor_course(conn, tid, code)
    return {"notes": _rows(conn.execute("SELECT id,title,scripture_ref AS ref,body,created_at AS postedAt FROM lecture_notes WHERE course_code=? ORDER BY id", (c["code"],)))}


def tutor_save_note(conn, tid, code, note_id, title, ref, body):
    c = _tutor_course(conn, tid, code)
    title, ref, body = _text(title, "a title", 200), _text(ref, "reference", 100, False), _text(body, "note", 20000)
    if note_id:
        if not conn.execute("SELECT 1 FROM lecture_notes WHERE id=? AND course_code=?", (note_id, c["code"])).fetchone():
            raise ApiError(404, "Note not found.")
        conn.execute("UPDATE lecture_notes SET title=?,scripture_ref=?,body=?,updated_at=? WHERE id=?", (title, ref, body, p.now(), note_id))
    else:
        conn.execute("INSERT INTO lecture_notes(course_code,tutor_id,title,scripture_ref,body) VALUES(?,?,?,?,?)", (c["code"], tid, title, ref, body))
        post_announcement(conn, "New lecture note: " + title, c["title"] + ": your tutor has posted a new lecture note.", tid, c["code"])
    return tutor_notes(conn, tid, c["code"])


def tutor_delete_note(conn, tid, code, note_id):
    c = _tutor_course(conn, tid, code)
    conn.execute("DELETE FROM lecture_notes WHERE id=? AND course_code=?", (note_id, c["code"]))
    return tutor_notes(conn, tid, c["code"])


# =====================================================================  tutor: gradebook
def _assessments(conn, code):
    return _rows(conn.execute("SELECT id,title,max_marks,kind FROM assignments WHERE course_code=? ORDER BY due_date,id", (code,)))


def gradebook(conn, tid, code):
    c = _tutor_course(conn, tid, code)
    asg = _assessments(conn, c["code"])
    cols = [{"id": a["id"], "label": f"A{i}", "title": a["title"], "max": a["max_marks"], "kind": a["kind"]} for i, a in enumerate(asg, 1)]
    cols += [{"id": "mid", "label": "Mid-semester", "title": "Mid-semester exam", "max": 100}, {"id": "final", "label": "Final exam", "title": "End-of-term exam", "max": 100}]
    students = _rows(conn.execute("""SELECT u.id,u.full_name AS name,s.registration_number AS reg,s.year_of_study AS year FROM enrolments e
                                     JOIN students s ON s.user_id=e.student_id JOIN users u ON u.id=s.user_id
                                     WHERE e.course_code=? ORDER BY u.full_name""", (c["code"],)))
    marks, subs = {}, {}
    for r in conn.execute("SELECT student_id,assessment,score FROM marks WHERE course_code=? AND score IS NOT NULL", (c["code"],)):
        marks.setdefault(r["student_id"], {})[r["assessment"]] = r["score"]
    for r in conn.execute("SELECT s.id,s.student_id,s.assignment_id,s.comment,s.submitted_at FROM submissions s JOIN assignments a ON a.id=s.assignment_id WHERE a.course_code=?", (c["code"],)):
        subs.setdefault(r["student_id"], {})[r["assignment_id"]] = {"comment": r["comment"], "submittedAt": r["submitted_at"], "files": _files(conn, r["id"])}
    for s in students:
        s["scores"] = marks.get(s["id"], {})
        s["submissions"] = subs.get(s["id"], {})
        s["submitted"] = list(s["submissions"])
        r = calc(conn, s["scores"], asg, s["year"])
        s["percent"], s["grade"], s["provisional"] = (r["percent"], r["grade"], not r["final"]) if r else (None, None, True)
    pub = conn.execute("SELECT published_at FROM course_publications WHERE course_code=?", (c["code"],)).fetchone()
    return {"course": {"code": c["code"], "title": c["title"]}, "columns": cols, "students": students, "publishedAt": pub[0] if pub else None}


def set_mark(conn, tid, code, student_id, assessment, score):
    c = _tutor_course(conn, tid, code)
    valid = {a["id"]: a["max_marks"] for a in _assessments(conn, c["code"])}
    valid.update({"mid": 100, "final": 100})
    if assessment not in valid:
        raise ApiError(400, "Unknown assessment.")
    if not conn.execute("SELECT 1 FROM enrolments WHERE student_id=? AND course_code=?", (student_id, c["code"])).fetchone():
        raise ApiError(404, "That student isn\u2019t enrolled in this course.")
    if score is not None and score != "":
        try:
            score = float(score)
        except (TypeError, ValueError):
            raise ApiError(400, "A mark must be a number.")
        if not 0 <= score <= valid[assessment]:
            raise ApiError(400, f"A mark must be between 0 and {valid[assessment]}.")
    else:
        score = None
    conn.execute("""INSERT INTO marks(student_id,course_code,assessment,score,updated_by) VALUES(?,?,?,?,?)
                    ON CONFLICT(student_id,course_code,assessment) DO UPDATE SET score=excluded.score, updated_by=excluded.updated_by, updated_at=?""",
                 (student_id, c["code"], assessment, score, tid, p.now()))
    conn.execute("DELETE FROM marks WHERE course_code=? AND score IS NULL AND published_score IS NULL", (c["code"],))
    return {"saved": True}


def publish(conn, tid, code):
    c = _tutor_course(conn, tid, code)
    conn.execute("UPDATE marks SET published_score=score WHERE course_code=?", (c["code"],))
    conn.execute("DELETE FROM marks WHERE course_code=? AND score IS NULL AND published_score IS NULL", (c["code"],))
    conn.execute("""INSERT INTO course_publications(course_code,published_at,published_by) VALUES(?,?,?)
                    ON CONFLICT(course_code) DO UPDATE SET published_at=excluded.published_at, published_by=excluded.published_by""",
                 (c["code"], p.now(), tid))
    post_announcement(conn, "Marks published: " + c["title"], "Your tutor has published marks for " + c["title"] + ". Open the Result slip to see them.", tid, c["code"])
    return gradebook(conn, tid, c["code"])
