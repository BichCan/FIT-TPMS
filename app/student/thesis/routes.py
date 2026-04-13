import os
import sqlite3
from flask import render_template, request, redirect, url_for, flash, abort, session
from werkzeug.utils import secure_filename
from app.database import get_db
from . import thesis_bp

@thesis_bp.route("/theses-projects")
def thesesprojects():
    q = request.args.get("q", "")
    year = request.args.get("year", "")
    type_ = request.args.get("type", "all")

    # Xác định base template dựa trên vai trò
    base_template = "student/base.html"
    if session.get('role') == 'lecturer':
        base_template = "lecturer/base.html"

    conn = get_db()
    cursor = conn.cursor()

    years = cursor.execute("""
        SELECT DISTINCT strftime('%Y', published_at) as year
        FROM published_reports
        ORDER BY year DESC
    """).fetchall()

    sql = """
        SELECT
            t.id, t.title, t.description,
            c.class_code, co.course_name, ct.type_name,
            u_lec.full_name AS lecturer_name,
            u_stu.full_name AS student_name,
            s.student_code,
            pr.published_at, pr.file_url, pr.source_code_url
        FROM published_reports pr
        JOIN topics t ON pr.topic_id = t.id
        JOIN classes c ON t.class_id = c.id
        JOIN courses co ON c.course_id = co.id
        JOIN course_types ct ON co.course_type_id = ct.id
        JOIN lecturers l ON c.lecturer_id = l.id
        JOIN users u_lec ON l.user_id = u_lec.id
        JOIN students s ON t.student_id = s.id
        JOIN users u_stu ON s.user_id = u_stu.id
        WHERE (t.title LIKE ? OR u_lec.full_name LIKE ?)
        """

    params = [f"%{q}%", f"%{q}%"]

    # lọc năm
    if year:
        sql += " AND strftime('%Y', pr.published_at) = ?"
        params.append(year)

    # lọc loại
    if type_ == "project":
        sql += " AND ct.type_name = 'Đề án'"
    elif type_ == "thesis":
        sql += " AND ct.type_name = 'Khóa luận'"

    rows = cursor.execute(sql, params).fetchall()

    return render_template(
        "student/theses.html",
        theses=rows,
        q=q,
        year=year,
        type=type_,
        years=years,
        base_template=base_template
    )

@thesis_bp.route("/theses/<int:topic_id>")
def thesis_detail(topic_id):
    base_template = "student/base.html"
    if session.get('role') == 'lecturer':
        base_template = "lecturer/base.html"

    conn = get_db()
    cursor = conn.cursor()

    sql = """
    SELECT
        topics.id,
        topics.title,
        topics.description,
        classes.class_code,
        courses.course_name,
        course_types.type_name,
        users.full_name AS lecturer_name,
        
        u2.full_name AS student_name,
        students.id AS student_code,
        
        published_reports.published_at,
        published_reports.file_url,
        published_reports.source_code_url
        
    FROM topics

    JOIN classes ON topics.class_id = classes.id
    JOIN courses ON classes.course_id = courses.id
    JOIN course_types ON courses.course_type_id = course_types.id
    JOIN lecturers ON classes.lecturer_id = lecturers.id
    JOIN users ON lecturers.user_id = users.id
    
    JOIN students ON topics.student_id = students.id
    JOIN users u2 ON students.user_id = u2.id

    LEFT JOIN published_reports
        ON published_reports.topic_id = topics.id

    WHERE topics.id = ?
    """

    thesis = cursor.execute(sql, (topic_id,)).fetchone()

    return render_template(
        "student/thesis_detail.html",
        t=thesis,
        base_template=base_template
    )


# 1. Route Xóa đề tài
@thesis_bp.route("/theses/delete/<int:topic_id>", methods=["POST"])
def delete_thesis(topic_id):
    if session.get('role') != 'lecturer':  # Hoặc admin
        flash("Bạn không có quyền!", "danger")
        return redirect(url_for("thesis.thesesprojects"))

    conn = get_db()
    cursor = conn.cursor()
    try:
        # 1. Xóa các báo cáo đã đăng liên quan đến đề tài này trước (Bảng con)
        # Nếu không xóa cái này, SQL sẽ chặn không cho xóa topic_id ở bảng topics
        cursor.execute("DELETE FROM published_reports WHERE topic_id = ?", (topic_id,))

        # 2. Bây giờ mới xóa đề tài (Bảng cha)
        cursor.execute("DELETE FROM topics WHERE id = ?", (topic_id,))

        conn.commit()
        flash("Xóa đề tài thành công!", "success")
    except Exception as e:
        conn.rollback()
        print(f"Lỗi khi xóa: {e}")
        flash(f"Lỗi khi xóa: {str(e)}", "danger")

    return redirect(url_for("thesis.thesesprojects"))
# 1. Lấy đường dẫn tuyệt đối của thư mục chứa file routes.py hiện tại
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Nhảy lên 3 cấp để ra thư mục gốc dự án (FIT-TPMS)
# Cấp 1: ra student/, Cấp 2: ra app/, Cấp 3: ra FIT-TPMS/
BASE_DIR = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))

# 3. Trỏ vào thư mục static/uploads nằm ở gốc
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

# Kiểm tra và tạo thư mục nếu chưa có để tránh lỗi khi lưu file
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
# 2. Route Cập nhật đề tài (Giao diện Form)
@thesis_bp.route("/theses/edit/<int:topic_id>", methods=["GET", "POST"])
def edit_thesis(topic_id):
    if session.get('role') != 'lecturer':
        flash("Bạn không có quyền thực hiện thao tác này!", "danger")
        return redirect(url_for("thesis.thesesprojects"))

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        source_url = request.form.get("source_code_url")

        # Xử lý File báo cáo
        file = request.files.get('report_file')
        file_url = None

        if file and file.filename != '':
            filename = secure_filename(file.filename)

            # Tạo thư mục nếu chưa có
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            # Lưu file vật lý
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            # Lưu đường dẫn vào DB (Dùng đường dẫn web)
            file_url = f"/static/uploads/{filename}"
        try:
            # 1. Luôn cập nhật thông tin tiêu đề/mô tả trong bảng topics
            cursor.execute("UPDATE topics SET title = ?, description = ? WHERE id = ?",
                           (title, description, topic_id))

            # 2. Kiểm tra xem topic_id này đã tồn tại trong published_reports chưa
            check_sql = "SELECT id, file_url FROM published_reports WHERE topic_id = ?"
            existing_report = cursor.execute(check_sql, (topic_id,)).fetchone()

            if existing_report:
                # Nếu ĐÃ CÓ: Update (phần này không cần student_id vì nó đã có sẵn)
                update_sql = """
                                UPDATE published_reports 
                                SET file_url = COALESCE(?, file_url),
                                    source_code_url = ?,
                                    published_at = datetime('now')
                                WHERE topic_id = ?
                            """
                cursor.execute(update_sql, (file_url, source_url, topic_id))
            else:
                # Nếu CHƯA CÓ: Insert mới hoàn toàn
                # BƯỚC QUAN TRỌNG: Phải lấy student_id của đề tài này trước
                topic_data = cursor.execute("SELECT student_id, class_id FROM topics WHERE id = ?",
                                            (topic_id,)).fetchone()

                if topic_data:
                    insert_sql = """
                                    INSERT INTO published_reports (topic_id, student_id, class_id, file_url, source_code_url, published_at)
                                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                                """
                    # Truyền thêm student_id và class_id vào để thỏa mãn ràng buộc database
                    cursor.execute(insert_sql, (
                        topic_id,
                        topic_data['student_id'],
                        topic_data['class_id'],
                        file_url,
                        source_url
                    ))
            conn.commit()
            flash("Cập nhật đề tài thành công!", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Lỗi database: {str(e)}", "danger")
        return redirect(url_for("thesis.thesesprojects"))

    # --- Phần GET dữ liệu cũ giữ nguyên ---
    sql = """
    SELECT t.*, ct.type_name, u.full_name as student_name, s.id as student_code,
           pr.file_url, pr.source_code_url
    FROM topics t
    JOIN students s ON t.student_id = s.id
    JOIN users u ON s.user_id = u.id
    JOIN classes c ON t.class_id = c.id
    JOIN courses co ON c.course_id = co.id
    JOIN course_types ct ON co.course_type_id = ct.id
    LEFT JOIN published_reports pr ON t.id = pr.topic_id
    WHERE t.id = ?
    """
    thesis = cursor.execute(sql, (topic_id,)).fetchone()

    if not thesis:
        abort(404)

    return render_template("lecturer/edit_thesis.html", t=thesis)

@thesis_bp.route("/publish-final-report/<int:submission_id>", methods=["POST"])
def publish_final_report(submission_id):
    if session.get('role') != 'lecturer':
        flash("Chỉ giảng viên mới có quyền đăng báo cáo!", "danger")
        return redirect(request.referrer)

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Lấy thông tin từ bảng topics (Tên, mô tả) và submissions (File, source code)
        # Liên kết dựa trên student_id và class_id chung giữa bài tập và đề tài
        query = """
            SELECT 
                t.id AS topic_id, t.title, t.description, t.student_id, t.class_id,
                s.file_url, s.source_code_url -- source_code_url có thể lấy từ form bài nộp
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            JOIN topics t ON (s.student_id = t.student_id AND a.class_id = t.class_id)
            WHERE s.id = ?
        """
        data = cursor.execute(query, (submission_id,)).fetchone()

        if not data:
            flash("Không tìm thấy dữ liệu đề tài hoặc bài nộp hợp lệ.", "warning")
            return redirect(request.referrer)

        # Kiểm tra xem đã tồn tại trong danh sách công khai chưa
        existing = cursor.execute("SELECT id FROM published_reports WHERE topic_id = ?", (data['topic_id'],)).fetchone()

        if existing:
            # CẬP NHẬT: Giữ nguyên topic_id, update file và source code mới nhất
            cursor.execute("""
                UPDATE published_reports 
                SET file_url = ?, source_code_url = ?, published_at = datetime('now')
                WHERE topic_id = ?
            """, (data['file_url'], data.get('source_code_url'), data['topic_id']))
            flash(f"Đã cập nhật bản báo cáo cho: {data['title']}", "success")
        else:
            # ĐĂNG MỚI: Lấy student_id và class_id từ topic đã đăng ký [cite: 6, 8]
            cursor.execute("""
                INSERT INTO published_reports (student_id, class_id, topic_id, file_url, source_code_url, published_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (data['student_id'], data['class_id'], data['topic_id'], data['file_url'], data.get('source_code_url')))
            flash(f"Đã đăng bản báo cáo: {data['title']}", "success")

        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f"Lỗi: {str(e)}", "danger")

    return redirect(request.referrer)