from flask import Blueprint, render_template, request
from app.database import get_db

lecturer_home_bp = Blueprint(
    'lecturer_home',
    __name__,
    url_prefix='/lecturer'
)


@lecturer_home_bp.route('/home')
def home():

    lecturer_id = 15

    keyword = request.args.get('q', '')
    course_type = request.args.get('type', '')
    semester_id = request.args.get('semester', '')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
           SELECT users.full_name
           FROM lecturers
           JOIN users ON lecturers.user_id = users.id
           WHERE lecturers.id = ?
       """, (lecturer_id,))
    lecturer = cursor.fetchone()


    sql = """
        SELECT classes.*, semesters.name AS semester_name, semesters.year AS semester_year
        FROM classes
        LEFT JOIN semesters ON classes.semester_id = semesters.id
        WHERE classes.lecturer_id = ?
    """

    params = [lecturer_id]

    if keyword:
        sql += " AND (classes.class_name LIKE ? OR classes.class_code LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])


    if semester_id:
        sql += " AND classes.semester_id = ?"
        params.append(semester_id)

    cursor.execute(sql, params)
    classes = cursor.fetchall()

    cursor.execute("SELECT * FROM semesters")
    semesters = cursor.fetchall()

    type_filter = request.args.get('type', '')

    if type_filter == 'de-an':
        classes = [
            c for c in classes
            if c['class_code'].startswith('DA')
        ]

    elif type_filter == 'khoa-luan':
        classes = [
            c for c in classes
            if c['class_code'].startswith('KL')
        ]

    def get_course_type(class_code):
        if class_code.startswith("DA_"):
            return "Đề án"
        elif class_code.startswith("KL_"):
            return "Khóa luận"
        return "Khác"

    # thêm loại môn học dựa vào MÃ LỚP
    classes_with_type = []
    for c in classes:
        c = dict(c)  # sqlite Row → dict
        c["course_type"] = get_course_type(c["class_code"])
        classes_with_type.append(c)

    classes = classes_with_type

    db.close()


    return render_template(
        'lecturer/home.html',
        lecturer=lecturer,
        classes=classes,
        semesters=semesters
    )