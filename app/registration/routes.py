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
    db=get_db()
    cursor = db.cursor()
    current_semester=get_current_semester()
    cursor.execute("""
            SELECT lecturer_id FROM lecturer_quotas 
            WHERE course_type_id = ? AND semester_id = ?
        """, (course_type_id, current_semester['id']))
    lecturers_id = cursor.fetchall()
    lecturers = []
    for(lecturer_id) in lecturers_id:
        cursor.execute("select * from lecturers where id=?",(lecturer_id))
        lecturer=cursor.fetchone()
        if lecturer:
            lecturers.append(lecturer)
    db.close()
    return lecturers
@registration_bp.route("/registration")
def registration():
    db = get_db()
    cursor=db.cursor()
    now=datetime.now().date()
    current_semester=get_current_semester()
    if not current_semester:
        return "Không có học kỳ hiện tại", 400

    project_lecturers = get_lecturers_by_course_type(1)
    thesis_lecturers = get_lecturers_by_course_type(2)
    db.close()
    return render_template("registration.html",current_semester=current_semester,project_lecturers=project_lecturers,thesis_lecturers=thesis_lecturers)


