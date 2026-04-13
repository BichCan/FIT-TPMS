from flask import render_template, session, redirect, url_for, flash, request, jsonify
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
            s.id AS student_id,
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

    # Kiem tra xem co quota nao chua
    cursor.execute("""
        SELECT COUNT(*) FROM lecturer_quotas 
        WHERE lecturer_id = ? AND semester_id = ?
    """, (lecturer_id, semester_id))
    quota_count = cursor.fetchone()[0]
    require_quota_setup = (quota_count == 0)
    
    return render_template(
        'lecturer/registrationsmanagement.html',
        registrations=registrations,
        current_filter=course_type_filter,
        require_quota_setup=require_quota_setup
    )

@registrationsmanagement_bp.route('/lecturer/api/save-quota', methods=['POST'])
def save_quota():
    if 'user_id' not in session or session.get('role') != 'lecturer':
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    project_max = data.get('project_max')
    thesis_max = data.get('thesis_max')

    if project_max is None or thesis_max is None:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        project_max = int(project_max)
        thesis_max = int(thesis_max)
    except ValueError:
        return jsonify({"error": "Invalid format"}), 400

    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT id FROM lecturers WHERE user_id = ?", (user_id,))
    lecturer = cursor.fetchone()
    if not lecturer:
        return jsonify({"error": "Lecturer not found"}), 404

    cursor.execute("SELECT id FROM semesters WHERE is_current = 1")
    semester = cursor.fetchone()
    if not semester:
        return jsonify({"error": "Semester not found"}), 404

    lecturer_id = lecturer['id']
    semester_id = semester['id']

    try:
        cursor.execute("SELECT COUNT(*) FROM lecturer_quotas WHERE lecturer_id = ? AND semester_id = ?", (lecturer_id, semester_id))
        if cursor.fetchone()[0] > 0:
            return jsonify({"error": "Quota already set"}), 400

        cursor.execute("""
            INSERT INTO lecturer_quotas (lecturer_id, course_type_id, semester_id, max_students, current_students)
            VALUES (?, 1, ?, ?, 0)
        """, (lecturer_id, semester_id, project_max))

        cursor.execute("""
            INSERT INTO lecturer_quotas (lecturer_id, course_type_id, semester_id, max_students, current_students)
            VALUES (?, 2, ?, ?, 0)
        """, (lecturer_id, semester_id, thesis_max))

        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

@registrationsmanagement_bp.route('/lecturer/api/get-available-classes/<int:registration_id>')
def get_available_classes(registration_id):
    if 'user_id' not in session or session.get('role') != 'lecturer':
        return jsonify({"error": "Unauthorized"}), 403

    db = get_db()
    cursor = db.cursor()

    # Lấy thông tin đơn đăng ký và course_type_id
    cursor.execute("""
        SELECT r.lecturer_id, r.course_type_id, r.semester_id 
        FROM registrations r 
        WHERE r.id = ?
    """, (registration_id,))
    reg = cursor.fetchone()
    
    if not reg:
        return jsonify({"error": "Registration not found"}), 404

    # Lấy danh sách lớp phù hợp (cùng giảng viên, cùng học kỳ, cùng loại học phần, trạng thái active)
    query = """
        SELECT c.id, c.class_code, c.class_name, co.course_name, s.name as semester_name, s.year
        FROM classes c
        JOIN courses co ON c.course_id = co.id
        JOIN semesters s ON c.semester_id = s.id
        WHERE c.lecturer_id = ? 
          AND c.semester_id = ? 
          AND co.course_type_id = ?
          AND c.status = 'active'
    """
    cursor.execute(query, (reg['lecturer_id'], reg['semester_id'], reg['course_type_id']))
    classes = cursor.fetchall()
    
    return jsonify([dict(row) for row in classes])

@registrationsmanagement_bp.route('/lecturer/api/assign-to-class', methods=['POST'])
def assign_student():
    if 'user_id' not in session or session.get('role') != 'lecturer':
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    registration_ids = data.get('registration_ids')
    class_id = data.get('class_id')

    if not registration_ids or not class_id:
        return jsonify({"error": "Missing parameters"}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        for reg_id in registration_ids:
            # Lấy student_id từ registration
            cursor.execute("SELECT student_id FROM registrations WHERE id = ?", (reg_id,))
            reg = cursor.fetchone()
            if not reg:
                continue # Hoặc báo lỗi nếu cần
            
            student_id = reg['student_id']

            # Thêm vào class_students (Sử dụng INSERT OR IGNORE để tránh lỗi nếu đã tồn tại)
            cursor.execute("""
                INSERT OR IGNORE INTO class_students (class_id, student_id, grade)
                VALUES (?, ?, NULL)
            """, (class_id, student_id))

            # Cập nhật trạng thái registration
            cursor.execute("""
                UPDATE registrations 
                SET status = 'approved', processed_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (reg_id,))

        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

@registrationsmanagement_bp.route('/lecturer/api/registration-details/<int:registration_id>')
def get_registration_details(registration_id):
    if 'user_id' not in session or session.get('role') != 'lecturer':
        return jsonify({"error": "Unauthorized"}), 403

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT 
            r.id,
            r.knowledge,
            r.project,
            r.topic,
            r.status,
            r.registered_at,
            u.full_name AS student_name,
            s.student_code,
            ct.type_name
        FROM registrations r
        JOIN students s ON r.student_id = s.id
        JOIN users u ON s.user_id = u.id
        JOIN course_types ct ON r.course_type_id = ct.id
        WHERE r.id = ?
    """, (registration_id,))
    
    details = cursor.fetchone()
    if not details:
        return jsonify({"error": "Details not found"}), 404
        
    return jsonify(dict(details))
