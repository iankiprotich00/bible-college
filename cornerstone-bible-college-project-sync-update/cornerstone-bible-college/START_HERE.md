# Cornerstone Bible College portal: project folder

Everything built so far is in this one folder.

## What is here
| Path | What it is |
|---|---|
| `server.py` | The portal server. It serves the web portal and checks every login against the database. |
| `portal_db.py` | Database code: accounts, password hashing, lockout, sessions, the login record, and upgrading. |
| `portal_data.py`, `portal_api.py` | The rules and web API for every page: courses, notes, assignments, marks, fees, rooms, announcements. |
| `portal_catalog.py` | **The 12 courses**: weekly timetable, exam dates, lecture notes and coursework. Edit this to change the catalogue. |
| `portal_seed.py` | The rooms, grading rules, announcements, information pages and demo people. Replace with the college's real information. |
| `upgrade_database.py` | Upgrades an older `portal.db` and keeps its accounts (the server also does this by itself). |
| `portal.db` | The SQLite database, with demo accounts, course content and sample marks. |
| `schema.sql`, `schema_postgres.sql` | The database design: version 2 for SQLite (every page), and an old, untested Postgres version of the login tables only. |
| `README_DATABASE_V2.md` | Which page uses which table, the rules, the grading, and how to upgrade. **Read this for the new database.** |
| `web/` | The portal web page (`index.html`) and its install files. This is the UI the app shows. |
| `android-app/` | Android Studio project that turns the portal into an installable Android app. |
| `downloads/` | Put the built `cornerstone-test.apk` here. The server offers it at `/download`. |
| `run_server.sh`, `run_server.bat` | Double-click launchers for the server (Mac/Linux, Windows). |
| `README_SERVER.md` | How to run the server and what uses the database. |
| `README_ANDROID.md` | How to build the test APK and install it. |
| `extras/` | Older and alternative versions: the single-file browser-only prototype (`bible-college-portal.html`), the installable web-app files (`static-pwa/`), and earlier guides (`docs/`). |

## Quick start
1. Try it in a browser: install Python 3.8+, then run `python3 server.py` (Windows: `py server.py`) and open http://localhost:8000.
2. Build the test app: follow `README_ANDROID.md` (Android Studio, about 15 minutes).
3. Install on a phone: run `run_server.sh` or `run_server.bat`, then open the `/download` address it prints on the phone.

## Demo logins (change or delete before real use)
- Administrator: admin@cornerstone.example, password `admin1234` (sign in on the staff page, the "Tutor login" link)
- Tutors: amani@, ruth@, samuel@ or grace@cornerstone.example, password `tutor1234`
- Students: for example joy.wanjiru@students.cornerstone.example (ID `30110001`, registration `CBC/2026/0101`), password `student1234`
- New students can sign up from the page. Administrators can also create students and tutors.

## What this update changed
Read `CHANGES_SYNC_UPDATE.md`. In short: every screen now reads and writes the database, assignment files are really stored,
and there is an administrator portal.

## What is and isn't finished
- **Done and tested:** logins, sign-up, sessions, the whole student and tutor experience on the database, file uploads and
  downloads, the administrator portal, password changes and resets.
- **Not done yet:** a "forgot my password" email flow, https hosting files, Android release signing, a backup tool.
- The Android project has been built and run on a phone, but only with the earlier version of the screens.
