# Login database for the Bible College portal

This is the database design and a working local copy for the **student** and **tutor** logins.

## Files
- `portal.db`: a ready-made SQLite database with demo data. Open it with the free **DB Browser for SQLite** (sqlitebrowser.org) or any SQLite tool.
- `schema.sql`: the table definitions (SQLite).
- `portal_db.py`: helper code (Python, nothing to install) that creates the database, registers students, checks logins, locks accounts after too many wrong passwords, and records every attempt.
- `schema_postgres.sql`: the same design for Postgres/Supabase (not tested).

## Tables
| Table | What it holds |
|---|---|
| `users` | Everyone who can log in: role (student/tutor/admin), email, hashed password, status, failed attempts, lock time, last login |
| `students` | ID number, registration number, year of study (students can log in with email, ID number or registration number) |
| `tutors` | Staff number (tutors log in with email) |
| `courses`, `tutor_courses` | The four courses, and which tutor teaches which |
| `login_events` | **The login record:** every attempt in either portal: who, which portal, how they logged in, success or failure, the reason, IP address, time |
| `sessions` | Active logins, with an expiry time (12 hours here). Only a hash of the token is stored |
| `v_login_history` | A ready-made report joining names to login events |

Passwords are never stored in plain text. They are salted and hashed (PBKDF2, 200,000 rounds). After 5 wrong passwords an account is locked for 15 minutes; both limits are settings at the top of `portal_db.py`.

## Demo data
- Tutors: the four tutors from the prototype, password `tutor1234`.
- Students: six sample students (for example `joy.wanjiru@students.cornerstone.example`, ID `30110001`, registration `CBC/2026/0101`), password `student1234`.
- `login_events` has seven demo attempts, including failed ones, marked with the user agent `demo-seed`.
- Delete the demo accounts and change these passwords before real use.

## Try it
```
python3 portal_db.py          # rebuilds portal.db and prints the login history
```
```python
import portal_db as p
c = p.connect()
p.register_student(c, "Ann Wambui", "ann@students.cornerstone.example", "30119999", "CBC/2026/0200", 1, "a-long-password")
ok, message, token = p.login(c, "student", "registration_number", "CBC/2026/0200", "a-long-password")
```

## Useful questions to ask the database
```sql
-- Recent logins and failures
SELECT * FROM v_login_history LIMIT 50;

-- Failed attempts in the last 24 hours
SELECT * FROM v_login_history WHERE success = 0 AND created_at > datetime('now','-1 day');

-- Last login for each person
SELECT full_name, role, last_login_at FROM users ORDER BY last_login_at DESC;

-- Currently locked accounts
SELECT full_name, locked_until FROM users WHERE locked_until > datetime('now');

-- Logins per portal and method
SELECT portal, method, COUNT(*) FROM login_events WHERE success = 1 GROUP BY portal, method;
```

## Important
- **The prototype page is not connected to this database yet.** It still keeps accounts in each browser. A web page can't safely talk to a database directly: you need a small server (or a service like Supabase) between them that runs the checks in `portal_db.py` and sends the page back a session.
- Never put database passwords or keys inside the HTML page.
- For a real launch, use HTTPS, and consider a service such as Supabase or Firebase for sign-in, since they handle password resets and email verification for you.
- Login records contain personal data (names, IP addresses). Decide how long to keep them and who may read them, and follow the data protection rules that apply to your college.
