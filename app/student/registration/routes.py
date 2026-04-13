from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from app.database import get_db
from . import registration_bp


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
    return lecturers

@registration_bp.route("/registration")
def registration():
    current_semester = get_current_semester()
    if not current_semester:
        return "Không có học kỳ hiện tại", 400

    project_lecturers = get_lecturers_by_course_type(1)
    thesis_lecturers = get_lecturers_by_course_type(2)
    
    db = get_db()
    cursor = db.cursor()
    user_id = session.get("user_id")
    registered_lecturer_ids = []
    
    if user_id:
        cursor.execute("SELECT id FROM students WHERE user_id = ?", (user_id,))
        student_res = cursor.fetchone()
        if student_res:
            student_id = student_res['id']
            cursor.execute("""
                SELECT lecturer_id FROM registrations 
                WHERE student_id = ? AND semester_id = ?
            """, (student_id, current_semester['id']))
            registered_lecturer_ids = [row['lecturer_id'] for row in cursor.fetchall()]

    return render_template("student/registration.html", 
                         current_semester=current_semester, 
                         project_lecturers=project_lecturers, 
                         thesis_lecturers=thesis_lecturers,
                         registered_lecturer_ids=registered_lecturer_ids)

@registration_bp.route("/registration/form/<int:lecturer_id>")
def registration_form(lecturer_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT l.*, u.full_name, u.email, u.phone
        FROM lecturers l
        JOIN users u ON l.user_id = u.id
        WHERE l.id = ?
    """, (lecturer_id,))
    
    lecturer = cursor.fetchone()
    if not lecturer:
        return "Giảng viên không tồn tại", 404
        
    course_type_id = request.args.get('course_type_id', 1, type=int)
    course_type_name = "Đề án" if course_type_id == 1 else "Khóa luận"
    
    return render_template("student/registrationform.html", 
                         lecturer=dict(lecturer),
                         course_type_id=course_type_id,
                         course_type_name=course_type_name)

@registration_bp.route("/registration/submit", methods=["POST"])
def registration_submit():
    lecturer_id = request.form.get("lecturer_id")
    course_type_id = request.form.get("course_type_id")
    
    current_semester = get_current_semester()
    if not current_semester:
        return jsonify({"success": False, "message": "Không tìm thấy học kỳ hiện tại."}), 400
        
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "Bạn cần đăng nhập để thực hiện hành động này."}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT id FROM students WHERE user_id = ?", (user_id,))
    student_res = cursor.fetchone()
    if not student_res:
        return jsonify({"success": False, "message": "Không tìm thấy thông tin sinh viên."}), 400
    student_id = student_res['id']
    
    try:
        cursor.execute("""
            INSERT INTO registrations (
                student_id, lecturer_id, course_type_id, semester_id, status, registered_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            student_id, lecturer_id, course_type_id, current_semester['id'], 
            'pending', datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        db.commit()
        return jsonify({"success": True, "message": "Đăng ký thành công! Vui lòng chờ giảng viên duyệt."})
    except Exception as e:
        db.rollback()
        print(f"Error during registration: {str(e)}")
        return jsonify({"success": False, "message": f"Có lỗi xảy ra khi lưu đăng ký: {str(e)}"})

@registration_bp.route("/registration/cancel", methods=["POST"])
def cancel_registration():
    lecturer_id = request.form.get("lecturer_id")
    current_semester = get_current_semester()
    user_id = session.get("user_id")
    
    if not current_semester or not user_id:
        return jsonify({"success": False, "message": "Lỗi hệ thống hoặc chưa đăng nhập."}), 400
        
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM students WHERE user_id = ?", (user_id,))
    student_res = cursor.fetchone()
    if not student_res:
        return jsonify({"success": False, "message": "Không tìm thấy thông tin."}), 400
        
    student_id = student_res['id']
    
    try:
        cursor.execute("""
            DELETE FROM registrations 
            WHERE student_id = ? AND lecturer_id = ? AND semester_id = ?
        """, (student_id, lecturer_id, current_semester['id']))
        db.commit()
        return jsonify({"success": True, "message": "Hủy đăng ký thành công."})
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "message": str(e)})
