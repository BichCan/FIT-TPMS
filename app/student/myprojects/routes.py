from flask import render_template, abort, session, redirect, url_for, request, flash
from app.database import get_db
from . import myprojects_bp
import os
from datetime import datetime


@myprojects_bp.route('/my-projects')
def my_projects():
    user_id = session.get('user_id') or 1
    conn = get_db()
    # Cấu hình trả về dictionary để dễ truy cập ở template
    conn.row_factory = lambda cursor, row: dict(zip([column[0] for column in cursor.description], row))
    cur = conn.cursor()

    # 1. Lấy danh sách lớp và tính toán TIẾN ĐỘ thực tế
    # Tiến độ = (số bài đã nộp / tổng số bài tập) * 100
    query_classes = """
        SELECT 
            c.id, c.class_code, c.class_name, 
            u_l.full_name AS lecturer_name,
            ct.type_name AS course_type,
            (SELECT COUNT(*) FROM assignments a WHERE a.class_id = c.id) as total_tasks,
            (SELECT COUNT(*) FROM submissions s 
             JOIN assignments a ON s.assignment_id = a.id 
             WHERE a.class_id = c.id AND s.student_id = st.id) as completed_tasks,
            (SELECT title FROM topics t WHERE t.class_id = c.id AND t.student_id = st.id LIMIT 1) as current_topic
        FROM classes c
        JOIN class_students cs ON c.id = cs.class_id
        JOIN students st ON cs.student_id = st.id
        JOIN lecturers l ON c.lecturer_id = l.id
        JOIN users u_l ON l.user_id = u_l.id
        JOIN courses cr ON c.course_id = cr.id
        JOIN course_types ct ON cr.course_type_id = ct.id
        WHERE st.user_id = ?
    """
    cur.execute(query_classes, (user_id,))
    registrations = cur.fetchall()

    # Tính toán thêm trường phần trăm cho mỗi lớp
    for item in registrations:
        if item['total_tasks'] > 0:
            item['progress_percent'] = int((item['completed_tasks'] / item['total_tasks']) * 100)
        else:
            item['progress_percent'] = 0

    # 2. Lấy LỊCH TRÌNH sắp tới (Assignment có deadline gần nhất chưa nộp)
    query_schedule = """
        SELECT a.title, a.deadline, a.description
        FROM assignments a
        JOIN class_students cs ON a.class_id = cs.class_id
        JOIN students st ON cs.student_id = st.id
        LEFT JOIN submissions s ON a.id = s.assignment_id AND s.student_id = st.id
        WHERE st.user_id = ? AND s.id IS NULL AND a.deadline > DATETIME('now')
        ORDER BY a.deadline ASC
        LIMIT 1
    """
    cur.execute(query_schedule, (user_id,))
    upcoming_event = cur.fetchone()

    return render_template('student/myprojects.html',
                           registrations=registrations,
                           upcoming_event=upcoming_event)

@myprojects_bp.route('/project-detail/<int:id>')
def project_detail(id):
    user_id = session.get('user_id') or 1
    conn = get_db()
    conn.row_factory = lambda cursor, row: dict(zip([column[0] for column in cursor.description], row))
    cur = conn.cursor()

    # 1. Lấy thông tin lớp học, giảng viên và thông tin sinh viên hiện tại [cite: 2, 6]
    cur.execute("""
        SELECT c.id, c.class_code, c.class_name, u.full_name AS lecturer_name, 
               s.id AS student_pk, s.student_code
        FROM classes c
        JOIN lecturers l ON c.lecturer_id = l.id
        JOIN users u ON l.user_id = u.id
        JOIN class_students cs ON c.id = cs.class_id
        JOIN students s ON cs.student_id = s.id
        WHERE c.id = ? AND s.user_id = ?
    """, (id, user_id))
    class_info = cur.fetchone()

    # 2. Tính toán Progress thực tế
    cur.execute("""
        SELECT 
            (SELECT COUNT(*) FROM assignments WHERE class_id = ?) as total,
            (SELECT COUNT(*) FROM submissions WHERE student_id = ? AND assignment_id IN 
                (SELECT id FROM assignments WHERE class_id = ?)) as completed
    """, (id, class_info['student_pk'], id))
    counts = cur.fetchone()
    progress = int((counts['completed'] / counts['total'] * 100)) if counts['total'] > 0 else 0

    # 3. Lấy thông tin đề tài
    cur.execute("SELECT title, description FROM topics WHERE class_id = ? AND student_id = ?",
               (id, class_info['student_pk']))
    topic = cur.fetchone()

    # 4. Lấy danh sách thông báo thực tế
    cur.execute("""
        SELECT title, content, created_at 
        FROM notifications 
        WHERE user_id = ? OR related_id = ? 
        ORDER BY created_at DESC LIMIT 1
    """, (user_id, id))
    latest_notification = cur.fetchone()

    # 5. Danh sách bài tập và điểm số (Lấy grade từ bảng class_students)
    cur.execute("""
        SELECT a.id, a.title, a.description, a.deadline, 
               sub.submitted_at, sub.file_url, sub.is_late, cs.grade
        FROM assignments a
        LEFT JOIN submissions sub ON a.id = sub.assignment_id AND sub.student_id = ?
        LEFT JOIN class_students cs ON a.class_id = cs.class_id AND cs.student_id = ?
        WHERE a.class_id = ?
        ORDER BY a.deadline ASC
    """, (class_info['student_pk'], class_info['student_pk'], id))
    assignments = cur.fetchall()

    return render_template('student/project_detail.html',
                           class_info=class_info, topic=topic,
                           latest_notification=latest_notification,
                           assignments=assignments, progress=progress)


@myprojects_bp.route('/update-topic/<int:class_id>', methods=['POST'])
def update_topic(class_id):
    user_id = session.get('user_id') or 1
    title = request.form.get('title')
    description = request.form.get('description')

    conn = get_db()
    cur = conn.cursor()

    # Lấy student_id của user hiện tại
    cur.execute("SELECT id FROM students WHERE user_id = ?", (user_id,))
    student = cur.fetchone()
    student_id = student[0]

    # Kiểm tra xem đã có topic chưa
    cur.execute("SELECT id FROM topics WHERE student_id = ? AND class_id = ?", (student_id, class_id))
    existing_topic = cur.fetchone()

    if existing_topic:
        # Nếu có rồi thì cập nhật
        cur.execute("UPDATE topics SET title = ?, description = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (title, description, existing_topic[0]))
    else:
        # Nếu chưa có thì thêm mới
        cur.execute("INSERT INTO topics (student_id, class_id, title, description) VALUES (?, ?, ?, ?)",
                    (student_id, class_id, title, description))

    conn.commit()
    return redirect(url_for('myprojects.project_detail', id=class_id))


@myprojects_bp.route('/assignment/<int:assignment_id>/submit', methods=['GET', 'POST'])
def submit_assignment(assignment_id):
    user_id = session.get('user_id') or 1
    conn = get_db()
    conn.row_factory = lambda cursor, row: dict(zip([column[0] for column in cursor.description], row))
    cur = conn.cursor()

    # 1. Lấy thông tin sinh viên
    cur.execute("SELECT id FROM students WHERE user_id = ?", (user_id,))
    student = cur.fetchone()
    if not student:
        abort(404)
    student_id = student['id']

    # 2. Lấy thông tin Assignment
    cur.execute("""
        SELECT a.*, c.class_name 
        FROM assignments a 
        JOIN classes c ON a.class_id = c.id 
        WHERE a.id = ?
    """, (assignment_id,))
    assignment = cur.fetchone()
    if not assignment:
        abort(404)

    # 3. XỬ LÝ KHI NHẤN "NỘP BÀI"
    if request.method == 'POST':

        # BẢO MẬT: Kiểm tra lại xem Assignment đã quá hạn chưa từ phía Backend
        try:
            deadline_date = datetime.strptime(assignment['deadline'], '%Y-%m-%d %H:%M:%S')
            if datetime.now() > deadline_date:
                flash('Bài tập này đã quá hạn. Bạn không thể nộp hoặc cập nhật thêm.', 'danger')
                return redirect(url_for('myprojects.submit_assignment', assignment_id=assignment_id))
        except ValueError:
            pass  # Bỏ qua nếu cấu trúc ngày tháng trong DB bị lưu sai format

        progress_report = request.form.get('progress_report')

        # Lấy thông tin bài nộp cũ để kiểm tra file hiện tại
        cur.execute("SELECT file_name, file_url, file_size FROM submissions WHERE assignment_id = ? AND student_id = ?",
                    (assignment_id, student_id))
        existing = cur.fetchone()

        # Xử lý File mới
        file = request.files.get('file')

        if file and file.filename:
            # Nếu CÓ chọn file mới -> Cập nhật thông tin file mới
            file_name = file.filename
            file_url = f"/uploads/{file_name}"
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
        else:
            # Nếu KHÔNG chọn file mới -> Giữ lại thông tin cũ (nếu có)
            if existing:
                file_name = existing['file_name']
                file_url = existing['file_url']
                file_size = existing['file_size']
            else:
                file_name = ""
                file_url = ""
                file_size = 0

        try:
            if existing:
                # Cập nhật: Thông tin file giờ đây sẽ là file mới HOẶC file cũ tùy theo logic trên
                cur.execute("""
                            UPDATE submissions 
                            SET file_name = ?, file_url = ?, file_size = ?, progress_report = ?, submitted_at = CURRENT_TIMESTAMP
                            WHERE assignment_id = ? AND student_id = ?
                        """, (file_name, file_url, file_size, progress_report, assignment_id, student_id))
            else:
                # Thêm mới (dành cho lần nộp đầu tiên)
                cur.execute("""
                            INSERT INTO submissions (assignment_id, student_id, file_name, file_url, file_size, progress_report)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (assignment_id, student_id, file_name, file_url, file_size, progress_report))

            conn.commit()
            flash('Cập nhật bài nộp thành công!', 'success')
            return redirect(url_for('myprojects.submit_assignment', assignment_id=assignment_id))

        except Exception as e:
            conn.rollback()
            flash('Có lỗi xảy ra: ' + str(e), 'danger')
            return redirect(url_for('myprojects.submit_assignment', assignment_id=assignment_id))
    # 4. HIỂN THỊ GIAO DIỆN (GET)
    cur.execute("SELECT * FROM submissions WHERE assignment_id = ? AND student_id = ?", (assignment_id, student_id))
    submission = cur.fetchone()

    # Tính toán trạng thái quá hạn
    is_overdue = False
    try:
        deadline_date = datetime.strptime(assignment['deadline'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() > deadline_date:
            is_overdue = True
    except ValueError:
        pass

    return render_template('submission.html', assignment=assignment, submission=submission, is_overdue=is_overdue)