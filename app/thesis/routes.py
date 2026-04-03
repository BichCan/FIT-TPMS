from flask import render_template, request
from app.database import get_db
from app.thesis import thesis_bp

@thesis_bp.route("/theses")
def theses():
    q = request.args.get("q", "")
    year = request.args.get("year", "")
    type_ = request.args.get("type", "all")

    conn = get_db()
    cursor = conn.cursor()

    years = cursor.execute("""
        SELECT DISTINCT strftime('%Y', published_at) as year
        FROM published_reports
        ORDER BY year DESC
    """).fetchall()

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
        
        -- lấy từ published_reports
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

    WHERE (topics.title LIKE ? OR users.full_name LIKE ?)
    """

    params = [f"%{q}%", f"%{q}%"]

    # lọc năm
    if year:
        sql += " AND strftime('%Y', published_reports.published_at) = ?"
        params.append(year)

    # lọc loại
    if type_ == "project":
        sql += " AND course_types.type_name = 'Đề án'"
    elif type_ == "thesis":
        sql += " AND course_types.type_name = 'Khóa luận'"

    rows = cursor.execute(sql, params).fetchall()
    conn.close()

    return render_template(
        "theses.html",
        theses=rows,
        q=q,
        year=year,
        type=type_,
        years=years
    )

@thesis_bp.route("/theses/<int:topic_id>")
def thesis_detail(topic_id):
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
    conn.close()

    return render_template("thesis_detail.html", t=thesis)