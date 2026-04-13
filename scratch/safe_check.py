import sqlite3

db_path = r'd:\FIT-TPMS\FIT-TPMS\FIT-TPMS.db'

def run_query(query, params=()):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Get the lecturer who has classes in the current semester
cur_sem = run_query("SELECT id FROM semesters WHERE is_current = 1")[0]['id']
print(f"Current Semester ID: {cur_sem}")

classes = run_query("""
    SELECT c.id, c.class_code, c.lecturer_id,
    (SELECT COUNT(*) FROM class_students WHERE class_id = c.id) as student_count
    FROM classes c
    WHERE c.semester_id = ?
""", (cur_sem,))

for c in classes:
    print(f"Class ID {c['id']} ({c['class_code']}) for Lecturer {c['lecturer_id']}: {c['student_count']} students")
    # Verify by registrations
    approved_regs = run_query("SELECT COUNT(*) as count FROM registrations WHERE lecturer_id = ? AND semester_id = ? AND status = 'approved'", (c['lecturer_id'], cur_sem))
    print(f"  Total approved registrations for this lecturer in this semester: {approved_regs[0]['count']}")
