#!/usr/bin/env python3
"""Mini EHR: a small electronic health record demo with role-based access and audit logging.

EDUCATIONAL DEMO ONLY. Uses fictional data. It is NOT real authentication and must
never be used with real patient information.
"""
import argparse
import sqlite3
from datetime import datetime

DB_FILE = "mini_ehr.db"

PERMISSIONS = {
    "admin": {"add_patient", "view_patient", "add_appointment", "view_appointment",
              "add_record", "view_record", "view_audit"},
    "doctor": {"view_patient", "add_appointment", "view_appointment",
               "add_record", "view_record"},
    "nurse": {"add_patient", "view_patient", "view_appointment", "view_record"},
    "receptionist": {"add_patient", "view_patient", "add_appointment", "view_appointment"},
}

DEMO_USERS = [("admin1", "admin"), ("dr_demo", "doctor"),
              ("nurse_demo", "nurse"), ("reception_demo", "receptionist")]

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    role TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    dob TEXT NOT NULL,
    gender TEXT,
    phone TEXT
);
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    doctor TEXT NOT NULL,
    date TEXT NOT NULL,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'scheduled'
);
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    author TEXT NOT NULL,
    diagnosis TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    action TEXT NOT NULL,
    detail TEXT,
    allowed INTEGER NOT NULL,
    timestamp TEXT NOT NULL
);
"""


def _now():
    return datetime.now().isoformat(timespec="seconds")


def connect(db=DB_FILE):
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def seed_demo(conn):
    conn.executemany("INSERT OR IGNORE INTO users VALUES (?,?)", DEMO_USERS)
    if not conn.execute("SELECT 1 FROM patients").fetchone():
        conn.executemany(
            "INSERT INTO patients (name, dob, gender, phone) VALUES (?,?,?,?)",
            [("Demo Patient One", "1990-01-15", "M", "0500000001"),
             ("Demo Patient Two", "1985-06-30", "F", "0500000002")])
    conn.commit()


def authorize(conn, username, action, detail=""):
    """Check the user's role against the action and write an audit entry either way."""
    row = conn.execute("SELECT role FROM users WHERE username = ?", (username,)).fetchone()
    allowed = bool(row) and action in PERMISSIONS.get(row["role"], set())
    conn.execute("INSERT INTO audit_log (username, action, detail, allowed, timestamp)"
                 " VALUES (?,?,?,?,?)", (username, action, detail, int(allowed), _now()))
    conn.commit()
    if not allowed:
        raise PermissionError(f"User '{username}' is not allowed to perform '{action}'.")


def _require_patient(conn, patient_id):
    if not conn.execute("SELECT 1 FROM patients WHERE id = ?", (patient_id,)).fetchone():
        raise ValueError(f"Patient #{patient_id} not found.")


def add_patient(conn, user, name, dob, gender="", phone=""):
    authorize(conn, user, "add_patient", name)
    cur = conn.execute("INSERT INTO patients (name, dob, gender, phone) VALUES (?,?,?,?)",
                       (name, dob, gender, phone))
    conn.commit()
    return cur.lastrowid


def list_patients(conn, user):
    authorize(conn, user, "view_patient")
    return conn.execute("SELECT * FROM patients ORDER BY id").fetchall()


def add_appointment(conn, user, patient_id, doctor, date, reason=""):
    authorize(conn, user, "add_appointment", f"patient={patient_id}")
    _require_patient(conn, patient_id)
    cur = conn.execute("INSERT INTO appointments (patient_id, doctor, date, reason)"
                       " VALUES (?,?,?,?)", (patient_id, doctor, date, reason))
    conn.commit()
    return cur.lastrowid


def list_appointments(conn, user, patient_id=None):
    authorize(conn, user, "view_appointment", f"patient={patient_id}")
    if patient_id:
        return conn.execute("SELECT * FROM appointments WHERE patient_id = ? ORDER BY date",
                            (patient_id,)).fetchall()
    return conn.execute("SELECT * FROM appointments ORDER BY date").fetchall()


def add_record(conn, user, patient_id, diagnosis, notes=""):
    authorize(conn, user, "add_record", f"patient={patient_id}")
    _require_patient(conn, patient_id)
    cur = conn.execute("INSERT INTO records (patient_id, author, diagnosis, notes, created_at)"
                       " VALUES (?,?,?,?,?)", (patient_id, user, diagnosis, notes, _now()))
    conn.commit()
    return cur.lastrowid


def list_records(conn, user, patient_id):
    authorize(conn, user, "view_record", f"patient={patient_id}")
    return conn.execute("SELECT * FROM records WHERE patient_id = ? ORDER BY id",
                        (patient_id,)).fetchall()


def audit_log(conn, user):
    authorize(conn, user, "view_audit")
    return conn.execute("SELECT * FROM audit_log ORDER BY id").fetchall()


def build_parser():
    p = argparse.ArgumentParser(description="Mini EHR (educational demo, fictional data only)")
    p.add_argument("--db", default=DB_FILE)
    p.add_argument("--user", help="username acting on the system")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="create the database with demo users and patients")
    sub.add_parser("patients", help="list patients")

    ap = sub.add_parser("add-patient")
    ap.add_argument("name")
    ap.add_argument("--dob", required=True, help="YYYY-MM-DD")
    ap.add_argument("--gender", default="")
    ap.add_argument("--phone", default="")

    aa = sub.add_parser("add-appointment")
    aa.add_argument("patient_id", type=int)
    aa.add_argument("--doctor", required=True)
    aa.add_argument("--date", required=True, help="YYYY-MM-DD HH:MM")
    aa.add_argument("--reason", default="")

    la = sub.add_parser("appointments")
    la.add_argument("--patient", type=int)

    ar = sub.add_parser("add-record")
    ar.add_argument("patient_id", type=int)
    ar.add_argument("--diagnosis", required=True)
    ar.add_argument("--notes", default="")

    lr = sub.add_parser("records")
    lr.add_argument("patient_id", type=int)

    sub.add_parser("audit", help="show the audit log (admin only)")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    conn = connect(args.db)
    if args.command == "init":
        seed_demo(conn)
        print("Database ready. Demo users:", ", ".join(f"{u} ({r})" for u, r in DEMO_USERS))
        return
    if not args.user:
        raise SystemExit("--user is required for this command.")
    try:
        if args.command == "patients":
            for r in list_patients(conn, args.user):
                print(f"#{r['id']:<3} {r['name']:<22} {r['dob']}  {r['gender']}  {r['phone']}")
        elif args.command == "add-patient":
            print(f"Patient #{add_patient(conn, args.user, args.name, args.dob, args.gender, args.phone)} added.")
        elif args.command == "add-appointment":
            print(f"Appointment #{add_appointment(conn, args.user, args.patient_id, args.doctor, args.date, args.reason)} booked.")
        elif args.command == "appointments":
            for r in list_appointments(conn, args.user, args.patient):
                print(f"#{r['id']:<3} patient {r['patient_id']:<3} {r['date']}  {r['doctor']}  {r['status']}  {r['reason']}")
        elif args.command == "add-record":
            print(f"Record #{add_record(conn, args.user, args.patient_id, args.diagnosis, args.notes)} saved.")
        elif args.command == "records":
            for r in list_records(conn, args.user, args.patient_id):
                print(f"[{r['created_at']}] {r['author']}: {r['diagnosis']} | {r['notes']}")
        elif args.command == "audit":
            for r in audit_log(conn, args.user):
                flag = "OK    " if r["allowed"] else "DENIED"
                print(f"{r['timestamp']} {flag} {r['username']:<15} {r['action']} {r['detail']}")
    except (PermissionError, ValueError) as exc:
        raise SystemExit(f"Error: {exc}")


if __name__ == "__main__":
    main()
