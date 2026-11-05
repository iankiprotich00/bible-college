-- Cornerstone Bible College: portal database, design version 3 (SQLite)
-- Safe to run on a new or an existing database: every table uses IF NOT EXISTS.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_version (
  version    INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL DEFAULT (datetime('now')),
  note       TEXT
);

-- =====================================================================
-- PART 1: PEOPLE AND LOGINS (unchanged from version 1)
-- =====================================================================
CREATE TABLE IF NOT EXISTS users (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  role            TEXT NOT NULL CHECK (role IN ('student','tutor','admin')),
  email           TEXT NOT NULL UNIQUE COLLATE NOCASE,
  password_hash   TEXT NOT NULL,
  full_name       TEXT NOT NULL,
  status          TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended','pending')),
  must_change_password INTEGER NOT NULL DEFAULT 0,   -- 1 after an admin creates or resets the account
  failed_attempts INTEGER NOT NULL DEFAULT 0,
  locked_until    TEXT,
  last_login_at   TEXT,
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS students (
  user_id             INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  id_number           TEXT NOT NULL UNIQUE,
  registration_number TEXT NOT NULL UNIQUE COLLATE NOCASE,
  year_of_study       INTEGER NOT NULL DEFAULT 1 CHECK (year_of_study BETWEEN 1 AND 4)
);

CREATE TABLE IF NOT EXISTS tutors (
  user_id      INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  staff_number TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS login_events (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
  portal     TEXT NOT NULL CHECK (portal IN ('student','tutor')),
  method     TEXT NOT NULL CHECK (method IN ('email','id_number','registration_number')),
  identifier TEXT NOT NULL,
  success    INTEGER NOT NULL CHECK (success IN (0,1)),
  reason     TEXT,
  ip_address TEXT,
  user_agent TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_login_events_user ON login_events (user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_login_events_time ON login_events (created_at);

CREATE TABLE IF NOT EXISTS sessions (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  portal     TEXT NOT NULL CHECK (portal IN ('student','tutor')),
  token_hash TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at TEXT NOT NULL,
  revoked    INTEGER NOT NULL DEFAULT 0
);

-- =====================================================================
-- PART 2: COURSES, ENROLMENT, TIMETABLE AND EXAMS
-- The Timetable page reads class_time and room. The Exams page reads exam_at and exam_venue.
-- =====================================================================
CREATE TABLE IF NOT EXISTS courses (
  code        TEXT PRIMARY KEY,
  title       TEXT NOT NULL,
  credits     INTEGER NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  tuition_fee INTEGER NOT NULL DEFAULT 0,
  class_time  TEXT NOT NULL DEFAULT '',
  room        TEXT NOT NULL DEFAULT '',
  exam_at     TEXT,                              -- 'YYYY-MM-DD HH:MM' (local time)
  exam_venue  TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS class_sessions (       -- the Timetable grid: one row per weekly class
  course_code TEXT    NOT NULL REFERENCES courses(code) ON DELETE CASCADE,
  day         INTEGER NOT NULL CHECK (day BETWEEN 0 AND 4),     -- 0 = Monday ... 4 = Friday
  band        INTEGER NOT NULL CHECK (band BETWEEN 0 AND 3),    -- the day's four class periods, from 0
  start_time  TEXT    NOT NULL,
  end_time    TEXT    NOT NULL,
  PRIMARY KEY (course_code, day, band)
);

CREATE TABLE IF NOT EXISTS tutor_courses (
  tutor_id    INTEGER NOT NULL REFERENCES tutors(user_id) ON DELETE CASCADE,
  course_code TEXT    NOT NULL REFERENCES courses(code),
  PRIMARY KEY (tutor_id, course_code)
);

CREATE TABLE IF NOT EXISTS enrolments (
  student_id  INTEGER NOT NULL REFERENCES students(user_id) ON DELETE CASCADE,
  course_code TEXT    NOT NULL REFERENCES courses(code),
  enrolled_at TEXT    NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (student_id, course_code)
);
CREATE INDEX IF NOT EXISTS idx_enrolments_course ON enrolments (course_code);

-- =====================================================================
-- PART 3: COURSE PAGE: lecture notes and coursework (assignments, essays, quizzes, projects)
-- (student_notes is no longer used by the app screens. It is kept so no data is lost.)
-- =====================================================================
CREATE TABLE IF NOT EXISTS lecture_notes (        -- written by tutors, read by enrolled students
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  course_code   TEXT NOT NULL REFERENCES courses(code),
  tutor_id      INTEGER REFERENCES tutors(user_id) ON DELETE SET NULL,
  title         TEXT NOT NULL,
  scripture_ref TEXT NOT NULL DEFAULT '',
  body          TEXT NOT NULL,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_lecture_notes_course ON lecture_notes (course_code, id);

CREATE TABLE IF NOT EXISTS student_notes (        -- private to each student
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id    INTEGER NOT NULL REFERENCES students(user_id) ON DELETE CASCADE,
  course_code   TEXT NOT NULL REFERENCES courses(code),
  title         TEXT NOT NULL,
  scripture_ref TEXT NOT NULL DEFAULT '',
  body          TEXT NOT NULL,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_student_notes_owner ON student_notes (student_id, course_code);

CREATE TABLE IF NOT EXISTS assignments (
  id          TEXT PRIMARY KEY,                     -- e.g. 'ot1'
  course_code TEXT NOT NULL REFERENCES courses(code),
  title       TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  due_date    TEXT NOT NULL,                        -- 'YYYY-MM-DD'
  max_marks   INTEGER NOT NULL CHECK (max_marks > 0),
  kind        TEXT NOT NULL DEFAULT 'assignment'   -- assignment, essay, reading, quiz, project or practical
);
CREATE INDEX IF NOT EXISTS idx_assignments_course ON assignments (course_code, due_date);

CREATE TABLE IF NOT EXISTS submissions (          -- one per student per assignment
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  assignment_id TEXT NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
  student_id    INTEGER NOT NULL REFERENCES students(user_id) ON DELETE CASCADE,
  comment       TEXT NOT NULL DEFAULT '',
  submitted_at  TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (assignment_id, student_id)
);

CREATE TABLE IF NOT EXISTS submission_files (     -- file names and sizes now; stored_path is for real uploads later
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  submission_id INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
  file_name     TEXT NOT NULL,
  size_bytes    INTEGER NOT NULL DEFAULT 0 CHECK (size_bytes >= 0),
  stored_path   TEXT
);

-- =====================================================================
-- PART 4: MARKS, GRADING AND THE RESULT SLIP
-- A mark's 'assessment' is an assignment id, 'mid' (mid-semester exam) or 'final' (end-of-term exam).
-- Tutors edit 'score'. Publishing copies it to 'published_score', which is all students ever see.
-- =====================================================================
CREATE TABLE IF NOT EXISTS marks (
  student_id      INTEGER NOT NULL REFERENCES students(user_id) ON DELETE CASCADE,
  course_code     TEXT NOT NULL REFERENCES courses(code),
  assessment      TEXT NOT NULL,
  score           REAL,
  published_score REAL,
  updated_by      INTEGER REFERENCES users(id) ON DELETE SET NULL,
  updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (student_id, course_code, assessment)
);

CREATE TABLE IF NOT EXISTS course_publications (  -- when a tutor last published a course's marks
  course_code  TEXT PRIMARY KEY REFERENCES courses(code),
  published_at TEXT NOT NULL,
  published_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS pass_marks (           -- pass mark rises with year of study
  year      INTEGER PRIMARY KEY CHECK (year BETWEEN 1 AND 4),
  pass_mark INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (             -- grading weights and grade bands
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- =====================================================================
-- PART 5: FEES AND ACCOMMODATION
-- Tuition comes from courses.tuition_fee for each enrolled course; room charges from room_types.
-- =====================================================================
CREATE TABLE IF NOT EXISTS payments (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL REFERENCES students(user_id) ON DELETE CASCADE,
  amount     INTEGER NOT NULL CHECK (amount > 0),
  method     TEXT NOT NULL,
  reference  TEXT NOT NULL DEFAULT '',
  status     TEXT NOT NULL DEFAULT 'recorded' CHECK (status IN ('recorded','confirmed','rejected')),
  paid_at    TEXT NOT NULL DEFAULT (datetime('now')),
  reviewed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,   -- the bursar who confirmed or rejected it
  reviewed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_payments_student ON payments (student_id, paid_at);

CREATE TABLE IF NOT EXISTS room_types (
  id           TEXT PRIMARY KEY,
  name         TEXT NOT NULL,
  fee_per_term INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS accommodation_requests (   -- one request per student at a time
  student_id   INTEGER PRIMARY KEY REFERENCES students(user_id) ON DELETE CASCADE,
  room_type_id TEXT NOT NULL REFERENCES room_types(id),
  status       TEXT NOT NULL DEFAULT 'requested' CHECK (status IN ('requested','approved','declined')),
  requested_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =====================================================================
-- PART 6: ANNOUNCEMENTS (the notification bell)
-- course_code NULL = for everyone. A course code = only that course's students and tutors.
-- =====================================================================
CREATE TABLE IF NOT EXISTS announcements (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  title       TEXT NOT NULL,
  body        TEXT NOT NULL,
  course_code TEXT REFERENCES courses(code),
  posted_by   INTEGER REFERENCES users(id) ON DELETE SET NULL,
  posted_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_announcements_time ON announcements (posted_at);

CREATE TABLE IF NOT EXISTS announcement_reads (
  user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  announcement_id INTEGER NOT NULL REFERENCES announcements(id) ON DELETE CASCADE,
  read_at         TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (user_id, announcement_id)
);

-- =====================================================================
-- PART 7: INFORMATION PAGES: Library, Chapel, About, Help and contact
-- =====================================================================
CREATE TABLE IF NOT EXISTS site_content (
  section       TEXT NOT NULL CHECK (section IN ('library','chapel','about','help')),
  position      INTEGER NOT NULL,
  title         TEXT NOT NULL,
  body          TEXT NOT NULL DEFAULT '',
  contact_email TEXT,
  PRIMARY KEY (section, position)
);

-- =====================================================================
-- VIEWS (read-only reports)
-- =====================================================================
DROP VIEW IF EXISTS v_login_history;
CREATE VIEW v_login_history AS
SELECT e.created_at, e.portal, COALESCE(u.full_name,'(unknown)') AS person,
       e.method, e.identifier, e.success, e.reason
FROM login_events e LEFT JOIN users u ON u.id = e.user_id
ORDER BY e.created_at DESC, e.id DESC;

DROP VIEW IF EXISTS v_fee_lines;
CREATE VIEW v_fee_lines AS
SELECT e.student_id, c.title || ' (tuition)' AS description, c.tuition_fee AS amount
FROM enrolments e JOIN courses c ON c.code = e.course_code
UNION ALL
SELECT a.student_id, 'Accommodation: ' || r.name || ' (' || a.status || ')', r.fee_per_term
FROM accommodation_requests a JOIN room_types r ON r.id = a.room_type_id
WHERE a.status IN ('requested','approved');

DROP VIEW IF EXISTS v_fee_balance;
CREATE VIEW v_fee_balance AS
SELECT student_id, charged, paid, charged - paid AS balance FROM (
  SELECT s.user_id AS student_id,
         COALESCE((SELECT SUM(amount) FROM v_fee_lines f WHERE f.student_id = s.user_id), 0) AS charged,
         COALESCE((SELECT SUM(amount) FROM payments p WHERE p.student_id = s.user_id AND p.status <> 'rejected'), 0) AS paid
  FROM students s);

DROP VIEW IF EXISTS v_published_marks;
CREATE VIEW v_published_marks AS
SELECT u.full_name AS student, s.registration_number, m.course_code, m.assessment, m.published_score
FROM marks m JOIN students s ON s.user_id = m.student_id JOIN users u ON u.id = m.student_id
WHERE m.published_score IS NOT NULL
ORDER BY m.course_code, u.full_name, m.assessment;

DROP VIEW IF EXISTS v_enrolment_counts;
CREATE VIEW v_enrolment_counts AS
SELECT c.code, c.title, COUNT(e.student_id) AS students
FROM courses c LEFT JOIN enrolments e ON e.course_code = c.code GROUP BY c.code ORDER BY c.code;
