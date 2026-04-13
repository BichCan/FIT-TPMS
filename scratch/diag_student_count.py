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

print("--- Current Semester Information ---")
current_semester = run_query("SELECT * FROM semesters WHERE is_current = 1")
print(current_semester)

if current_semester:
    sem_id = current_semester[0]['id']
    print(f"\n--- Classes in Semester {sem_id} for Lecturer 15 (as example) ---")
    # Note: user_id is in session, I don't know the current lecturer_id. 
    # Let's just list all classes in this semester.
    classes = run_query("""
        SELECT c.id, c.class_code, c.class_name, 
        (SELECT COUNT(*) FROM class_students WHERE class_id = c.id) as student_count
        FROM classes c
        WHERE c.semester_id = ?
    """, (sem_id,))
    for c in classes:
        print(c)
        students = run_query("SELECT student_id FROM class_students WHERE class_id = ?", (c['id'],))
        print(f"  Students: {students}")

print("\n--- All Class-Students Mappings ---")
mappings = run_query("SELECT * FROM class_students LIMIT 20")
print(mappings)
