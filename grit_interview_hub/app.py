import streamlit as st
import sqlite3
from pathlib import Path
from datetime import datetime, date, time, timedelta
import uuid

DB_PATH = Path(__file__).with_name("grit_interviews.db")
BADGE_LEVELS = ["Novice", "Specialist", "Expert", "Master", "Grand Master"]
ACTIVE_STATUSES = ("SCHEDULED", "RESCHEDULED")

st.set_page_config(page_title="GRIT Interview Hub", page_icon="🎓", layout="wide")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            track TEXT NOT NULL,
            badge_level TEXT NOT NULL,
            attendance REAL NOT NULL DEFAULT 0,
            registration_ok INTEGER NOT NULL DEFAULT 1,
            conduct_ok INTEGER NOT NULL DEFAULT 1,
            skills_completed INTEGER NOT NULL DEFAULT 0,
            required_skills INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS interviewers (
            interviewer_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS availability_slots (
            slot_id TEXT PRIMARY KEY,
            interviewer_id TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN',
            created_at TEXT NOT NULL,
            FOREIGN KEY(interviewer_id) REFERENCES interviewers(interviewer_id),
            CHECK(end_time > start_time)
        );

        CREATE TABLE IF NOT EXISTS interviews (
            interview_id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            interviewer_id TEXT NOT NULL,
            slot_id TEXT NOT NULL,
            track TEXT NOT NULL,
            badge_level TEXT NOT NULL,
            status TEXT NOT NULL,
            outcome TEXT,
            feedback TEXT,
            booked_at TEXT NOT NULL,
            completed_at TEXT,
            FOREIGN KEY(student_id) REFERENCES students(student_id),
            FOREIGN KEY(interviewer_id) REFERENCES interviewers(interviewer_id),
            FOREIGN KEY(slot_id) REFERENCES availability_slots(slot_id)
        );

        CREATE TABLE IF NOT EXISTS badges (
            badge_id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            track TEXT NOT NULL,
            badge_level TEXT NOT NULL,
            status TEXT NOT NULL,
            awarded_at TEXT,
            nullified_at TEXT,
            nullification_reason TEXT,
            FOREIGN KEY(student_id) REFERENCES students(student_id),
            UNIQUE(student_id, track, badge_level)
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            log_id TEXT PRIMARY KEY,
            actor TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            action TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_interviews_student
        ON interviews(student_id, track, badge_level);
        CREATE INDEX IF NOT EXISTS idx_slots_start
        ON availability_slots(start_time, status);
        """)
    seed_demo_data()

def audit(actor, entity_type, entity_id, action, old_value="", new_value=""):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), actor, entity_type, entity_id, action,
             str(old_value), str(new_value), datetime.now().isoformat(timespec="seconds"))
        )

def seed_demo_data():
    with get_conn() as conn:
        if conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] > 0:
            return
        now = datetime.now().isoformat(timespec="seconds")
        students = [
            ("STU001", "Aarav Kumar", "aarav@niat.edu", "AI Product Mastery", "Novice", 92, 1, 1, 4, 4),
            ("STU002", "Diya Sharma", "diya@niat.edu", "AI Systems Mastery", "Novice", 88, 1, 1, 5, 5),
            ("STU003", "Ishaan Reddy", "ishaan@niat.edu", "AI Product Mastery", "Specialist", 81, 1, 1, 6, 6),
            ("STU004", "Meera Nair", "meera@niat.edu", "AI Models Mastery", "Novice", 68, 1, 1, 4, 4),
            ("STU005", "Kabir Patel", "kabir@niat.edu", "AI Systems Mastery", "Novice", 95, 1, 1, 3, 5),
            ("STU006", "Ananya Rao", "ananya@niat.edu", "AI Product Mastery", "Novice", 90, 1, 1, 4, 4),
        ]
        conn.executemany(
            "INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(*s, now) for s in students]
        )
        interviewers = [
            ("INT001", "Priya Menon", "priya@niat.edu", 1),
            ("INT002", "Rahul Verma", "rahul@niat.edu", 1),
            ("INT003", "Sneha Iyer", "sneha@niat.edu", 1),
        ]
        conn.executemany("INSERT INTO interviewers VALUES (?, ?, ?, ?)", interviewers)

      
        interviewers_ids = ["INT001", "INT002", "INT003"]
        for day_offset in range(1, 8):
            d = date.today() + timedelta(days=day_offset)
            for interviewer_id, hour in zip(interviewers_ids, [10, 11, 14]):
                start = datetime.combine(d, time(hour, 0))
                end = start + timedelta(minutes=30)
                conn.execute(
                    "INSERT INTO availability_slots VALUES (?, ?, ?, ?, 'OPEN', ?)",
                    (str(uuid.uuid4()), interviewer_id, start.isoformat(timespec="minutes"),
                     end.isoformat(timespec="minutes"), now)
                )

       
        slots = conn.execute(
            "SELECT slot_id, interviewer_id, start_time FROM availability_slots ORDER BY start_time"
        ).fetchall()
        if slots:
            conn.execute("UPDATE availability_slots SET status='BOOKED' WHERE slot_id=?", (slots[0]["slot_id"],))
            conn.execute(
                """INSERT INTO interviews VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("IVW-DEMO-001", "STU001", slots[0]["interviewer_id"], slots[0]["slot_id"],
                 "AI Product Mastery", "Novice", "SCHEDULED", None, None, now, None)
            )
        if len(slots) > 1:
            conn.execute("UPDATE availability_slots SET status='BOOKED' WHERE slot_id=?", (slots[1]["slot_id"],))
            conn.execute(
                """INSERT INTO interviews VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("IVW-DEMO-002", "STU002", slots[1]["interviewer_id"], slots[1]["slot_id"],
                 "AI Systems Mastery", "Novice", "COMPLETED", "PASS",
                 "Strong fundamentals and clear problem-solving.", now, now)
            )
            conn.execute(
                "INSERT OR IGNORE INTO badges VALUES (?, ?, ?, ?, ?, ?, NULL, NULL)",
                ("BDG-DEMO-002", "STU002", "AI Systems Mastery", "Novice", "AWARDED", now)
            )
        if len(slots) > 2:
            conn.execute("UPDATE availability_slots SET status='BOOKED' WHERE slot_id=?", (slots[2]["slot_id"],))
            conn.execute(
                """INSERT INTO interviews VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("IVW-DEMO-003", "STU003", slots[2]["interviewer_id"], slots[2]["slot_id"],
                 "AI Product Mastery", "Specialist", "RETAKE_REQUIRED", "RETAKE",
                 "Please strengthen system design explanation and try again.", now, now)
            )


def rows(query, params=()):
    with get_conn() as conn:
        return conn.execute(query, params).fetchall()

def one(query, params=()):
    with get_conn() as conn:
        return conn.execute(query, params).fetchone()

def student_eligibility(student):
    reasons = []
    if student["attendance"] < 75:
        reasons.append("Attendance must be at least 75%.")
    if not student["registration_ok"]:
        reasons.append("Semester registration is incomplete.")
    if not student["conduct_ok"]:
        reasons.append("Code-of-conduct review is pending.")
    if student["skills_completed"] < student["required_skills"]:
        reasons.append(f"Complete all required skills ({student['skills_completed']}/{student['required_skills']}).")
    return len(reasons) == 0, reasons

def get_student_current_interview(student_id, track, badge_level):
    return one(
        """SELECT i.*, s.start_time, s.end_time, it.name AS interviewer_name
           FROM interviews i
           JOIN availability_slots s ON s.slot_id=i.slot_id
           JOIN interviewers it ON it.interviewer_id=i.interviewer_id
           WHERE i.student_id=? AND i.track=? AND i.badge_level=?
           ORDER BY i.booked_at DESC LIMIT 1""",
        (student_id, track, badge_level)
    )

def book_slot(student_id, slot_id):
    student = one("SELECT * FROM students WHERE student_id=?", (student_id,))
    eligible, reasons = student_eligibility(student)
    if not eligible:
        return False, "Student is not eligible: " + " ".join(reasons)
    slot = one("SELECT * FROM availability_slots WHERE slot_id=?", (slot_id,))
    if not slot or slot["status"] != "OPEN":
        return False, "This slot is no longer available. Please select another slot."
    if datetime.fromisoformat(slot["start_time"]) <= datetime.now():
        return False, "Past slots cannot be booked."

    current = get_student_current_interview(student_id, student["track"], student["badge_level"])
    if current and current["status"] in ACTIVE_STATUSES:
        return False, "You already have an active booking for this badge."

    try:
        with get_conn() as conn:
             
            cur = conn.execute(
                "UPDATE availability_slots SET status='BOOKED' WHERE slot_id=? AND status='OPEN'",
                (slot_id,)
            )
            if cur.rowcount != 1:
                return False, "Someone else just booked this slot. Choose another."
            conn.execute(
                """INSERT INTO interviews
                   VALUES (?, ?, ?, ?, ?, ?, 'SCHEDULED', NULL, NULL, ?, NULL)""",
                (str(uuid.uuid4()), student_id, slot["interviewer_id"], slot_id,
                 student["track"], student["badge_level"], datetime.now().isoformat(timespec="seconds"))
            )
        audit(student_id, "interview", slot_id, "BOOKED", "OPEN", "SCHEDULED")
        return True, "Your interview is booked successfully."
    except sqlite3.IntegrityError:
        return False, "Booking could not be completed. Please refresh and try again."

def add_availability(interviewer_id, start_dt, end_dt):
    if start_dt <= datetime.now():
        return False, "Availability must be in the future."
    if end_dt <= start_dt:
        return False, "End time must be after start time."
    overlap = one(
        """SELECT slot_id FROM availability_slots
           WHERE interviewer_id=? AND status='OPEN'
           AND start_time < ? AND end_time > ? LIMIT 1""",
        (interviewer_id, end_dt.isoformat(timespec="minutes"), start_dt.isoformat(timespec="minutes"))
    )
    if overlap:
        return False, "This overlaps with another open slot."
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO availability_slots VALUES (?, ?, ?, ?, 'OPEN', ?)",
            (str(uuid.uuid4()), interviewer_id, start_dt.isoformat(timespec="minutes"),
             end_dt.isoformat(timespec="minutes"), datetime.now().isoformat(timespec="seconds"))
        )
    audit(interviewer_id, "availability", interviewer_id, "SLOT_ADDED", "", start_dt.isoformat())
    return True, "Availability added."

def record_outcome(interview_id, outcome, feedback, actor):
    interview = one("SELECT * FROM interviews WHERE interview_id=?", (interview_id,))
    if not interview:
        return False, "Interview not found."
    if interview["status"] not in ("SCHEDULED", "RESCHEDULED"):
        return False, "An outcome can only be recorded for a scheduled interview."
    new_status = {"PASS": "COMPLETED", "FAIL": "COMPLETED", "RETAKE": "RETAKE_REQUIRED"}[outcome]
    now = datetime.now().isoformat(timespec="seconds")
    with get_conn() as conn:
        conn.execute(
            """UPDATE interviews SET status=?, outcome=?, feedback=?, completed_at=?
               WHERE interview_id=?""",
            (new_status, outcome, feedback, now, interview_id)
        )
        if outcome == "PASS":
            conn.execute(
                """INSERT OR REPLACE INTO badges
                   (badge_id, student_id, track, badge_level, status, awarded_at, nullified_at, nullification_reason)
                   VALUES (?, ?, ?, ?, 'AWARDED', ?, NULL, NULL)""",
                (str(uuid.uuid4()), interview["student_id"], interview["track"],
                 interview["badge_level"], now)
            )
    audit(actor, "interview", interview_id, "OUTCOME_RECORDED", "SCHEDULED", f"{outcome}: {feedback}")
    return True, f"Outcome saved: {outcome}."

def flag_malpractice(student_id, reason, actor):
    if not reason.strip():
        return False, "Please provide a reason."
    now = datetime.now().isoformat(timespec="seconds")
    with get_conn() as conn:
        badge_rows = conn.execute(
            "SELECT * FROM badges WHERE student_id=? AND status='AWARDED'", (student_id,)
        ).fetchall()
        conn.execute(
            """UPDATE badges SET status='NULLIFIED', nullified_at=?, nullification_reason=?
               WHERE student_id=? AND status='AWARDED'""",
            (now, reason.strip(), student_id)
        )
    audit(actor, "student", student_id, "MALPRACTICE_FLAGGED",
          f"{len(badge_rows)} awarded badge(s)", reason.strip())
    return True, f"Malpractice flag recorded. {len(badge_rows)} badge(s) nullified."

def release_slot_for_cancel(interview_id, actor):
    interview = one("SELECT * FROM interviews WHERE interview_id=?", (interview_id,))
    if not interview or interview["status"] not in ACTIVE_STATUSES:
        return False, "Only active bookings can be cancelled."
    with get_conn() as conn:
        conn.execute("UPDATE interviews SET status='CANCELLED' WHERE interview_id=?", (interview_id,))
        conn.execute("UPDATE availability_slots SET status='OPEN' WHERE slot_id=?", (interview["slot_id"],))
    audit(actor, "interview", interview_id, "CANCELLED", "SCHEDULED", "CANCELLED")
    return True, "Booking cancelled and slot reopened."


def status_label(status):
    return status.replace("_", " ").title() if status else "Not started"

def page_header(title, subtitle):
    st.title(title)
    st.caption(subtitle)
    st.divider()

def student_select():
    students = rows("SELECT * FROM students ORDER BY name")
    labels = {f"{s['name']} ({s['student_id']})": s["student_id"] for s in students}
    selected = st.sidebar.selectbox("Demo student", list(labels.keys()))
    return one("SELECT * FROM students WHERE student_id=?", (labels[selected],))


init_db()

st.sidebar.title("🎓 GRIT Interview Hub")
role = st.sidebar.radio("Choose workspace", ["Student", "Interviewer", "Interview Team"])
st.sidebar.caption("Prototype • Demo data • SQLite persistence")
st.sidebar.divider()

if role == "Student":
    student = student_select()
    eligible, reasons = student_eligibility(student)
    current = get_student_current_interview(student["student_id"], student["track"], student["badge_level"])
    badge = one(
        "SELECT * FROM badges WHERE student_id=? AND track=? AND badge_level=?",
        (student["student_id"], student["track"], student["badge_level"])
    )
    page_header("Student Dashboard", f"Welcome, {student['name']} • {student['track']} / {student['badge_level']}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Skills completed", f"{student['skills_completed']}/{student['required_skills']}")
    c2.metric("Attendance", f"{student['attendance']}%")
    c3.metric("Interview status", status_label(current["status"]) if current else "Not booked")

    if badge and badge["status"] == "NULLIFIED":
        st.error("Your badge has been nullified following a malpractice review. Please contact the GRIT team for clarification.")
    elif badge and badge["status"] == "AWARDED":
        st.success(f"Congratulations! Your {badge['badge_level']} badge in {badge['track']} has been awarded.")
    elif not eligible:
        st.warning("You are not yet eligible to book your interview.")
        for reason in reasons:
            st.write("• " + reason)
    elif current and current["status"] in ACTIVE_STATUSES:
        st.success("Your interview is confirmed.")
        a, b = st.columns(2)
        a.write(f"**Date & time:** {datetime.fromisoformat(current['start_time']).strftime('%d %b %Y, %I:%M %p')}")
        b.write(f"**Interviewer:** {current['interviewer_name']}")
        st.info("Please join on time and keep your project work and identification ready.")
        if st.button("Cancel booking (demo policy)", type="secondary"):
            ok, msg = release_slot_for_cancel(current["interview_id"], student["student_id"])
            (st.success if ok else st.error)(msg)
            st.rerun()
    elif current and current["status"] == "RETAKE_REQUIRED":
        st.warning("A retake has been requested. Review the feedback and book a new interview slot.")
        st.write(f"**Interviewer feedback:** {current['feedback'] or 'Please contact the interview team.'}")
    elif current and current["outcome"] == "FAIL":
        st.error("Your interview result is Fail. Please follow the guidance shared by the GRIT team.")
        st.write(f"**Feedback:** {current['feedback'] or 'No feedback provided.'}")
    else:
        st.info("You have completed the required skills. Choose an available interviewer slot below.")

    st.subheader("Book an interview")
    can_book = eligible and not (current and current["status"] in ACTIVE_STATUSES) and not (badge and badge["status"] == "AWARDED")
    open_slots = rows(
        """SELECT a.*, i.name AS interviewer_name
           FROM availability_slots a JOIN interviewers i ON i.interviewer_id=a.interviewer_id
           WHERE a.status='OPEN' AND a.start_time > ?
           ORDER BY a.start_time""",
        (datetime.now().isoformat(timespec="minutes"),)
    )
    if not can_book:
        st.caption("Booking is unavailable until the conditions above are resolved.")
    elif not open_slots:
        st.info("No interview slots are currently available. Please check again later.")
    else:
        slot_options = {
            f"{datetime.fromisoformat(s['start_time']).strftime('%a, %d %b • %I:%M %p')} – {s['interviewer_name']}":
            s["slot_id"] for s in open_slots
        }
        chosen = st.selectbox("Available slots", list(slot_options.keys()))
        if st.button("Confirm interview booking", type="primary"):
            ok, msg = book_slot(student["student_id"], slot_options[chosen])
            (st.success if ok else st.error)(msg)
            st.rerun()

    st.subheader("Interview history")
    history = rows(
        """SELECT i.*, a.start_time, it.name AS interviewer_name
           FROM interviews i JOIN availability_slots a ON a.slot_id=i.slot_id
           JOIN interviewers it ON it.interviewer_id=i.interviewer_id
           WHERE i.student_id=? ORDER BY i.booked_at DESC""",
        (student["student_id"],)
    )
    if history:
        st.dataframe([{
            "Badge": f"{x['track']} / {x['badge_level']}",
            "Date": datetime.fromisoformat(x["start_time"]).strftime("%d %b %Y %I:%M %p"),
            "Interviewer": x["interviewer_name"],
            "Status": status_label(x["status"]),
            "Outcome": x["outcome"] or "—",
            "Feedback": x["feedback"] or "—"
        } for x in history], use_container_width=True, hide_index=True)
    else:
        st.caption("No interview history yet.")

elif role == "Interviewer":
    interviewers = rows("SELECT * FROM interviewers WHERE active=1 ORDER BY name")
    interviewer_map = {f"{i['name']} ({i['interviewer_id']})": i["interviewer_id"] for i in interviewers}
    selected = st.sidebar.selectbox("Interviewer", list(interviewer_map.keys()))
    interviewer_id = interviewer_map[selected]
    interviewer = one("SELECT * FROM interviewers WHERE interviewer_id=?", (interviewer_id,))
    page_header("Interviewer Workspace", f"Manage availability and interview outcomes • {interviewer['name']}")

    tab1, tab2 = st.tabs(["My availability", "Daily schedule & outcomes"])
    with tab1:
        st.subheader("Add availability")
        d = st.date_input("Date", value=date.today() + timedelta(days=1), min_value=date.today())
        t1, t2 = st.columns(2)
        start_t = t1.time_input("Start time", value=time(10, 0))
        end_t = t2.time_input("End time", value=time(10, 30))
        if st.button("Publish availability", type="primary"):
            start_dt = datetime.combine(d, start_t)
            end_dt = datetime.combine(d, end_t)
            ok, msg = add_availability(interviewer_id, start_dt, end_dt)
            (st.success if ok else st.error)(msg)
            st.rerun()

        st.subheader("My upcoming slots")
        slots = rows(
            "SELECT * FROM availability_slots WHERE interviewer_id=? ORDER BY start_time",
            (interviewer_id,)
        )
        if slots:
            st.dataframe([{
                "Date": datetime.fromisoformat(s["start_time"]).strftime("%d %b %Y"),
                "Time": datetime.fromisoformat(s["start_time"]).strftime("%I:%M %p"),
                "End": datetime.fromisoformat(s["end_time"]).strftime("%I:%M %p"),
                "Status": s["status"]
            } for s in slots], use_container_width=True, hide_index=True)
        else:
            st.caption("No availability published.")

    with tab2:
        selected_day = st.date_input("Schedule date", value=date.today(), key="schedule_day")
        start_iso = datetime.combine(selected_day, time.min).isoformat()
        end_iso = datetime.combine(selected_day + timedelta(days=1), time.min).isoformat()
        schedule = rows(
            """SELECT i.*, s.name AS student_name, s.email, a.start_time, a.end_time
               FROM interviews i JOIN students s ON s.student_id=i.student_id
               JOIN availability_slots a ON a.slot_id=i.slot_id
               WHERE i.interviewer_id=? AND a.start_time>=? AND a.start_time<?
               ORDER BY a.start_time""",
            (interviewer_id, start_iso, end_iso)
        )
        if not schedule:
            st.info("No interviews scheduled for this date.")
        for item in schedule:
            with st.expander(
                f"{datetime.fromisoformat(item['start_time']).strftime('%I:%M %p')} • {item['student_name']} • {item['badge_level']} • {status_label(item['status'])}",
                expanded=item["status"] in ACTIVE_STATUSES
            ):
                st.write(f"**Student:** {item['student_name']} ({item['student_id']})")
                st.write(f"**Email:** {item['email']}")
                st.write(f"**Track / Badge:** {item['track']} / {item['badge_level']}")
                st.write(f"**Status:** {status_label(item['status'])}")
                if item["status"] in ACTIVE_STATUSES:
                    outcome = st.selectbox(
                        "Interview outcome",
                        ["PASS", "FAIL", "RETAKE"],
                        key=f"outcome_{item['interview_id']}"
                    )
                    feedback = st.text_area("Feedback for student", key=f"feedback_{item['interview_id']}")
                    if st.button("Save outcome", key=f"save_{item['interview_id']}", type="primary"):
                        ok, msg = record_outcome(item["interview_id"], outcome, feedback, interviewer_id)
                        (st.success if ok else st.error)(msg)
                        st.rerun()
                else:
                    st.write(f"**Outcome:** {item['outcome'] or '—'}")
                    st.write(f"**Feedback:** {item['feedback'] or '—'}")

else:
    page_header("Interview Operations Console", "Track eligibility, bookings, outcomes and malpractice reviews.")
    students = rows("SELECT * FROM students ORDER BY name")
    total = len(students)
    eligible_students = [s for s in students if student_eligibility(s)[0]]
    booked_ids = {
        r["student_id"] for r in rows(
            "SELECT student_id FROM interviews WHERE status IN ('SCHEDULED','RESCHEDULED')"
        )
    }
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total students", total)
    c2.metric("Eligible", len(eligible_students))
    c3.metric("Booked", len(booked_ids))
    c4.metric("Yet to book", max(0, len(eligible_students) - len(booked_ids)))

    st.subheader("Eligible student booking tracker")
    tracker = []
    for s in eligible_students:
        latest = get_student_current_interview(s["student_id"], s["track"], s["badge_level"])
        tracker.append({
            "Student": s["name"],
            "Student ID": s["student_id"],
            "Track / Badge": f"{s['track']} / {s['badge_level']}",
            "Booking": status_label(latest["status"]) if latest else "Not booked",
            "Outcome": latest["outcome"] if latest and latest["outcome"] else "—",
            "Interviewer": latest["interviewer_name"] if latest else "—"
        })
    st.dataframe(tracker, use_container_width=True, hide_index=True)

    st.subheader("All interview bookings")
    all_interviews = rows(
        """SELECT i.*, s.name AS student_name, it.name AS interviewer_name, a.start_time
           FROM interviews i JOIN students s ON s.student_id=i.student_id
           JOIN interviewers it ON it.interviewer_id=i.interviewer_id
           JOIN availability_slots a ON a.slot_id=i.slot_id
           ORDER BY a.start_time DESC"""
    )
    if all_interviews:
        st.dataframe([{
            "Student": x["student_name"],
            "Track": x["track"],
            "Badge": x["badge_level"],
            "Interviewer": x["interviewer_name"],
            "Date/time": datetime.fromisoformat(x["start_time"]).strftime("%d %b %Y %I:%M %p"),
            "Status": status_label(x["status"]),
            "Outcome": x["outcome"] or "—"
        } for x in all_interviews], use_container_width=True, hide_index=True)

    st.subheader("Eligibility management (demo)")
    st.caption("Use this to demonstrate how changes in attendance, skills or registration affect booking eligibility.")
    student_options = {f"{s['name']} ({s['student_id']})": s["student_id"] for s in students}
    chosen_student = st.selectbox("Select student", list(student_options.keys()))
    target_id = student_options[chosen_student]
    target = one("SELECT * FROM students WHERE student_id=?", (target_id,))
    with st.form("eligibility_form"):
        attendance = st.number_input("Attendance %", min_value=0.0, max_value=100.0, value=float(target["attendance"]))
        skills_done = st.number_input("Skills completed", min_value=0, max_value=30, value=int(target["skills_completed"]))
        required = st.number_input("Required skills", min_value=1, max_value=30, value=int(target["required_skills"]))
        registration = st.checkbox("Semester registration complete", value=bool(target["registration_ok"]))
        conduct = st.checkbox("Code of conduct clear", value=bool(target["conduct_ok"]))
        update = st.form_submit_button("Update eligibility")
        if update:
            with get_conn() as conn:
                conn.execute(
                    """UPDATE students SET attendance=?, skills_completed=?, required_skills=?,
                       registration_ok=?, conduct_ok=? WHERE student_id=?""",
                    (attendance, skills_done, required, int(registration), int(conduct), target_id)
                )
            audit("ADMIN", "student", target_id, "ELIGIBILITY_UPDATED", "", f"{attendance}% / {skills_done}/{required}")
            st.success("Student eligibility updated.")
            st.rerun()

    st.subheader("Malpractice review")
    st.warning("Only authorised GRIT administrators should use this action. It nullifies currently awarded badges but preserves the original interview record.")
    flagged_student = st.selectbox("Student to flag", list(student_options.keys()), key="malpractice_student")
    reason = st.text_area("Reason / case reference", placeholder="Describe the verified malpractice finding...")
    if st.button("Flag malpractice and nullify awarded badge", type="primary"):
        ok, msg = flag_malpractice(student_options[flagged_student], reason, "ADMIN")
        (st.success if ok else st.error)(msg)
        st.rerun()

    st.subheader("Audit trail")
    logs = rows("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 30")
    if logs:
        st.dataframe([dict(x) for x in logs], use_container_width=True, hide_index=True)
    else:
        st.caption("No audit events yet.")

st.sidebar.divider()
st.sidebar.caption("Demo note: choose different student profiles to explore before/after states. Data persists in grit_interviews.db.")
