import sqlite3
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, session, abort
from app.database import get_db
from app.lecturer import lecturer_bp


def get_lecturer_id():
    """Lấy lecturer_id từ session user_id."""
    user_id = session.get('user_id')
    if not user_id or session.get('role') != 'lecturer':
        return None
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM lecturers WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    return row[0] if row else None


# ============================================================
# 1. DANH SACH LOP HOC
# ============================================================
@lecturer_bp.route('/lecturer/lop-hoc')
def classes():
    lecturer_id = get_lecturer_id()
    if not lecturer_id:
        flash('Bạn cần đăng nhập với vai trò giảng viên.', 'danger')
        return redirect(url_for('login.login'))

    q = request.args.get('q', '').strip()
    tab = request.args.get('tab', 'all')

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sql = """
        SELECT c.id, c.class_code, c.class_name, c.status,
               ct.type_name AS course_type,
               s.name AS semester_name, s.year AS semester_year,
               (SELECT COUNT(*) FROM class_students cs WHERE cs.class_id = c.id) AS student_count
        FROM classes c
        JOIN courses co ON c.course_id = co.id
        JOIN course_types ct ON co.course_type_id = ct.id
        JOIN semesters s ON c.semester_id = s.id
        WHERE c.lecturer_id = ?
    """
    params = [lecturer_id]

    if q:
        sql += " AND (c.class_code LIKE ? OR c.class_name LIKE ?)"
        params.extend([f'%{q}%', f'%{q}%'])

    if tab == 'active':
        sql += " AND c.status = 'active'"
    elif tab == 'archived':
        sql += " AND (c.status = 'completed' OR c.status = 'archived')"

    sql += " ORDER BY s.year DESC, s.name DESC, c.class_code"
    cur.execute(sql, params)
    classes_list = cur.fetchall()

    return render_template('lecturer/lecturer_classes.html',
                           classes=classes_list, q=q, tab=tab)


# ============================================================
# 2. TAO LOP MOI
# ============================================================
@lecturer_bp.route('/lecturer/lop-hoc/tao-moi', methods=['GET', 'POST'])
def create_class():
    lecturer_id = get_lecturer_id()
    if not lecturer_id:
        flash('Bạn cần đăng nhập với vai trò giảng viên.', 'danger')
        return redirect(url_for('login.login'))

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if request.method == 'POST':
        class_code = request.form.get('class_code', '').strip()
        semester_id = request.form.get('semester_id')
        course_type_id = request.form.get('course_type_id')

        if not class_code or not semester_id or not course_type_id:
            flash('Vui lòng điền đầy đủ thông tin.', 'danger')
            return redirect(url_for('lecturer.create_class'))

        # Lấy course tương ứng với course_type
        cur.execute("SELECT id, course_name FROM courses WHERE course_type_id = ? LIMIT 1",
                    (course_type_id,))
        course = cur.fetchone()
        if not course:
            flash('Loại hình đồ án không hợp lệ.', 'danger')
            return redirect(url_for('lecturer.create_class'))

        # Kiểm tra mã lớp trùng
        cur.execute("SELECT id FROM classes WHERE class_code = ?", (class_code,))
        if cur.fetchone():
            flash('Mã lớp học đã tồn tại. Vui lòng chọn mã khác.', 'danger')
            return redirect(url_for('lecturer.create_class'))

        try:
            cur.execute("""
                INSERT INTO classes (class_code, class_name, course_id, lecturer_id, semester_id, status)
                VALUES (?, ?, ?, ?, ?, 'active')
            """, (class_code, course['course_name'], course['id'], lecturer_id, semester_id))
            conn.commit()
            flash('Tạo lớp học thành công!', 'success')
            return redirect(url_for('lecturer.classes'))
        except Exception as e:
            conn.rollback()
            flash(f'Lỗi khi tạo lớp: {str(e)}', 'danger')
            return redirect(url_for('lecturer.create_class'))

    # GET: lấy danh sách học kỳ và loại hình
    cur.execute("SELECT * FROM semesters ORDER BY year DESC, name DESC")
    semesters = cur.fetchall()
    cur.execute("SELECT * FROM course_types")
    course_types = cur.fetchall()

    return render_template('lecturer/lecturer_create_class.html',
                           semesters=semesters, course_types=course_types)


# ============================================================
# 3. CHI TIET LOP HOC
# ============================================================
@lecturer_bp.route('/lecturer/lop-hoc/<int:class_id>')
def class_detail(class_id):
    lecturer_id = get_lecturer_id()
    if not lecturer_id:
        flash('Bạn cần đăng nhập với vai trò giảng viên.', 'danger')
        return redirect(url_for('login.login'))

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Thông tin lớp
    cur.execute("""
        SELECT c.*, ct.type_name AS course_type,
               s.name AS semester_name, s.year AS semester_year, s.is_current
        FROM classes c
        JOIN courses co ON c.course_id = co.id
        JOIN course_types ct ON co.course_type_id = ct.id
        JOIN semesters s ON c.semester_id = s.id
        WHERE c.id = ? AND c.lecturer_id = ?
    """, (class_id, lecturer_id))
    class_info = cur.fetchone()
    if not class_info:
        abort(404)

    # Danh sách sinh viên
    cur.execute("""
        SELECT s.id AS student_id, s.student_code, u.full_name,
               cs.grade,
               (SELECT COUNT(*) FROM submissions sub
                JOIN assignments a ON sub.assignment_id = a.id
                WHERE a.class_id = ? AND sub.student_id = s.id) AS submission_count,
               (SELECT COUNT(*) FROM assignments WHERE class_id = ?) AS total_assignments
        FROM class_students cs
        JOIN students s ON cs.student_id = s.id
        JOIN users u ON s.user_id = u.id
        WHERE cs.class_id = ?
        ORDER BY u.full_name
    """, (class_id, class_id, class_id))
    students = cur.fetchall()

    # Danh sách bài tập
    cur.execute("""
        SELECT a.*,
               (SELECT COUNT(*) FROM submissions s WHERE s.assignment_id = a.id) AS submission_count
        FROM assignments a
        WHERE a.class_id = ?
        ORDER BY a.deadline ASC
    """, (class_id,))
    assignments = cur.fetchall()

    # Bài nộp gần đây
    cur.execute("""
        SELECT sub.id, sub.file_name, sub.submitted_at, sub.is_late,
               a.title AS assignment_title,
               u.full_name AS student_name, s.student_code
        FROM submissions sub
        JOIN assignments a ON sub.assignment_id = a.id
        JOIN students s ON sub.student_id = s.id
        JOIN users u ON s.user_id = u.id
        WHERE a.class_id = ?
        ORDER BY sub.submitted_at DESC
        LIMIT 5
    """, (class_id,))
    recent_submissions = cur.fetchall()

    # Thông báo gần đây
    cur.execute("""
        SELECT id, title, content, created_at
        FROM notifications
        WHERE class_id = ?
        ORDER BY created_at DESC
        LIMIT 3
    """, (class_id,))
    announcements = cur.fetchall()

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template('lecturer/lecturer_class_detail.html',
                           class_info=class_info,
                           students=students,
                           assignments=assignments,
                           recent_submissions=recent_submissions,
                           announcements=announcements,
                           now_str=now_str)


# ============================================================
# 4. TAO BAI TAP (Assignment)
# ============================================================
@lecturer_bp.route('/lecturer/lop-hoc/<int:class_id>/tao-bai-tap', methods=['GET', 'POST'])
def create_assignment(class_id):
    lecturer_id = get_lecturer_id()
    if not lecturer_id:
        flash('Bạn cần đăng nhập với vai trò giảng viên.', 'danger')
        return redirect(url_for('login.login'))

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Kiểm tra quyền sở hữu lớp
    cur.execute("SELECT * FROM classes WHERE id = ? AND lecturer_id = ?", (class_id, lecturer_id))
    class_info = cur.fetchone()
    if not class_info:
        abort(404)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        deadline = request.form.get('deadline', '').strip()

        if not title or not deadline:
            flash('Vui lòng nhập tiêu đề và hạn nộp.', 'danger')
            return redirect(url_for('lecturer.create_assignment', class_id=class_id))

        try:
            cur.execute("""
                INSERT INTO assignments (class_id, title, description, deadline, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (class_id, title, description, deadline, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            flash('Tạo bài tập thành công!', 'success')
            return redirect(url_for('lecturer.class_detail', class_id=class_id))
        except Exception as e:
            conn.rollback()
            flash(f'Lỗi: {str(e)}', 'danger')

    return render_template('lecturer/lecturer_create_assignment.html', class_info=class_info)


# ============================================================
# 5. SUA BAI TAP
# ============================================================
@lecturer_bp.route('/lecturer/lop-hoc/<int:class_id>/bai-tap/<int:assignment_id>/sua', methods=['POST'])
def edit_assignment(class_id, assignment_id):
    lecturer_id = get_lecturer_id()
    if not lecturer_id:
        flash('Bạn cần đăng nhập với vai trò giảng viên.', 'danger')
        return redirect(url_for('login.login'))

    conn = get_db()
    cur = conn.cursor()

    # Kiểm tra quyền
    cur.execute("""
        SELECT a.id FROM assignments a
        JOIN classes c ON a.class_id = c.id
        WHERE a.id = ? AND c.id = ? AND c.lecturer_id = ?
    """, (assignment_id, class_id, lecturer_id))
    if not cur.fetchone():
        abort(404)

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    deadline = request.form.get('deadline', '').strip()

    if not title or not deadline:
        flash('Tiêu đề và hạn nộp không được để trống.', 'danger')
        return redirect(url_for('lecturer.class_detail', class_id=class_id))

    try:
        cur.execute("""
            UPDATE assignments SET title = ?, description = ?, deadline = ?
            WHERE id = ?
        """, (title, description, deadline, assignment_id))
        conn.commit()
        flash('Cập nhật bài tập thành công!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Lỗi: {str(e)}', 'danger')

    return redirect(url_for('lecturer.class_detail', class_id=class_id))


# ============================================================
# 6. XOA BAI TAP
# ============================================================
@lecturer_bp.route('/lecturer/lop-hoc/<int:class_id>/bai-tap/<int:assignment_id>/xoa', methods=['POST'])
def delete_assignment(class_id, assignment_id):
    lecturer_id = get_lecturer_id()
    if not lecturer_id:
        flash('Bạn cần đăng nhập với vai trò giảng viên.', 'danger')
        return redirect(url_for('login.login'))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT a.id FROM assignments a
        JOIN classes c ON a.class_id = c.id
        WHERE a.id = ? AND c.id = ? AND c.lecturer_id = ?
    """, (assignment_id, class_id, lecturer_id))
    if not cur.fetchone():
        abort(404)

    try:
        cur.execute("DELETE FROM submissions WHERE assignment_id = ?", (assignment_id,))
        cur.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
        conn.commit()
        flash('Đã xóa bài tập.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Lỗi: {str(e)}', 'danger')

    return redirect(url_for('lecturer.class_detail', class_id=class_id))


# ============================================================
# 7. TAO THONG BAO (Announcement)
# ============================================================
@lecturer_bp.route('/lecturer/lop-hoc/<int:class_id>/tao-thong-bao', methods=['GET', 'POST'])
def create_announcement(class_id):
    lecturer_id = get_lecturer_id()
    if not lecturer_id:
        flash('Bạn cần đăng nhập với vai trò giảng viên.', 'danger')
        return redirect(url_for('login.login'))

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM classes WHERE id = ? AND lecturer_id = ?", (class_id, lecturer_id))
    class_info = cur.fetchone()
    if not class_info:
        abort(404)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()

        if not title:
            flash('Vui lòng nhập tiêu đề thông báo.', 'danger')
            return redirect(url_for('lecturer.create_announcement', class_id=class_id))

        try:
            # Lấy danh sách sinh viên trong lớp
            cur.execute("""
                SELECT s.user_id FROM class_students cs
                JOIN students s ON cs.student_id = s.id
                WHERE cs.class_id = ?
            """, (class_id,))
            student_users = cur.fetchall()

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for su in student_users:
                cur.execute("""
                    INSERT INTO notifications (user_id, title, content, class_id, is_read, created_at)
                    VALUES (?, ?, ?, ?, 0, ?)
                """, (su['user_id'], title, content, class_id, now))

            conn.commit()
            flash('Đăng thông báo thành công!', 'success')
            return redirect(url_for('lecturer.class_detail', class_id=class_id))
        except Exception as e:
            conn.rollback()
            flash(f'Lỗi: {str(e)}', 'danger')

    return render_template('lecturer/lecturer_create_announcement.html', class_info=class_info)


# ============================================================
# 8. XEM TAT CA BAI NOP CUA 1 BAI TAP
# ============================================================
@lecturer_bp.route('/lecturer/lop-hoc/<int:class_id>/bai-tap/<int:assignment_id>/bai-nop')
def assignment_submissions(class_id, assignment_id):
    lecturer_id = get_lecturer_id()
    if not lecturer_id:
        flash('Bạn cần đăng nhập với vai trò giảng viên.', 'danger')
        return redirect(url_for('login.login'))

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT a.*, c.class_code, c.class_name
        FROM assignments a
        JOIN classes c ON a.class_id = c.id
        WHERE a.id = ? AND c.id = ? AND c.lecturer_id = ?
    """, (assignment_id, class_id, lecturer_id))
    assignment = cur.fetchone()
    if not assignment:
        abort(404)

    cur.execute("""
        SELECT sub.*, u.full_name AS student_name, s.student_code,
               (SELECT COUNT(*) FROM feedbacks f WHERE f.submission_id = sub.id) AS feedback_count
        FROM submissions sub
        JOIN students s ON sub.student_id = s.id
        JOIN users u ON s.user_id = u.id
        WHERE sub.assignment_id = ?
        ORDER BY sub.submitted_at DESC
    """, (assignment_id,))
    submissions = cur.fetchall()

    return render_template('lecturer/lecturer_all_submissions.html',
                           assignment=assignment,
                           submissions=submissions,
                           class_id=class_id)


# ============================================================
# 9. CHI TIET BAI NOP + NHAN XET
# ============================================================
@lecturer_bp.route('/lecturer/bai-nop/<int:submission_id>', methods=['GET'])
def submission_detail(submission_id):
    lecturer_id = get_lecturer_id()
    if not lecturer_id:
        flash('Bạn cần đăng nhập với vai trò giảng viên.', 'danger')
        return redirect(url_for('login.login'))

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT sub.*, a.title AS assignment_title, a.class_id,
               u.full_name AS student_name, s.student_code,
               c.class_code, c.class_name
        FROM submissions sub
        JOIN assignments a ON sub.assignment_id = a.id
        JOIN classes c ON a.class_id = c.id
        JOIN students s ON sub.student_id = s.id
        JOIN users u ON s.user_id = u.id
        WHERE sub.id = ? AND c.lecturer_id = ?
    """, (submission_id, lecturer_id))
    submission = cur.fetchone()
    if not submission:
        abort(404)

    # Lấy nhận xét
    cur.execute("""
        SELECT f.*, u.full_name AS lecturer_name
        FROM feedbacks f
        JOIN lecturers l ON f.lecturer_id = l.id
        JOIN users u ON l.user_id = u.id
        WHERE f.submission_id = ?
        ORDER BY f.created_at DESC
    """, (submission_id,))
    feedbacks = cur.fetchall()

    return render_template('lecturer/lecturer_submission_detail.html',
                           submission=submission, feedbacks=feedbacks)


@lecturer_bp.route('/lecturer/bai-nop/<int:submission_id>/nhan-xet', methods=['POST'])
def add_feedback(submission_id):
    lecturer_id = get_lecturer_id()
    if not lecturer_id:
        flash('Bạn cần đăng nhập với vai trò giảng viên.', 'danger')
        return redirect(url_for('login.login'))

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Kiểm tra quyền
    cur.execute("""
        SELECT c.lecturer_id FROM submissions sub
        JOIN assignments a ON sub.assignment_id = a.id
        JOIN classes c ON a.class_id = c.id
        WHERE sub.id = ?
    """, (submission_id,))
    row = cur.fetchone()
    if not row or row['lecturer_id'] != lecturer_id:
        abort(404)

    content = request.form.get('content', '').strip()
    if not content:
        flash('Vui lòng nhập nội dung nhận xét.', 'danger')
        return redirect(url_for('lecturer.submission_detail', submission_id=submission_id))

    try:
        cur.execute("""
            INSERT INTO feedbacks (submission_id, lecturer_id, content, created_at)
            VALUES (?, ?, ?, ?)
        """, (submission_id, lecturer_id, content, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        flash('Gửi nhận xét thành công!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Lỗi: {str(e)}', 'danger')

    return redirect(url_for('lecturer.submission_detail', submission_id=submission_id))
