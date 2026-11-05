# Portal database, version 2

Version 1 only stored logins. Version 2 stores everything the other pages need: courses, enrolments, notes,
assignments, marks, fees, rooms, announcements and the information pages. It is the same `portal.db` file.

**Important:** the app's screens are not connected to the new tables yet. The pages still save their data on each
phone, exactly as before, so nothing you have working has changed. The database and the web API for every page are
built and tested. The next step is to switch each screen over to them.

## Which page uses which tables
| Page | Tables | API (all need a login) |
|---|---|---|
| Profile | `users`, `students`, `tutors`, `login_events` | `GET /api/me`, `GET /api/dashboard` |
| Enrol in a course / My courses | `courses`, `enrolments` | `GET /api/courses`, `GET /api/enrolments`, `POST /api/enrolments/enrol`, `/drop` |
| Course page: lecture notes | `lecture_notes` | `GET /api/course/<code>` |
| Course page: my notes | `student_notes` | *Removed from the screens.* The table and API are kept so no data is lost. |
| Course page: coursework (assignments, essays, reading responses, quizzes, projects, practicals) | `assignments` (with a `kind`), `submissions`, `submission_files` | `GET /api/course/<code>`, `POST /api/submissions` |
| Timetable (the day-by-period grid) and Exams | `class_sessions`, `courses` (class time, room, exam date, venue) | `GET /api/schedule` |
| Result slip | `marks`, `course_publications`, `pass_marks`, `settings` | `GET /api/results` |
| Fees and accounting | `courses` (fee), `room_types`, `payments`, views `v_fee_lines`, `v_fee_balance` | `GET /api/fees`, `POST /api/payments` |
| Accommodation | `room_types`, `accommodation_requests` | `GET/POST /api/accommodation`, `POST /api/accommodation/cancel` |
| Announcements and the bell | `announcements`, `announcement_reads` | `GET /api/announcements`, `POST /api/announcements/read` |
| Library, Chapel, About, Help | `site_content` | `GET /api/content/<library|chapel|about|help>` |
| Tutor: lecture notes | `lecture_notes` | `GET/POST /api/tutor/notes`, `POST /api/tutor/notes/delete` |
| Tutor: gradebook | `marks`, `course_publications` | `GET /api/tutor/gradebook?course=`, `POST /api/tutor/marks`, `/publish` |

## The course catalogue (12 units)
All courses, their weekly class times, exam dates, lecture notes and coursework are defined in **`portal_catalog.py`**.
The database is seeded from it. Four units are Year 1 core units from the first version (OT101, NT110, TH201, MN150) and
eight were added: HM120 Hermeneutics, GK105 Biblical Greek I, CH101 Church History I, PR130 Preaching and Homiletics,
CN140 Pastoral Counselling, NT210 Pauline Epistles, ET230 Christian Ethics and MS220 Mission and Evangelism.
Each tutor teaches three units. Every unit has four coursework items, including one held in class.
Coursework kinds: `assignment`, `essay`, `reading`, `quiz` and `practical` (the last two are held in class, so
students upload nothing for them and the tutor enters the mark), and `project`.
Note: the web page currently carries its own copy of this catalogue, generated from the same file, until its screens are
connected to the API. If you change `portal_catalog.py`, the page's copy does not change yet.

## Rules the server enforces
- A student sees and changes only their own notes, submissions, payments, room request and results.
- A student must be enrolled in a course to open it, write notes in it, or submit its assignments.
- A tutor can only open, edit and mark the courses they teach, and only for students enrolled in them.
- A tutor can't use student pages, and a student can't use tutor pages.
- Marks must be numbers between 0 and the maximum. A mark can be cleared by sending an empty value.
- **Draft and published marks are separate.** A tutor's edits go to `marks.score`. Students only ever see
  `marks.published_score`, which is copied from the draft when the tutor presses Publish.
- Publishing, and posting a new lecture note, create an announcement for that course's students only.
- Quizzes and practicals are held in class: uploading to one is refused.
- Resubmitting an assignment replaces the earlier submission. Files are limited to 10 files of 10 MB each.
- Payments must be a whole amount above zero by an allowed method. They are recorded, not verified.

## How the grade is worked out
Coursework counts 30%, the mid-semester exam 20% and the end-of-term exam 50% (`settings` table). Only parts that
have a mark are counted, so a score stays provisional until the final exam is entered. Grades: A 70+, B 60+, C 50+,
D from the pass mark up to the C line, F below the pass mark. The pass mark depends on year of study (`pass_marks`:
Years 1 and 2: 40, Year 3: 45, Year 4: 50). Change any of these in the tables, not in code.

## Upgrading an existing database
You don't have to do anything. **Starting the server upgrades an older `portal.db` automatically**, after saving a
backup called `portal.db.backup-<date>-<time>`. Accounts, passwords and login records are kept. A database that is
already up to date is left alone.

To do it by hand: `python3 upgrade_database.py`. It is safe to run more than once.

An upgraded database gets the full course catalogue and timetable, coursework (with its kinds), lecture notes, rooms, grading
rules, announcements and information pages, but **no invented students or marks**. Only a brand-new database (made when `portal.db` is
missing) also gets the demo enrolments and marks for the six sample students.

Lecture notes and announcements are added **once**. If a tutor deletes a note, upgrading never brings it back.

To start again from scratch, delete `portal.db` and start the server.

## Useful questions to ask the database
Open `portal.db` with DB Browser for SQLite (sqlitebrowser.org) and run:
```sql
SELECT * FROM v_enrolment_counts;                         -- students per course
SELECT * FROM v_fee_balance WHERE balance > 0;            -- who owes fees
SELECT * FROM v_published_marks WHERE course_code='OT101';
SELECT a.title, COUNT(s.id) AS submitted FROM assignments a
  LEFT JOIN submissions s ON s.assignment_id = a.id GROUP BY a.id;     -- submissions per assignment
SELECT u.full_name, p.amount, p.method, p.paid_at FROM payments p
  JOIN users u ON u.id = p.student_id ORDER BY p.id DESC;              -- recent payments
SELECT * FROM v_login_history LIMIT 50;                                -- login record
```

## Not done yet
- **The screens still use on-device storage.** Connecting each page to its API is the next job.
- **Submitted files aren't stored.** Only file names and sizes are saved. The `stored_path` column is ready for real uploads.
- **Payments are not checked** with a bank or mobile money provider, and there is no bursar screen to confirm them.
- **No admin tools** yet: course setup, room approval, creating tutors and students, announcements by staff.
- `schema_postgres.sql` still covers only the version 1 login tables, and was never tested.
- Back up `portal.db` regularly. It holds personal data, so decide who may read it and for how long you keep it.
