# Bible College portal with the login database connected

This edition runs the portal from a small Python server that checks every login against `portal.db`
and records each attempt (success or failure) in the `login_events` table.

## What you need
Python 3.8 or newer (check with `python3 --version`; on Windows try `py --version`). Nothing else to install.

## Run it
1. Extract the zip.
2. Open a terminal in the extracted folder.
3. Run `python3 server.py` (on Windows: `py server.py`).
4. Open http://localhost:8000 in your browser.

Stop the server with Ctrl+C.

## What now uses the database
- Student sign-up, with the same checks as before: unique email, ID number and registration number
- Student login by email, ID number or registration number
- Tutor login
- Session handling: logging in creates a session that lasts 12 hours and survives a page reload; logging out ends it
- Lockout after 5 wrong passwords (15 minutes)
- A record of every attempt in `login_events`
- Year of study changes on the result slip
- "Previous login" on the student's profile page

## The wider database (version 2)
The database now also holds courses, notes, assignments, marks, fees, rooms and announcements, with a tested web API for each page.
The screens aren't connected to it yet. See `README_DATABASE_V2.md`.

## What still lives in the browser
Only logging in uses the database. Enrolments, notes, assignments, fees, room requests, tutor notes, the gradebook and
published marks are still saved in the browser, as in the prototype, so they are not shared between devices. The next
step is to move them into the database too.

## Demo accounts (change or remove before real use)
- Tutors: amani@, ruth@, samuel@ or grace@cornerstone.example, password `tutor1234`
- Students: for example joy.wanjiru@students.cornerstone.example (ID `30110001`, registration `CBC/2026/0101`), password `student1234`
- New students can sign up from the page, and they are saved to the database

## Reading the login records
Open `portal.db` with DB Browser for SQLite (sqlitebrowser.org) and run, for example:
```sql
SELECT * FROM v_login_history LIMIT 50;
SELECT * FROM v_login_history WHERE success = 0;
```
More queries are in the earlier database README.

## Using it on your phone
Run `python3 server.py --host 0.0.0.0`. It prints an address like http://192.168.1.20:8000. Open that on a phone connected
to the same Wi-Fi. Logins from the phone and the laptop then go to the same database.
Note: that address is plain http, so Chrome won't offer "Install app" there. Installing needs https (hosting).

## Test app for Android
The `android-app` folder is an Android Studio project that wraps this portal as an installable app, and the server has a
`/download` page for installing it from your Wi-Fi. See `README_ANDROID.md` (you build the `.apk` once, then drop it in `downloads`).

## Before real students use it
- This server is for testing on your own network. Don't expose it to the internet as it is.
- Put it behind https on a proper host, or move to a service such as Supabase (`schema_postgres.sql` is the starting design).
- Back up `portal.db`. It contains personal data (names, IDs, IP addresses), so decide who can read it and for how long you keep it.
- If you open `bible-college-portal.html` straight from a folder (no server), the page falls back to the old browser-only accounts.
