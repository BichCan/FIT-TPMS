from datetime import datetime
from flask import render_template, request
from app.database import get_db
from app.registration import registration_bp


def get_current_semester():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM semesters WHERE is_current = 1 LIMIT 1")
    current_semester = cursor.fetchone()
    return current_semester
def get_lecturers_by_course_type(course_type_id):
    db = get_db()
    cursor = db.cursor()
    current_semester = get_current_semester()
    if not current_semester:
        return []
    
    cursor.execute("""
        SELECT l.*, u.full_name, u.email, u.phone
        FROM lecturers l
        JOIN users u ON l.user_id = u.id
        JOIN lecturer_quotas q ON l.id = q.lecturer_id
        WHERE q.course_type_id = ? AND q.semester_id = ?
    """, (course_type_id, current_semester['id']))
    
    lecturers = [dict(row) for row in cursor.fetchall()]
    db.close()
    return lecturers

@registration_bp.route("/registration")
def registration():
    current_semester = get_current_semester()
    if not current_semester:
        return "Không có học kỳ hiện tại", 400

    project_lecturers = get_lecturers_by_course_type(1)
    thesis_lecturers = get_lecturers_by_course_type(2)
    return render_template("registration.html", 
                         current_semester=current_semester, 
                         project_lecturers=project_lecturers, 
                         thesis_lecturers=thesis_lecturers)



