"""Web API for every portal page. server.py hands requests here.

Public:         GET catalog                    (the course list, also shown on the welcome page)
Everyone:       POST password                  (change your own password)
                GET courses, content/<section>, announcements   POST announcements/read
Student pages:  GET state (everything at once), enrolments, schedule, course/<code>, notes, results, fees,
                accommodation, dashboard
                POST enrolments/enrol, enrolments/drop, submissions (with file contents), payments,
                accommodation, accommodation/cancel
Tutor pages:    GET tutor/courses, tutor/notes?course=, tutor/gradebook?course=
                POST tutor/notes, tutor/notes/delete, tutor/marks, tutor/publish
Admin pages:    GET admin/overview, admin/payments, admin/accommodation, admin/people
                POST admin/payments/status, admin/accommodation/status, admin/announce, admin/people/create,
                admin/people/status, admin/people/reset, admin/people/tutor-courses, admin/courses/save,
                admin/coursework/save, admin/coursework/delete
Files:          GET files/<id> is handled by server.py (it returns the file itself, not JSON)
Everything except `catalog` needs the login token (Authorization: Bearer ...).
"""
import portal_db as p
import portal_data as d
import portal_admin as adm
from portal_data import ApiError


def _need(user, role):
    if user["role"] != role:
        raise ApiError(403, "This page is for " + {"admin": "administrators", "tutor": "tutors", "student": "students"}[role] + ".")


def _q(query, key):
    v = (query or {}).get(key)
    return v[0] if v else None


def _admin(conn, user, verb, sub, data):
    uid = user["id"]
    if verb == "GET":
        if sub == "overview": return adm.overview(conn)
        if sub == "payments": return adm.payments(conn)
        if sub == "accommodation": return adm.accommodation(conn)
        if sub == "people": return adm.people(conn)
    if verb == "POST":
        if sub == "payments/status": return adm.set_payment_status(conn, uid, data.get("id"), data.get("status"))
        if sub == "accommodation/status": return adm.set_accommodation_status(conn, data.get("student"), data.get("status"))
        if sub == "announce": return adm.announce(conn, uid, data.get("title"), data.get("body"), data.get("course"))
        if sub == "people/create-student": return adm.create_student(conn, data)
        if sub == "people/create-tutor": return adm.create_tutor(conn, data)
        if sub == "people/status": return adm.set_status(conn, uid, data.get("id"), data.get("status"))
        if sub == "people/reset": return adm.reset_password(conn, uid, data.get("id"))
        if sub == "people/tutor-courses": return adm.set_tutor_courses(conn, data.get("id"), data.get("courses"))
        if sub == "courses/save": return adm.save_course(conn, data)
        if sub == "coursework/save": return adm.save_coursework(conn, data)
        if sub == "coursework/delete": return adm.delete_coursework(conn, data.get("id"))
    raise ApiError(404, "Not found.")


def dispatch(conn, user, verb, parts, query, data, token):
    uid, name = user["id"], "/".join(parts)
    if verb == "POST" and name == "password":
        ok, msg = p.change_password(conn, uid, str(data.get("current") or ""), str(data.get("new") or ""), token)
        if not ok:
            raise ApiError(400, msg)
        return {"message": msg}
    if parts[0] == "admin":
        _need(user, "admin")
        return _admin(conn, user, verb, "/".join(parts[1:]), data)
    if parts[0] == "tutor":
        _need(user, "tutor")
        sub = "/".join(parts[1:])
        if verb == "GET" and sub == "courses": return {"courses": d.tutor_courses(conn, uid)}
        if verb == "GET" and sub == "notes": return d.tutor_notes(conn, uid, _q(query, "course"))
        if verb == "GET" and sub == "gradebook": return d.gradebook(conn, uid, _q(query, "course"))
        if verb == "POST" and sub == "notes": return d.tutor_save_note(conn, uid, data.get("course"), data.get("id"), data.get("title"), data.get("ref"), data.get("body"))
        if verb == "POST" and sub == "notes/delete": return d.tutor_delete_note(conn, uid, data.get("course"), data.get("id"))
        if verb == "POST" and sub == "marks": return d.set_mark(conn, uid, data.get("course"), data.get("student"), data.get("assessment"), data.get("score"))
        if verb == "POST" and sub == "publish": return d.publish(conn, uid, data.get("course"))
        raise ApiError(404, "Not found.")
    # pages anyone signed in can read
    if verb == "GET" and name == "courses": return {"courses": d.list_courses(conn)}
    if verb == "GET" and parts[0] == "content" and len(parts) == 2: return {"items": d.content(conn, parts[1])}
    if verb == "GET" and name == "announcements": return d.announcements(conn, user)
    if verb == "POST" and name == "announcements/read": return d.mark_announcements_read(conn, user)
    # student pages
    _need(user, "student")
    if verb == "GET":
        if name == "state": return d.student_state(conn, user)
        if name == "enrolments": return {"enrolled": d.enrolled_codes(conn, uid)}
        if name == "schedule": return {"courses": d.schedule(conn, uid)}
        if parts[0] == "course" and len(parts) == 2: return d.course_detail(conn, uid, parts[1])
        if name == "notes": return {"notes": d.my_notes(conn, uid, _q(query, "course"))}
        if name == "results": return d.results(conn, uid)
        if name == "fees": return d.fees(conn, uid)
        if name == "accommodation": return d.accommodation(conn, uid)
        if name == "dashboard": return d.dashboard(conn, user)
    if verb == "POST":
        if name == "enrolments/enrol": return {"enrolled": d.enrol(conn, uid, data.get("course"))}
        if name == "enrolments/drop": return {"enrolled": d.drop(conn, uid, data.get("course"))}
        if name == "notes": return d.add_note(conn, uid, data.get("course"), data.get("title"), data.get("ref"), data.get("body"))
        if name == "notes/update": return d.update_note(conn, uid, data.get("id"), data.get("title"), data.get("ref"), data.get("body"))
        if name == "notes/delete": return d.delete_note(conn, uid, data.get("id"))
        if name == "submissions": return d.submit(conn, uid, data.get("assignment"), data.get("comment"), data.get("files"))
        if name == "payments": return d.record_payment(conn, uid, data.get("amount"), data.get("method"), data.get("reference"))
        if name == "accommodation": return d.request_room(conn, uid, data.get("room"))
        if name == "accommodation/cancel": return d.cancel_room(conn, uid)
    raise ApiError(404, "Not found.")


def route(conn, verb, name, query, data, token):
    """Returns (http status, JSON-ready dict)."""
    if verb == "GET" and name == "catalog":
        return 200, {"ok": True, **d.catalog(conn)}
    user = p.check_session(conn, token or "")
    if not user:
        return 401, {"ok": False, "message": "Session expired. Please log in again."}
    try:
        result = dispatch(conn, user, verb, name.strip("/").split("/"), query, data if isinstance(data, dict) else {}, token)
        conn.commit()
        return 200, {"ok": True, **result}
    except ApiError as e:
        conn.rollback()
        return e.status, {"ok": False, "message": e.message}
