import sqlite3
import os

db_path = r'd:\FIT-TPMS\FIT-TPMS\FIT-TPMS.db'

def run_query(query, params=()):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# We don't know the lecturer_id for the user, but let's assume one or check all.
lecturers = run_query("SELECT lecturers.id, users.full_name FROM lecturers JOIN users ON lecturers.user_id = users.id")

print("--- Lecturer Registration vs Class Assignment Check ---")
for lec in lecturers:
    lec_id = lec['id']
    print(f"\nLecturer: {lec['full_name']} (ID: {lec_id})")
    
    # Approved registrations
    approved_regs = run_query("SELECT id, student_id, class_id FROM registrations WHERE lecturer_id = ? AND status = 'approved'", (lec_id,))
    print(f"  Approved Registrations: {len(approved_regs)}")
    
    # Class assignments
    total_assignments = run_query("""
        SELECT COUNT(*) as count 
        FROM class_students cs
        JOIN classes c ON cs.class_id = c.id
        WHERE c.lecturer_id = ?
    """, (lec_id,))[0]['count']
    print(f"  Total Class Assignments (class_students): {total_assignments}")
    
    if len(approved_regs) != total_assignments:
        print("  WARNING: Mismatch detected!")

print("\n--- Current Semester Classes ---")
cur_sem = run_query("SELECT id FROM semesters WHERE is_current = 1")
if cur_sem:
    sem_id = cur_sem[0]['id']
    classes = run_query("SELECT id, class_code, class_name FROM classes WHERE semester_id = ?", (sem_id,))
    for c in classes:
        count = run_query("SELECT COUNT(*) as count FROM class_students WHERE class_id = ?", (c['id'],))[0]['count']
        print(f"  Class {c['class_code']}: {count} students")
