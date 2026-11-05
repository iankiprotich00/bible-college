# What changed in this update: the screens now use the database

Until now only logins used the database. Every other page saved its data on the phone it was used on. This update
connects all of them, so the phone, a tablet and the tutors' laptops now see the same data.

## For students (when the server is running)
- Enrolments, coursework submissions, results, fees, room requests and announcements are all kept on the server.
- Assignment files are **uploaded for real** (up to 10 MB each, 30 MB per submission) and can be downloaded again.
- The result slip, fees and notifications update as soon as a tutor or the bursar acts.
- The bell checks for new announcements every 30 seconds by itself.
- Information pages (Library, Chapel, About, Help) and the course list come from the database.
- "Change your password" is on the profile page. Changing it signs you out of your other devices.

## For tutors
- Lecture notes, the gradebook (marks save as you type), publishing, and a **Submitted work** list where you can
  download each student's files. You can switch between the courses you teach.

## New: administrator portal (bursar and registrar)
Sign in on the same staff page as tutors (the "Tutor login" link). Tabs:
- **Overview**: students, tutors, fees collected and outstanding, what needs review.
- **Payments**: confirm or reject what students record. A rejected payment no longer counts toward their balance.
- **Rooms**: approve or decline accommodation requests. Approved rooms are charged on the fee statement.
- **Announcements**: send to everyone, or to one course.
- **People**: create students and tutors (they get a temporary password and must choose their own), reset passwords,
  suspend or reactivate, and choose which courses each tutor teaches.
- **Courses**: add or edit courses (fee, room, exam, weekly timetable) and their coursework. Students see the change
  straight away.

Demo administrator: `admin@cornerstone.example`, password `admin1234`. Change or delete it before real use.
On a real database, make your own with `python3 create_admin.py`.

## Upgrading
Start the server as usual. An older `portal.db` is backed up and upgraded automatically (to version 3). No accounts,
payments or submissions are lost. Files submitted before this update only have their names recorded, so they can't be downloaded.

## Still true
- Without the server (opening the HTML file directly, or the published preview) the app falls back to saving on the
  device, as before. Staff screens and syncing need the server.
- Nothing here has been run on https yet, or on a phone's Android build.
