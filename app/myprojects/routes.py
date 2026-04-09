from flask import render_template, abort
from app.database import get_db
from app.myprojects import myprojects_bp


@myprojects_bp.route('/my-projects')
def my_projects():
    conn = get_db()
    cur = conn.cursor()

    # Truy vấn lấy thông tin:
    # Kết nối bảng registrations -> lecturers -> users (để lấy tên GV)
    # Kết nối bảng registrations -> course_types (để lấy loại hình)
    query = """
        SELECT 
            r.id, 
            ct.type_name AS course_type_name, 
            u.full_name AS lecturer_name, 
            r.registered_at, 
            r.status
        FROM registrations r
        JOIN lecturers l ON r.lecturer_id = l.id
        JOIN users u ON l.user_id = u.id
        JOIN course_types ct ON r.course_type_id = ct.id
        ORDER BY r.registered_at DESC
    """
    cur.execute(query)
    registrations = cur.fetchall()
    return render_template('my_projects.html', registrations=registrations)


@myprojects_bp.route('/project-detail/<int:id>')
def project_detail(id):
    conn = get_db()
    cur = conn.cursor()

    # Query chi tiết: Lấy tên SV và tên GV từ bảng users
    query = """
        SELECT 
            r.*, 
            u_s.full_name AS student_name, 
            s.student_code,
            u_l.full_name AS lecturer_name, 
            ct.type_name AS course_type_name
        FROM registrations r
        JOIN students s ON r.student_id = s.id
        JOIN users u_s ON s.user_id = u_s.id
        JOIN lecturers l ON r.lecturer_id = l.id
        JOIN users u_l ON l.user_id = u_l.id
        JOIN course_types ct ON r.course_type_id = ct.id
        WHERE r.id = ?
    """
    cur.execute(query, (id,))
    project = cur.fetchone()

    if project is None:
        abort(404)

    return render_template('project_detail.html', project=project)