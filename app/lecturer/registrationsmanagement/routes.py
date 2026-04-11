from flask import render_template, session, redirect, url_for, flash, request
from app.database import get_db
from . import registrationsmanagement_bp

@registrationsmanagement_bp.route('/lecturer/registrations')
def registrations_management():
    if 'user_id' not in session or session.get('role') != 'lecturer':
        flash("Bạn không có quyền truy cập trang này.", "danger")
        return redirect(url_for('login.login'))

    user_id = session['user_id']
    course_type_filter = request.args.get('type', 'all')
    
    db = get_db()
    cursor = db.cursor()

    # 1. Lấy lecturer_id từ user_id
    cursor.execute("SELECT id FROM lecturers WHERE user_id = ?", (user_id,))
    lecturer = cursor.fetchone()
    if not lecturer:
        flash("Không tìm thấy thông tin giảng viên.", "danger")
        return redirect(url_for('login.login'))
    
    lecturer_id = lecturer['id']

    # 2. Lấy semester_id hiện tại
    cursor.execute("SELECT id FROM semesters WHERE is_current = 1")
    semester = cursor.fetchone()
    if not semester:
        flash("Không tìm thấy học kỳ hiện tại.", "danger")
        return redirect(url_for('login.login'))
    
    semester_id = semester['id']

    # 3. Truy vấn danh sách sinh viên đăng ký
    query = """
        SELECT 
            r.id,
            r.status,
            r.registered_at,
            u.full_name AS student_name,
            s.student_code,
            ct.type_name,
            ct.id AS course_type_id
        FROM registrations r
        JOIN students s ON r.student_id = s.id
        JOIN users u ON s.user_id = u.id
        JOIN course_types ct ON r.course_type_id = ct.id
        WHERE r.lecturer_id = ? AND r.semester_id = ?
    """
    
    params = [lecturer_id, semester_id]
    
    if course_type_filter == 'project':
        query += " AND r.course_type_id = 1"
    elif course_type_filter == 'thesis':
        query += " AND r.course_type_id = 2"
        
    query += " ORDER BY r.registered_at DESC"
    
    cursor.execute(query, params)
    registrations = cursor.fetchall()
    
    return render_template(
        'lecturer/registrationsmanagement.html',
        registrations=registrations,
        current_filter=course_type_filter
    )
