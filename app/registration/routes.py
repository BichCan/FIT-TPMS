from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify
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
    
    return render_template("registrationform.html", 
                         lecturer=dict(lecturer),
                         course_type_id=course_type_id,
                         course_type_name=course_type_name)

@registration_bp.route("/registration/submit", methods=["POST"])
def registration_submit():
    # Lấy thông tin từ form
    lecturer_id = request.form.get("lecturer_id")
    course_type_id = request.form.get("course_type_id")
    knowledge = request.form.get("knowledge")
    project = request.form.get("project")
    topic = request.form.get("topic")
    
    # Lấy học kỳ hiện tại
    current_semester = get_current_semester()
    if not current_semester:
        return jsonify({"success": False, "message": "Không tìm thấy học kỳ hiện tại."}), 400
        
    # Giả định student_id = 1 cho prototype (vì chưa có login session)
    student_id = 1
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO registration (
                student_id, lecturer_id, semester_id, course_type_id, 
                knowledge, project, topic, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_id, lecturer_id, current_semester['id'], course_type_id,
            knowledge, project, topic, 'Chờ duyệt', datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        db.commit()
        return jsonify({"success": True, "message": "Đăng ký thành công! Vui lòng chờ giảng viên duyệt."})
    except Exception as e:
        db.rollback()
        print(f"Error during registration: {str(e)}")
        return jsonify({"success": False, "message": f"Có lỗi xảy ra khi lưu đăng ký: {str(e)}"})
    finally:
        db.close()





