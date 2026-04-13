from flask import render_template, session, redirect, url_for
from app.database import get_db
from . import student_home_bp

@student_home_bp.route('/')
@student_home_bp.route('/home')
def home():
    if 'user_id' not in session or session.get('role') != 'student':
        # If lecturer is logged in, redirect to lecturer home or handle appropriately
        if session.get('role') == 'lecturer':
             return redirect(url_for('lecturer_home.home'))
        return redirect(url_for('login.login'))

    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()

    # 1. Get current semester
    cursor.execute("SELECT * FROM semesters WHERE is_current = 1 LIMIT 1")
    current_semester = cursor.fetchone()
    
    # 2. Get student_id
    cursor.execute("SELECT id FROM students WHERE user_id = ?", (user_id,))
    student = cursor.fetchone()
    if not student:
        return "Student profile not found", 404
    student_id = student['id']

    ongoing_courses = []
    if current_semester:
        # 3. Get ongoing classes
        cursor.execute("""
            SELECT c.*, ct.type_name, co.course_name, u.full_name as lecturer_name
            FROM class_students cs
            JOIN classes c ON cs.class_id = c.id
            JOIN courses co ON c.course_id = co.id
            JOIN course_types ct ON co.course_type_id = ct.id
            JOIN lecturers l ON c.lecturer_id = l.id
            JOIN users u ON l.user_id = u.id
            WHERE cs.student_id = ? AND c.semester_id = ?
        """, (student_id, current_semester['id']))
        ongoing_courses = cursor.fetchall()

    # 4. Get thesis library (latest 6 published reports)
    cursor.execute("""
        SELECT pr.*, t.title, u.full_name as lecturer_name, ct.type_name, co.course_name
        FROM published_reports pr
        JOIN topics t ON pr.topic_id = t.id
        JOIN classes c ON t.class_id = c.id
        JOIN courses co ON c.course_id = co.id
        JOIN course_types ct ON co.course_type_id = ct.id
        JOIN lecturers l ON c.lecturer_id = l.id
        JOIN users u ON l.user_id = u.id
        ORDER BY pr.published_at DESC
        LIMIT 2
    """)
    library_items = cursor.fetchall()

    return render_template(
        'student/home.html',
        ongoing_courses=ongoing_courses,
        library_items=library_items,
        current_semester=current_semester
    )
