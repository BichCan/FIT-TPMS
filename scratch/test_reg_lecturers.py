import sqlite3

def test_query():
    conn = sqlite3.connect('FIT-TPMS.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Get current semester
    cursor.execute("SELECT * FROM semesters WHERE is_current = 1 LIMIT 1")
    current_semester = cursor.fetchone()
    print(f"Current Semester: {dict(current_semester) if current_semester else 'None'}")
    
    if not current_semester:
        return

    # 2. Get lecturers for type 1 (Project)
    course_type_id = 1
    cursor.execute("""
        SELECT l.*, u.full_name, u.email, u.phone, 
               q.max_students, q.current_students
        FROM lecturers l
        JOIN users u ON l.user_id = u.id
        JOIN lecturer_quotas q ON l.id = q.lecturer_id
        WHERE q.course_type_id = ? AND q.semester_id = ?
    """, (course_type_id, current_semester['id']))
    
    lecturers = [dict(row) for row in cursor.fetchall()]
    print(f"Project Lecturers (Type 1): {len(lecturers)}")
    for l in lecturers:
        print(f" - {l['full_name']} (ID: {l['id']}), Quota: {l['max_students']}, Used: {l['current_students']}")

    # 3. Get lecturers for type 2 (Thesis)
    course_type_id = 2
    cursor.execute("""
        SELECT l.*, u.full_name, u.email, u.phone, 
               q.max_students, q.current_students
        FROM lecturers l
        JOIN users u ON l.user_id = u.id
        JOIN lecturer_quotas q ON l.id = q.lecturer_id
        WHERE q.course_type_id = ? AND q.semester_id = ?
    """, (course_type_id, current_semester['id']))
    
    lecturers = [dict(row) for row in cursor.fetchall()]
    print(f"Thesis Lecturers (Type 2): {len(lecturers)}")
    for l in lecturers:
        print(f" - {l['full_name']} (ID: {l['id']}), Quota: {l['max_students']}, Used: {l['current_students']}")

    conn.close()

if __name__ == "__main__":
    test_query()
