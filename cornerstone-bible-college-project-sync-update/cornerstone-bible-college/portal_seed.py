"""Starting data for the portal database.

The courses, timetable, exams, lecture notes and coursework come from portal_catalog.py.

seed_reference()  catalogue, rooms, grading rules, announcements and the information pages. Safe to run again and
                  again: it only fills in what is missing, and never re-adds notes a tutor has deleted.
seed_people()     the demo tutors and students (new databases only).
seed_demo()       demo enrolments, marks and one submission (new databases only).
Replace all of this with the college's real information.
"""
import portal_db as p
import portal_catalog as cat

ROOMS = [("shared", "Shared room (4 students)", 6000), ("double", "Double room", 9000),
         ("single", "Single room", 12000), ("family", "Family unit", 20000)]

SETTINGS = [("weight_coursework", "30"), ("weight_mid", "20"), ("weight_final", "50"),
            ("grade_a", "70"), ("grade_b", "60"), ("grade_c", "50")]
PASS_MARKS = [(1, 40), (2, 40), (3, 45), (4, 50)]

ANNOUNCEMENTS = [  # title, body, posted_at (oldest first so ids run in time order)
    ("Fee payment deadline", "Please clear your balance by 30 November. See the Fees and accounting tab.", "2026-10-15 08:00:00"),
    ("Chapel moves to the main hall", "This week\u2019s chapel services will be held in the main hall.", "2026-10-19 08:00:00"),
    ("Exam timetable published", "End-of-term exams begin on 7 December. Check the Exams tab for your dates and venues.", "2026-10-20 08:00:00"),
]

CONTENT = [  # section, position, title, body, contact email
    ("library", 1, "Bible study tools", "Concordances, commentaries, and Bible dictionaries available for loan.", None),
    ("library", 2, "Course readings", "Required and recommended readings for each course, listed by week.", None),
    ("library", 3, "Past exam papers", "Practice papers from previous years to help you prepare.", None),
    ("library", 4, "Opening hours", "Monday to Friday, 8:00\u201317:00. Saturday, 9:00\u201313:00.", None),
    ("chapel", 1, "Chapel", "Tuesday and Thursday, 8:00. All students are encouraged to attend.", None),
    ("chapel", 2, "Prayer meeting", "Friday, 17:00. Open to students and staff.", None),
    ("chapel", 3, "Fellowship groups", "Small groups meet weekly for Bible study and prayer. Ask the chaplain\u2019s office to join one.", None),
    ("about", 1, "Our mission", "We prepare men and women to know Scripture, live faithfully, and serve the church and their communities.", None),
    ("about", 2, "Statement of faith", "Replace this with your college\u2019s statement of faith.", None),
    ("about", 3, "Our history", "Replace this with a short history of the college.", None),
    ("help", 1, "Registrar", "Enrolment, results, and records.", "registrar@cornerstone.example"),
    ("help", 2, "Bursar", "Fees and payments.", "bursar@cornerstone.example"),
    ("help", 3, "Accommodation office", "Room requests and housing questions.", "housing@cornerstone.example"),
    ("help", 4, "IT support", "Help with your portal account.", "it@cornerstone.example"),
]

STUDENTS = [("Joy Wanjiru", "joy.wanjiru", "30110001", "CBC/2026/0101", 1), ("Peter Otieno", "peter.otieno", "30110002", "CBC/2026/0102", 1),
            ("Faith Achieng", "faith.achieng", "30110003", "CBC/2026/0103", 2), ("Daniel Mutua", "daniel.mutua", "30110004", "CBC/2026/0104", 1),
            ("Grace Chebet", "grace.chebet", "30110005", "CBC/2026/0105", 3), ("Samuel Kamau", "samuel.kamau", "30110006", "CBC/2026/0106", 1)]

ORIGINAL_COURSES = ["OT101", "NT110", "TH201", "MN150"]
_OLD_CLASS_TIME = {"MN150": "Fri, 9:00\u201312:00"}      # wording used by the first version of the database


def _once(conn, key):
    """True the first time it is called for this key, so a one-time seed never repeats."""
    return conn.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?, '1')", ("seeded:" + key,)).rowcount == 1


def seed_reference(conn):
    for code, title, credits, desc, fee, sessions, room, exam, venue in cat.COURSES:
        when = cat.when_text(sessions)
        conn.execute("INSERT OR IGNORE INTO courses(code,title,credits) VALUES(?,?,?)", (code, title, credits))
        conn.execute("""UPDATE courses SET description=?, tuition_fee=?, class_time=?, room=?, exam_at=?, exam_venue=?
                        WHERE code=? AND description=''""", (desc, fee, when, room, exam, venue, code))
        if code in _OLD_CLASS_TIME:
            conn.execute("UPDATE courses SET class_time=? WHERE code=? AND class_time=?", (when, code, _OLD_CLASS_TIME[code]))
        for day, band in sessions:
            conn.execute("INSERT OR IGNORE INTO class_sessions(course_code,day,band,start_time,end_time) VALUES(?,?,?,?,?)",
                         (code, day, band, cat.BANDS[band][0], cat.BANDS[band][1]))
    for cid, code, title, desc, due, pts, kind in cat.COURSEWORK:
        conn.execute("INSERT OR IGNORE INTO assignments(id,course_code,title,description,due_date,max_marks,kind) VALUES(?,?,?,?,?,?,?)",
                     (cid, code, title, desc, due, pts, kind))
        conn.execute("UPDATE assignments SET kind=? WHERE id=? AND kind='assignment'", (kind, cid))
    for email, _, _, codes in cat.TUTORS:                # give tutors who already exist their courses
        row = conn.execute("SELECT id FROM users WHERE email=? AND role='tutor'", (email,)).fetchone()
        if row:
            for code in codes:
                conn.execute("INSERT OR IGNORE INTO tutor_courses(tutor_id,course_code) VALUES(?,?)", (row[0], code))
    conn.executemany("INSERT OR IGNORE INTO room_types(id,name,fee_per_term) VALUES(?,?,?)", ROOMS)
    conn.executemany("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", SETTINGS)
    conn.executemany("INSERT OR IGNORE INTO pass_marks(year,pass_mark) VALUES(?,?)", PASS_MARKS)
    conn.executemany("INSERT OR IGNORE INTO site_content(section,position,title,body,contact_email) VALUES(?,?,?,?,?)", CONTENT)
    if _once(conn, "announcements") and conn.execute("SELECT COUNT(*) FROM announcements").fetchone()[0] == 0:
        conn.executemany("INSERT INTO announcements(title,body,posted_at) VALUES(?,?,?)", ANNOUNCEMENTS)
    for code, *_ in cat.COURSES:                         # lecture notes: once per course, and only if it has a tutor and no notes
        tutor = conn.execute("SELECT tutor_id FROM tutor_courses WHERE course_code=? LIMIT 1", (code,)).fetchone()
        if not tutor:
            continue
        if _once(conn, "lecture_notes:" + code) and not conn.execute("SELECT COUNT(*) FROM lecture_notes WHERE course_code=?", (code,)).fetchone()[0]:
            for c2, t2, r2, b2 in [n for n in cat.LECTURE_NOTES if n[0] == code]:
                conn.execute("INSERT INTO lecture_notes(course_code,tutor_id,title,scripture_ref,body) VALUES(?,?,?,?,?)", (c2, tutor[0], t2, r2, b2))
    conn.commit()


def seed_people(conn):
    conn.execute("INSERT INTO users(role,email,password_hash,full_name) VALUES('admin','admin@cornerstone.example',?,'College Administrator')", (p.hash_pw("admin1234"),))
    for email, name, staff, codes in cat.TUTORS:
        cur = conn.execute("INSERT INTO users(role,email,password_hash,full_name) VALUES('tutor',?,?,?)", (email, p.hash_pw("tutor1234"), name))
        conn.execute("INSERT INTO tutors VALUES(?,?)", (cur.lastrowid, staff))
        for code in codes:
            conn.execute("INSERT INTO tutor_courses VALUES(?,?)", (cur.lastrowid, code))
    conn.commit()
    for n, e, i, r, y in STUDENTS:
        ok, msg = p.register_student(conn, n, e + "@students.cornerstone.example", i, r, y, "student1234")
        assert ok, msg


def seed_demo(conn):
    """Demo enrolments and published marks for the six sample students, plus one submitted assignment."""
    ids = [r[0] for r in conn.execute("SELECT id FROM users WHERE role='student' ORDER BY id")]
    tutor_of = {r[0]: r[1] for r in conn.execute("SELECT course_code, tutor_id FROM tutor_courses")}
    newer = [c[0] for c in cat.COURSES if c[0] not in ORIGINAL_COURSES]
    work = {}
    for cid, code, title, desc, due, pts, kind in cat.COURSEWORK:
        work.setdefault(code, []).append((cid, pts))
    offsets = [0, -6, 4, -12, 8, -3]                      # percentage-point variation between students
    def vary(base, top, off):
        return max(0.0, min(float(top), round(base * (1 + off / 100) * 2) / 2))
    for n, (sid, off) in enumerate(zip(ids, offsets)):
        mine = list(ORIGINAL_COURSES)
        if n:                                             # everyone but Joy also takes two of the newer units
            mine += [newer[(n * 3) % 8], newer[(n * 3 + 1) % 8]]
        for code in mine:
            conn.execute("INSERT OR IGNORE INTO enrolments(student_id,course_code) VALUES(?,?)", (sid, code))
            mid = vary(cat.sample_mid(code), 100, off)
            conn.execute("INSERT OR IGNORE INTO marks(student_id,course_code,assessment,score,published_score,updated_by) VALUES(?,?,?,?,?,?)",
                         (sid, code, "mid", mid, mid, tutor_of[code]))
            for cid, pts in work[code]:
                v = vary(cat.sample_mark(cid, pts), pts, off)
                conn.execute("INSERT OR IGNORE INTO marks(student_id,course_code,assessment,score,published_score,updated_by) VALUES(?,?,?,?,?,?)",
                             (sid, code, cid, v, v, tutor_of[code]))
    for code, *_ in cat.COURSES:
        conn.execute("INSERT OR IGNORE INTO course_publications(course_code,published_at,published_by) VALUES(?,?,?)",
                     (code, p.now(), tutor_of[code]))
    # something for the bursar and the accommodation office to act on
    conn.execute("INSERT INTO payments(student_id,amount,method,reference,status) VALUES(?,?,?,?,?)", (ids[1], 6000, "Mobile money", "QK2X91", "recorded"))
    conn.execute("INSERT INTO payments(student_id,amount,method,reference,status) VALUES(?,?,?,?,?)", (ids[2], 20000, "Bank transfer", "TRF-4471", "confirmed"))
    conn.execute("INSERT INTO accommodation_requests(student_id,room_type_id,status) VALUES(?,?,?)", (ids[2], "double", "requested"))
    cur = conn.execute("INSERT INTO submissions(assignment_id,student_id,comment) VALUES('ot1',?,'Here is my comparison.')", (ids[0],))
    conn.execute("INSERT INTO submission_files(submission_id,file_name,size_bytes) VALUES(?,?,?)", (cur.lastrowid, "covenants.docx", 45312))
    conn.commit()
