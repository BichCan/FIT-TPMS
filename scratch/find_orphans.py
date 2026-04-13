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

cur_sem = 13
lec_id = 8

print(f"--- Investigating Lecturer {lec_id} in Semester {cur_sem} ---")

# Students with approved registrations
approved_students = run_query("""
    SELECT r.id as reg_id, r.student_id, u.full_name
    FROM registrations r
    JOIN students s ON r.student_id = s.id
    JOIN users u ON s.user_id = u.id
    WHERE r.lecturer_id = ? AND r.semester_id = ? AND r.status = 'approved'
""", (lec_id, cur_sem))

print(f"Approved Students in Registrations: {len(approved_students)}")
for s in approved_students:
    # Check if they are in ANY class in this semester
    in_class = run_query("""
        SELECT c.class_code
        FROM class_students cs
        JOIN classes c ON cs.class_id = c.id
        WHERE cs.student_id = ? AND c.semester_id = ?
    """, (s['student_id'], cur_sem))
    
    if not in_class:
        print(f"  MISSING: {s['full_name']} (Reg ID: {s['reg_id']}, Student ID: {s['student_id']}) is NOT in any class this semester!")
    else:
        print(f"  OK: {s['full_name']} is in {in_class[0]['class_code']}")
